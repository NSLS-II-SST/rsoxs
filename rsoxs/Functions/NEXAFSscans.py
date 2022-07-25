import numpy as np
from ..HW.energy import en
from ..HW.signals import Sample_TEY, Izero_Mesh, Beamstop_SAXS, Beamstop_WAXS
from ..Functions.alignment import sample, load_sample
from ..Functions.alignment import rotate_now
from .energyscancore import NEXAFS_fly_scan_core, NEXAFS_scan_core
from .energyscans import clean_up_md
from sst_funcs.printing import run_report, read_input


run_report(__file__)


def full_Carbon_NEXAFS(
    sigs=[],
    pol=0,
    diode_range=8,
    m3_pitch=7.98,
    open_each_step=True,
    exp_time=1,
    grating="no change",
    motorname="None",
    offset=0,
    master_plan=None,
    md={},
    enscan_type="full_Carbon_NEXAFS",
    **kwargs
):
    """
    Full Carbon Scan runs an RSoXS sample set through the carbon edge, with particular emphasis in he pre edge region
    typically this is not run anymore as of jan 2021.  fly scans are the preferred NEXAFS method
    I'm keeping this here just as a historical record / fallback in case flying stops working

    :param sigs: which other signals to use
    :param dets: which detector to use
    :param energy: what energy motor to scan
    :return: perform scan

    normal scan takes ~ 7 minutes to complete
    """
    enscan_type = "full_Carbon_NEXAFS"
    sample()
    # create a list of energies
    energies = np.arange(270, 282, 0.5)
    energies = np.append(energies, np.arange(282, 286, 0.1))
    energies = np.append(energies, np.arange(286, 292, 0.1))
    energies = np.append(energies, np.arange(292, 310, 0.25))
    energies = np.append(energies, np.arange(310, 320, 1))
    energies = np.append(energies, np.arange(320, 350, 1))

    uid = yield from NEXAFS_scan_core(
        sigs,
        energies,
        enscan_type=enscan_type,
        master_plan=master_plan,
        md=md,
        openshutter=True,
        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        open_each_step=open_each_step,
        exp_time=exp_time,
        grating=grating,
        motorname=motorname,
        offset=offset,
        **kwargs
    )
    return uid


def fly_Carbon_NEXAFS(
    speed=0.2,
    cycles=0,
    pol=0,
    diode_range=8,
    m3_pitch=7.94,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Carbon_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Carbon_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(270, 282, speed * 3), (282, 297, speed), (297, 340, speed * 5)],
        enscan_type=enscan_type,
        openshutter=True,
        master_plan=master_plan,
        md=md,
        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        cycles=cycles,
        **kwargs
    )
    return uid


def fly_Calcium_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=7.99,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Calcium_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Calcium_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(320, 340, speed * 3), (340, 355, speed)],
        enscan_type=enscan_type,
        openshutter=True,

        master_plan=master_plan,
        md=md,
        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        **kwargs
    )
    return uid


def fly_SulfurL_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=7.97,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_SulfurL_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_SulfurL_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(180, 225, speed)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_SiliconL_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=8.01,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_SiliconL_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_SiliconL_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(100, 140, speed)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_SiliconK_NEXAFS(
    speed=0.4,
    pol=0,
    diode_range=8,
    m3_pitch=7.97,
    grating="1200",
    master_plan=None,
    md={},
    enscan_type="fly_SiliconK_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_SiliconK_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(1830, 1870, speed)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Nitrogen_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=7.96,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Nitrogen_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Nitrogen_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(385, 397, speed * 3), (397, 407, speed), (407, 440, speed * 5)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Oxygen_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=7.96,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Oxygen_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Oxygen_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(510, 525, speed * 3), (525, 540, speed), (540, 560, speed * 5)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Fluorine_NEXAFS(
    speed=0.4,
    pol=0,
    diode_range=8,
    m3_pitch=7.98,
    grating="1200",
    master_plan=None,
    md={},
    enscan_type="fly_Fluorine_NEXAFS",
    **kwargs
):
    """
    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Fluorine_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(670, 685, 3 * speed), (685, 700, speed), (700, 740, 3 * speed)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid



def fly_Iron_NEXAFS(
    speed=0.3,
    pol=0,
    diode_range=8,
    m3_pitch=7.98,
    grating="1200",
    master_plan=None,
    md={},
    enscan_type="fly_Iron_NEXAFS",
    **kwargs
):
    """
    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Iron_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(690, 700, 5 * speed), (700, 730, speed), (730, 750, 5 * speed)],
        enscan_type=enscan_type,
        openshutter=True,

        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid




def fly_Boron_NEXAFS(
    speed=0.2,
    pol=0,
    diode_range=8,
    m3_pitch=8.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Boron_NEXAFS",
    **kwargs
):
    """

    @param speed: the speed in eV/second to fly the mono
    @param pol: the polarization of the EPU to set before run
    @param diode_range: sets the range of the SAXS and WAXS beamstop DIODEs for direct beam measurements
    @param m3_pitch: the pitch of the M3 mirror to use for this energy range
    @param grating: the grating of the mono to use for the scan (currently "1200", "250" and "rsoxs" are only valid choices)
    @return: perform a flying NEXAFS scan
    """
    plan_name = "fly_Boron_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(180, 220, speed)],
        enscan_type=enscan_type,
        openshutter=True,
        diode_range=diode_range,
        m3_pitch=m3_pitch,
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def do_HOPGscans_epu(hopggrazing, hopgnormal):
    pols = [0, 20, 40, 55, 70, 90, -1]
    yield from load_sample(hopggrazing)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)
    yield from load_sample(hopgnormal)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)
    yield from load_sample(hopggrazing)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)
    yield from load_sample(hopgnormal)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)
    yield from load_sample(hopggrazing)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)
    yield from load_sample(hopgnormal)
    for polarization in pols:
        yield from full_Carbon_NEXAFS(dets=[Sample_TEY, Izero_Mesh], pol=polarization)


def normal_incidence_rotate_pol_nexafs(
    nexafs_plan="fly_Carbon_NEXAFS",
    polarizations=[0, 20, 45, 70, 90],
    master_plan="normal_incidence_rotate_pol_nexafs",
    md={},
    enscan_type="normal_incidence_rotate_pol_nexafs",
    **kwargs
):
    """
    At normal incidence, rotate the polarization of the X-ray beam and conduct a NEXAFS scan at each polarization
    """
    plan_name = "normal_incidence_rotate_pol_nexafs"
    # grab locals
    arguments = dict(locals())
    arguments["nexafs_plan"] = eval(nexafs_plan).__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = eval(nexafs_plan)
    uids = []
    for pol in polarizations:
        uid = yield from nexafs_plan_plan(angle=90,pol=pol, master_plan=master_plan, md=md, **kwargs)
        uids.append(uid)
    return uids

def fixed_pol_rotate_sample_nexafs(
    nexafs_plan="fly_Carbon_NEXAFS",
    angles=[20, 40, 55, 70, 90],
    polarization=0,
    master_plan="fixed_pol_rotate_sample_nexafs",
    md={},
    enscan_type="fixed_pol_rotate_sample_nexafs",
    **kwargs
):
    """
    At fixed polarization, rotate the sample to do a traditional angle dependant NEXAFS measurement
    """
    plan_name = "fixed_pol_rotate_sample_nexafs"
    # grab locals
    arguments = dict(locals())
    arguments["nexafs_plan"] = eval(nexafs_plan).__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = eval(nexafs_plan)
    uids = []
    for angle in angles:
        uid = yield from nexafs_plan_plan(
            pol=polarization,
            angle=angle,
            master_plan=master_plan,
            md=md, **kwargs)
        uids.append(uid)
    return uids

def epu_angle_from_grazing(real_incident_angle, grazing_angle=20):
    return (
        np.arccos(
            np.cos(real_incident_angle * np.pi / 180)
            * 1
            / (np.cos(grazing_angle * np.pi / 180))
        )
        * 180
        / np.pi
    )


def fixed_sample_rotate_pol_nexafs(
    nexafs_plan="fly_Carbon_NEXAFS",
    grazing_angle=20,
    master_plan="fixed_sample_rotate_pol_nexafs",
    angles=[20, 40, 55, 70, 90],
    md={},
    enscan_type="fixed_sample_rotate_pol_nexafs",
    **kwargs
):
    """
    At fixed incident angle, rotate the polarization angle of the X-rays and take NEXAFS at each step
    polarization is calculated relative to the sample normal
    angles less than the grazing angle are not allowed and are ignored
    """
    plan_name = "fixed_sample_rotate_pol_nexafs"
    # grab locals
    arguments = dict(locals())
    arguments["nexafs_plan"] = eval(nexafs_plan).__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = eval(nexafs_plan)
    uids = []
    for angle in angles:
        if angle < grazing_angle:
            continue
        uid = yield from nexafs_plan_plan(
            angle=grazing_angle,
            pol=epu_angle_from_grazing(angle, grazing_angle),
            master_plan=master_plan,
            md=md,
            **kwargs)
        uids.append(uid)
    return uids

def fixed_sample_rotate_pol_list_nexafs(
    nexafs_plan="fly_Carbon_NEXAFS",
    grazing_angle=20,
    master_plan="fixed_sample_rotate_pol_list_nexafs",
    polarizations=[0, 40, 55, 70, 90],
    md={},
    enscan_type="fixed_sample_rotate_pol_list_nexafs",
    **kwargs
):
    """
    At fixed incident angle, rotate the polarization angle of the X-rays and take NEXAFS at each step
    polarization is calculated relative to the sample normal
    angles less than the grazing angle are not allowed and are ignored
    """
    plan_name = "fixed_sample_rotate_pol_list_nexafs"
    # grab locals
    arguments = dict(locals())
    arguments["nexafs_plan"] = eval(nexafs_plan).__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = eval(nexafs_plan)
    uids = []
    for pol in polarizations:
        uid = yield from nexafs_plan_plan(
            angle=grazing_angle,
            pol=pol,
            master_plan=master_plan,
            md=md,
            **kwargs)
        uids.append(uid)
    return uids
