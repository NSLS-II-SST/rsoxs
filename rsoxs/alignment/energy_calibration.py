import bluesky.plan_stubs as bps
from nbs_bl.hw import (
    en,
    grating,
    mirror2,
    Sample_TEY_int,
)
from nbs_bl.gGrEqns import get_mirror_grating_angles, find_best_offsets
from .fly_alignment import rsoxs_fly_max



## Copying Eliot's tune_pgm function and just using Jamie's new fly_max function
def calibrate_pgm_offsets(
    cs=[1.4, 1.35, 1.35],
    ms=[1, 1, 2],
    energy=291.65,
    pol=90,
    k=250, ## Grating l/mm
    detector=None,
    signal="RSoXS Sample Current",
    grat_off_search = 0.08,
    grating_rb_off = 0,
    mirror_rb_off = 0,
    search_ratio = 30,
    scan_time = 30,
):
    # RE(load_sample(sample_by_name(bar, 'HOPG')))
    # RE(tune_pgm(cs=[1.35,1.37,1.385,1.4,1.425,1.45],ms=[1,1,1,1,1],energy=291.65,pol=90,k=250))
    # RE(tune_pgm(cs=[1.55,1.6,1.65,1.7,1.75,1.8],ms=[1,1,1,1,1],energy=291.65,pol=90,k=1200))

    detector = detector if detector else Sample_TEY_int  ## Cannot have device in function definition for gui

    yield from bps.mv(en.polarization, pol)
    yield from bps.mv(en, energy)
    detector.kind = "hinted"
    mirror_measured = []
    grating_measured = []
    energy_measured = []
    m_measured = []
    # bec.enable_plots()
    for cff, m_order in zip(cs, ms):
        m_set, g_set = get_mirror_grating_angles(energy, cff, k, m_order)
        print(f'setting cff to {cff} for a mirror with k={k} at {m_order} order')
        m_set += mirror_rb_off
        g_set += grating_rb_off
        yield from bps.mv(grating.velocity, 0.1, mirror2.velocity, 0.1)
        yield from bps.sleep(1)
        yield from bps.mv(grating, g_set, mirror2, m_set)
        yield from bps.sleep(1)
        peaklist = []
        yield from rsoxs_fly_max(
            detectors=[detector],
            motor=grating,
            start=g_set - grat_off_search,
            stop=g_set + grat_off_search,
            velocities=[grat_off_search*2/scan_time, grat_off_search*2/(search_ratio * scan_time), grat_off_search*2/(search_ratio**2 * scan_time)],
            period = 0.5,
            snake=False,
            peaklist=peaklist,
            range_ratio=search_ratio,
            open_shutter=True,
            rb_offset=grating_rb_off,
            stream=False
        )
        grating_measured.append(peaklist[0][signal][grating.name] - grating_rb_off )
        mirror_measured.append(mirror2.read()[mirror2.name]["value"] - mirror_rb_off)
        energy_measured.append(291.65)
        m_measured.append(m_order)
    print(f"mirror positions: {mirror_measured}")
    print(f"grating positions: {grating_measured}")
    print(f"energy positions: {energy_measured}")
    print(f"orders: {m_measured}")
    fit = find_best_offsets(mirror_measured, grating_measured, m_measured, energy_measured, k)
    print(fit)
    accept = input("Accept these values and set the offset (y/n)? ")
    if accept in ["y", "Y", "yes"]:
        yield from bps.mvr(mirror2.user_offset, -fit.x[0], grating.user_offset, -fit.x[1])
    # bec.disable_plots()
    detector.kind = "normal"
    return fit