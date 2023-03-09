from matplotlib import pyplot as plt
import numpy as np
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import pandas as pd
from bluesky.callbacks.fitting import PeakStats
from bluesky.preprocessors import subs_wrapper
from bluesky import preprocessors as bpp
from bluesky.run_engine import Msg
from ..HW.signals import (
    Izero_Mesh,
    Beamstop_WAXS,
    Sample_TEY,
    Beamstop_SAXS,
    Slit1_Current_Top,
    Slit1_Current_Bottom,
    Slit1_Current_Inboard,
    Slit1_Current_Outboard
    )
from ..HW.energy import (
    en,
    mono_en,
    grating_to_1200,
    grating_to_250,
    grating_to_rsoxs,
    grating,
    mirror2,
    set_polarization,
    epu_gap,
    epu_phase,
    )
from ..HW.energy import epu_mode
from sst_hw.diode import Shutter_control, Shutter_enable
from ..HW.slits import slits1, slits2
from ..Functions.alignment import load_configuration
from ..HW.detectors import set_exposure, waxs_det
from ..HW.motors import sam_Th, sam_Y
from sst_hw.gatevalves import gv28, gv27a, gvll
from sst_hw.shutters import psh10
from sst_hw.vacuum import rsoxs_ll_gpwr
from ..startup import bec
from sst_funcs.printing import run_report
from sst_funcs.gGrEqns import get_mirror_grating_angles, find_best_offsets
from .fly_alignment import fly_max
run_report(__file__)


def buildeputable(
    start,
    stop,
    step,
    widfract,
    startinggap=14000,
    phase=0,
    mode="L",
    grat="1200",
    name="test",
):
    ens = np.arange(start, stop, step)
    gaps = []
    gapsbs = []
    ensout = []
    heights = []
    heightsbs = []
    Izero_Mesh.kind = "hinted"
    Beamstop_WAXS.kind = "hinted"
    mono_en.kind = "hinted"
    epu_gap.kind = 'hinted'
    # startinggap = epugap_from_energy(ens[0]) #get starting position from existing table
    # if grat == "1200":
    #     yield from grating_to_1200(2.0,-6.3,0.0)
    # elif grat == "250":
    #     yield from grating_to_250(2.0,-6.3,0.0)
    # elif grat == "rsoxs":
    #     yield from grating_to_rsoxs(2.0,-6.3,0.0)
    bec.enable_plots()

    plt.close()
    plt.close()
    plt.close()
    plt.close()

    #yield from bps.mv(sam_Y,30)
    if mode == "C":
        yield from bps.mv(epu_mode, 0)
    elif mode == "CW":
        yield from bps.mv(epu_mode, 1)
    elif mode == "L3":
        yield from bps.mv(epu_mode, 3)
    else:
        yield from bps.mv(epu_mode, 2)
    yield from bps.mv(epu_phase, phase)

    count = 0
    peaklist=[]
    for energy in ens:
        yield from bps.mv(mono_en, energy)
        yield from bps.mv(en.scanlock,False)
        yield from bps.mv(en.mir3Pitch,en.m3pitchcalc(energy,False))
        yield from bps.mv(epu_gap, max(14000, startinggap - 500 * widfract))
        yield from bps.mv(Shutter_enable, 0)
        yield from bps.mv(Shutter_control, 1)
        yield from tune_max(
            [Izero_Mesh, Beamstop_WAXS],
            ["RSoXS Au Mesh Current",
            "WAXS Beamstop",],
            epu_gap,
            min(99500, max(14000, startinggap - 500 * widfract)),
            min(100000, max(15000, startinggap + 1500 * widfract)),
            3 * widfract,
            10,
            3,
            True,
            peaklist
        )
        [maxread, max_xI_signals, max_I_signals] = peaklist[-1]
        startinggap = max_xI_signals["RSoXS Au Mesh Current"]
        gapbs = max_xI_signals["WAXS Beamstop"]
        height = max_I_signals["RSoXS Au Mesh Current"]
        heightbs = max_I_signals["WAXS Beamstop"]
        gaps.append(startinggap)
        gapsbs.append(gapbs)
        heights.append(height)
        heightsbs.append(heightbs)
        ensout.append(mono_en.position)
        data = {"Energies": ensout,
                "EPUGaps": gaps,
                "PeakCurrent": heights,
                "EPUGapsBS": gapsbs,
                "PeakCurrentBS": heightsbs,
                }
        dataframe = pd.DataFrame(data=data)
        dataframe.to_csv("/nsls2/data/sst/legacy/RSoXS/EPUdata_2023Feb_" + name + ".csv")
        count += 1
        if count > 20:
            count = 0
            plt.close()
            plt.close()
            plt.close()
            plt.close()
    plt.close()
    plt.close()
    plt.close()
    plt.close()
    # print(ens,gaps)


def do_some_eputables_2023_en():

    yield from load_configuration("WAXSNEXAFS")
    yield from bps.mv(slits1.hsize, 1)
    yield from bps.mv(slits2.hsize, 1)
    # angles = [0,5,15,25,40,50,60,70,80,90]
    # phases = [0,
    #           6688.9843608114115,
    #           10781.54138668513,
    #           13440.927684320242,
    #           15705.851176691127,
    #           17575.669146953864,
    #           19598.02761805813,
    #           21948.115314738126,
    #           24889.02500863509,
    #           29500]

#    startingens = [95,125,155,185,200,200,185,160]
#    for angle,ph,sten in zip(angles[5:],phases[5:],startingens[5:]):
#        yield from buildeputable(sten, 500, 10, 2, 14000, ph, "L", "250", f'linear{angle}deg_250')
#    for angle,ph,sten in zip(angles,phases,startingens):
#        yield from buildeputable(sten, 500, 10, 2, 14000, ph, "L3", "250", f'linear{180-angle}deg_250')

    # startgaps = [33271.94497611413,
    #             29889.652490430373,
    #             27174.560460333993,
    #             24965.844827621615,
    #             23564.225919905086,
    #             22983.602525718445,
    #             22874.408275853402,
    #             23677.309482826902]
    #
    # for angle,ph,stgp in zip(angles,phases,startgaps):
    #     yield from buildeputable(400, 1400, 20, 4, stgp, ph, "L", "1200", f'linear{angle}deg_1200')
    # for angle,ph,stgp in zip(angles,phases,startgaps):
    #     yield from buildeputable(400, 1400, 20, 4, stgp, ph, "L3", "1200", f'linear{180-angle}deg_1200')


    angles = [0,2.94,5,10,20,30,40,50,60,70,80,85,90]
    phases = [0,
              2500,
              4000,
              6688.9843608114115,
              10781.54138668513,
              13440.927684320242,
              15705.851176691127,
              17575.669146953864,
              19598.02761805813,
              21948.115314738126,
              24889.02500863509,
              27000,
              29500]
    #yield from buildeputable(110, 1300, 20, 3, 14000, 15000, 'C', '1200', 'CW_1200_H1')
    #yield from buildeputable(110, 1300, 20, 3, 14000, 15000, 'CW', '1200', 'C_1200_H1')
    startingens = [110,110,110,110,125,155,185,200,200,185,160,140]
    for angle,ph,sten in zip(angles,phases,startingens):
        yield from buildeputable(sten, 1300, 25, 3, 14000, ph, "L", "1200", f'linear_{angle}deg_1200_H1')
    for angle,ph,sten in zip(angles,phases,startingens):
        yield from buildeputable(sten, 1300, 25, 3, 14000, ph, "L3", "1200", f'linear_{180-angle}deg_1200_H1')


    # 1200l/pp from 400 to 1400 eV
    # then third harmonic from 1000 to 2200 eV

#    yield from buildeputable(200, 1300, 10, 2, 20922, 8000, "L", "1200", "mL8_1200")

#    yield from buildeputable(200, 1300, 10, 2, 23704, 0, "L3", "1200", "m3L0_1200")

    #yield from buildeputable(80, 500, 10, 2, 14000, 0, "L", "250", "mL0_250")
    #yield from buildeputable(145, 500, 10, 2, 14000, 29500, "L", "250", "mL29p5_250")

    #yield from buildeputable(80, 500, 10, 2, 14000, 0, "L3", "250", "m3L0_250")


def Scan_izero_peak(startingen, widfract):
    ps = PeakStats("en_energy", "RSoXS Au Mesh Current")
    yield from subs_wrapper(
        tune_max(
            [Izero_Mesh, Beamstop_WAXS],
            "RSoXS Au Mesh Current",
            mono_en,
            min(2100, max(72, startingen - 10 * widfract)),
            min(2200, max(90, startingen + 50 * widfract)),
            1,
            25,
            2,
            True,
            md={"plan_name": "energy_tune"},
        ),
        ps,
    )
    print(ps.cen)
    return ps


def buildeputablegaps(start, stop, step, widfract, startingen, name, phase, grating):
    gaps = np.arange(start, stop, step)
    ens = []
    gapsout = []
    heights = []
    Beamstop_WAXS.kind= 'hinted'
    Izero_Mesh.kind= 'hinted'
    epu_gap.kind = 'hinted'
    # startinggap = epugap_from_energy(ens[0]) #get starting position from existing table

    count = 0

    if grating == "1200":
        yield from grating_to_1200()

    elif grating == "250":
        yield from grating_to_250()

    yield from bps.mv(epu_phase, phase)

    for gap in gaps:
        yield from bps.mv(epu_gap, gap)
        yield from bps.mv(mono_en, max(72, startingen - 10 * widfract))
        peaklist = []
        yield from tune_max(
            [Izero_Mesh, Beamstop_WAXS],
            "RSoXS Au Mesh Current",
            mono_en,
            min(2100, max(72, startingen - 10 * widfract)),
            min(2200, max(90, startingen + 50 * widfract)),
            1,
            25,
            2,
            True,
            md={"plan_name": "energy_tune"},
            peaklist=peaklist,
        )

        ens.append(peaklist[0])
        heights.append(peaklist[1])
        gapsout.append(epu_gap.position)
        startingen = peaklist[0]
        data = {"Energies": ens, "EPUGaps": gapsout, "PeakCurrent": heights}
        dataframe = pd.DataFrame(data=data)
        dataframe.to_csv("/mnt/zdrive/EPUdata_2021_" + name + ".csv")
        count += 1
        if count > 20:
            count = 0
            plt.close()
            plt.close()
            plt.close()
    plt.close()
    plt.close()
    plt.close()


def do_2020_eputables():
    # yield from buildeputablegaps(15000, 55000, 500, 1.5, 75, 'H1phase02',0)
    # yield from bps.mv(mono_en,600)
    # yield from bps.mv(mono_en,400)
    # yield from bps.mv(mono_en,200)
    # yield from buildeputablegaps(15000, 50000, 500, 1.5, 150, 'H1phase295002',29500)
    # yield from bps.mv(mono_en,600)
    # yield from bps.mv(mono_en,400)
    # yield from bps.mv(mono_en,200)
    # yield from buildeputablegaps(15000, 50000, 500, 2, 3*75, 'H3phase02',0)
    # yield from bps.mv(mono_en,900)
    # yield from bps.mv(mono_en,600)
    # yield from bps.mv(mono_en,400)
    # yield from bps.mv(epu_mode,0)
    yield from buildeputablegaps(15000, 40000, 500, 2, 200, "H1Circphase150002", 15000)
    yield from bps.mv(mono_en, 800)
    yield from buildeputablegaps(15000, 30000, 500, 2, 600, "H3Circphase150002", 15000)


# yield from bps.mv(epu_mode,2)


def do_2023_eputables():
    Izero_Mesh.kind = "hinted"
    Beamstop_WAXS.kind = "hinted"
    mono_en.readback.kind = "hinted"
    mono_en.kind = "hinted"
    mono_en.read_attrs = ["readback"]
    bec.enable_plots()  # TODO: this will work, but not needed - need to move all plotting to a seperate app
    yield from load_configuration("WAXSNEXAFS")
    yield from bps.mv(slits1.hsize, 1)
    yield from bps.mv(slits2.hsize, 1)
    yield from bps.mv(epu_mode, 3)

    yield from buildeputablegaps(
        14000, 35000, 500, 1, 80, "_Feb2023_phase4000_0", 0, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase29500_1200", 29500, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase26000_1200", 26000, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase23000_1200", 23000, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase21000_1200", 21000, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase18000_1200", 18000, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase15000_1200", 15000, 1200
    )
    yield from buildeputablegaps(
        14000, 30000, 500, 2, 150, "_Feb2023_phase12000_1200", 12000, 1200
    )
    yield from buildeputablegaps(
        14000, 35000, 500, 1, 80, "_Feb2023_phase8000_1200", 8000, 1200
    )
    yield from buildeputablegaps(
        14000, 35000, 500, 1, 80, "_Feb2023_phase4000_1200", 4000, 1200
    )
    yield from buildeputablegaps(
        14000, 35000, 500, 1, 80, "_Feb2023_phase4000_1200", 4000, 1200
    )



def tune_max(
    detectors,
    signals,
    motor,
    start,
    stop,
    min_step,
    num=10,
    step_factor=3.0,
    snake=False,
    peaklist=[],
    *,
    md=None,
):
    r"""
    plan: tune a motor to the maximum of signal(motor)

    Initially, traverse the range from start to stop with
    the number of points specified.  Repeat with progressively
    smaller step size until the minimum step size is reached.
    Rescans will be centered on the signal maximum
    with original scan range reduced by ``step_factor``.

    Set ``snake=True`` if your positions are reproducible
    moving from either direction.  This will not
    decrease the number of traversals required to reach convergence.
    Snake motion reduces the total time spent on motion
    to reset the positioner.  For some positioners, such as
    those with hysteresis, snake scanning may not be appropriate.
    For such positioners, always approach the positions from the
    same direction.

    Note:  if there are multiple maxima, this function may find a smaller one
    unless the initial number of steps is large enough.

    Parameters
    ----------
    detectors : Signal
        list of 'readable' objects
    signals : string
        detector fields whose output is to maximize
        (the first will be the primary, but secondardy maxes will be recorded)
    motor : object
        any 'settable' object (motor, temp controller, etc.)
    start : float
        start of range
    stop : float
        end of range, note: start < stop
    min_step : float
        smallest step size to use.
    num : int, optional
        number of points with each traversal, default = 10
    step_factor : float, optional
        used in calculating new range after each pass

        note: step_factor > 1.0, default = 3
    snake : bool, optional
        if False (default), always scan from start to stop
    md : dict, optional
        metadata

    Examples
    --------
    Find the center of a peak using synthetic hardware.

     from ophyd.sim import SynAxis, SynGauss
     motor = SynAxis(name='motor')
     det = SynGauss(name='det', motor, 'motor',
                    center=-1.3, Imax=1e5, sigma=0.05)
     RE(tune_max([det], "det", motor, -1.5, -0.5, 0.01, 10))
    """
    signal = signals[0]
    if min_step <= 0:
        raise ValueError("min_step must be positive")
    if step_factor <= 1.0:
        raise ValueError("step_factor must be greater than 1.0")
    try:
        (motor_name,) = motor.hints["fields"]
    except (AttributeError, ValueError):
        motor_name = motor.name
    _md = {
        "detectors": [det.name for det in detectors],
        "motors": [motor.name],
        "plan_args": {
            "detectors": list(map(repr, detectors)),
            "motor": repr(motor),
            "start": start,
            "stop": stop,
            "num": num,
            "min_step": min_step,
        },
        "plan_name": "tune_max",
        "hints": {},
    }
    _md.update(md or {})
    try:
        dimensions = [(motor.hints["fields"], "primary")]
    except (AttributeError, KeyError):
        pass
    else:
        _md["hints"].setdefault("dimensions", dimensions)

    low_limit = min(start, stop)
    high_limit = max(start, stop)

    @bpp.stage_decorator(list(detectors) + [motor])
    @bpp.run_decorator(md=_md)
    def _tune_core(start, stop, num, signal, peaklist):
        next_pos = start
        step = (stop - start) / (num - 1)
        peak_position = None
        cur_I = None
        max_I = -1e50  # for peak maximum finding (allow for negative values)
        max_xI = 0
        cur_sigI = None
        max_I_signals={}
        max_xI_signals={}
        for sig in signals:
            max_I_signals[sig] = -1e50
        while abs(step) >= min_step and low_limit <= next_pos <= high_limit:
            yield Msg("checkpoint")
            yield from bps.mv(motor, next_pos)
            ret = yield from bps.trigger_and_read(detectors + [motor])
            cur_I = ret[signal]["value"]
            position = ret[motor_name]["value"]
            if cur_I > max_I:
                max_I = cur_I
                max_xI = position
                max_ret = ret
            for sig in signals:
                cur_sigI=ret[sig]["value"]
                if(cur_sigI>max_I_signals[sig]):
                    max_I_signals[sig]=cur_sigI
                    max_xI_signals[sig]=position

            next_pos += step
            in_range = min(start, stop) <= next_pos <= max(start, stop)

            if not in_range:
                if max_I == -1e50:
                    return
                peak_position = max_xI  # maxiumum
                max_xI, max_I = 0, 0  # reset for next pass
                new_scan_range = (stop - start) / step_factor
                start = np.clip(
                    peak_position - new_scan_range / 2, low_limit, high_limit
                )
                stop = np.clip(
                    peak_position + new_scan_range / 2, low_limit, high_limit
                )
                if snake:
                    start, stop = stop, start
                step = (stop - start) / (num - 1)
                next_pos = start
                # print("peak position = {}".format(peak_position))
                # print("start = {}".format(start))
                # print("stop = {}".format(stop))

        # finally, move to peak position
        if peak_position == 0:
            peak_position = start
        if peak_position is not None:
            # improvement: report final peak_position
            # print("final position = {}".format(peak_position))
            yield from bps.mv(motor, peak_position)
        peaklist.append([max_ret, max_xI_signals, max_I_signals])
        return [max_ret, max_xI_signals, max_I_signals]

    return (yield from _tune_core(start, stop, num, signal, peaklist))


def stability_scans(num):
    scans = np.arange(num)
    for scan in scans:
        yield from bps.mv(en, 200)
        yield from bp.scan([Izero_Mesh], en, 200, 1400, 1201)


# settings for 285.3 eV 1.6 C 1200l/mm gold Aug 1, 2020
# e 285.3
# en.monoen.grating.set_current_position(-7.494888000531973)
# en.monoen.mirror2.set_current_position(-6.085536389355577)

# {'en_monoen_grating_user_offset': {'value': -0.31108245265481216,
#   'timestamp': 1596294657.763531}}

# {'en_monoen_mirror2_user_offset': {'value': -1.158546028874075,
#   'timestamp': 1596294681.080148}}


def isvar_scan():
    polarizations = [0, 90]
    angles = [10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30]
    exps = [0.01, 0.01, 0.05, 0.05, 0.1, 1, 1, 1, 1]
    for angle, exp in zip(angles, exps):
        set_exposure(exp)
        yield from bps.mv(sam_Th, 90 - angle)
        for polarization in polarizations:
            yield from bps.mv(en.polarization, polarization)
            yield from bp.scan([waxs_det], en, 270, 670, 5)


def vent():
    yield from psh10.close()
    yield from gv28.close()
    yield from gv27a.close()
    yield from bps.mv(sam_Y, 349)

    print("waiting for you to close the load lock gate valve")
    print(
        "Please also close the small manual black valve on the back of the load lock now"
    )
    while gvll.state.get() is 1:
        gvll.read()  # attempt at a fix for problem where macro hangs here.
        bps.sleep(1)
    print("TEM load lock closed - turning off loadlock gauge")
    yield from bps.mv(rsoxs_ll_gpwr, 0)
    print(
        "Should be safe to begin vent by pressing right most button of BOTTOM turbo controller once"
    )
    print("")


def tune_pgm(cs = [1.4,1.35,1.35], ms = [1,1,2],energy=291.65,pol=90,k=250):
    #RE(load_sample(sample_by_name(bar, 'HOPG')))
    yield from bps.mv(en.polarization, pol)
    yield from bps.mv(en,energy)
    Sample_TEY.kind = 'hinted'
    Izero_Mesh.kind = 'normal'
    mirror_measured = []
    grating_measured = []
    energy_measured = []
    m_measured = []
    bec.enable_plots()
    for cff,m_order in zip(cs,ms):
        m_set, g_set = get_mirror_grating_angles(291.65, cff, k, m_order)
        yield from bps.mv(grating, g_set, mirror2, m_set, grating.velocity,0.1,mirror2.velocity,0.1)
        yield from bps.sleep(0.2)
        peaklist = []
        yield from fly_max(
            detectors = [Izero_Mesh, Sample_TEY],
            signals = ["RSoXS Sample Current"],
            motor = grating,
            start = g_set - .2,
            stop = g_set + .2,
            velocities=[0.02,0.0005],
            snake = False,
            peaklist= peaklist,
            range_ratio=30,
            open_shutter=True,
        )
        grating_measured.append(peaklist[0][0])
        mirror_measured.append(mirror2.read()['Mono Mirror']['value'])
        energy_measured.append(291.65)
        m_measured.append(m_order)
    print(f'mirror positions: {mirror_measured}')
    print(f'grating positions: {grating_measured}')
    print(f'energy positions: {energy_measured}')
    print(f'orders: {m_measured}')
    fit = find_best_offsets(mirror_measured,grating_measured,m_measured,energy_measured,k)
    print(fit)
    print(fit.x)
    return fit
