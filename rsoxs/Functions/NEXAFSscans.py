import numpy as np
from ..HW.signals import Sample_TEY, Izero_Mesh, High_Gain_diode_i400,setup_diode_i400
from ..HW.lakeshore import tem_tempstage
from ..Functions.alignment import sample, load_sample
from ..Functions.alignment import rotate_now
from .energyscancore import NEXAFS_fly_scan_core, NEXAFS_scan_core
from .energyscans import clean_up_md
import bluesky.plan_stubs as bps
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
        pol=pol,
        grating=grating,
        cycles=cycles,
        **kwargs
    )
    return uid


def fly_Titaniuml2_NEXAFS(
    speed=0.2,
    cycles=0,
    pol=0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="fly_Titaniuml2_NEXAFS",
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
    plan_name = "fly_Titaniuml2_NEXAFS"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    uid = yield from NEXAFS_fly_scan_core(
        [(445, 455, speed * 3), (455, 468, speed), (468, 480, speed * 3)],
        enscan_type=enscan_type,
        openshutter=True,
        master_plan=master_plan,
        md=md,
        pol=pol,
        grating=grating,
        cycles=cycles,
        **kwargs
    )
    return uid

def fly_Calcium_NEXAFS(
    speed=0.2,
    pol=0,
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
        pol=pol,
        grating=grating,
        **kwargs
    )
    return uid


def fly_SulfurL_NEXAFS(
    speed=0.2,
    pol=0,
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_SiliconL_NEXAFS(
    speed=0.2,
    pol=0,
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_SiliconK_NEXAFS(
    speed=0.4,
    pol=0,
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Nitrogen_NEXAFS(
    speed=0.2,
    pol=0,
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Oxygen_NEXAFS(
    speed=0.2,
    pol=0,
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid


def fly_Fluorine_NEXAFS(
    speed=0.4,
    pol=0,
    grating="rsoxs",
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid



def fly_Iron_NEXAFS(
    speed=0.3,
    pol=0,
    grating="rsoxs",
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
        pol=pol,
        grating=grating,
        master_plan=master_plan,
        **kwargs
    )
    return uid




def fly_Boron_NEXAFS(
    speed=0.2,
    pol=0,
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
    nexafs_func = globals()[nexafs_plan]
    arguments["nexafs_plan"] = nexafs_func.__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = nexafs_func
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
    nexafs_func = globals()[nexafs_plan]
    arguments["nexafs_plan"] = nexafs_func.__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = nexafs_func
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
    nexafs_func = globals()[nexafs_plan]
    arguments["nexafs_plan"] = nexafs_func.__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = nexafs_func
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
    nexafs_func = globals()[nexafs_plan]
    arguments["nexafs_plan"] = nexafs_func.__name__
    clean_up_md(arguments, md, **kwargs)
    nexafs_plan_plan = nexafs_func
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



def nexafs_plan(edge, speed='normal', speed_ratios=None, cycles=0, mode="sample", polarizations = [0],angles = None,grating='rsoxs',diode_range='high',temperatures=None,temp_ramp_speed=10,temp_wait=True,sim_mode=0, md = None, **kwargs):
    # nexafs plan is a bit like rsoxs plan, in that it comprises a full experiment however each invdividual energy scan is going to be its own run (as it has been in the past)  this will make analysis much easier
    valid = True
    valid_text = ""
    params, time = get_nexafs_scan_params(edge,speed,speed_ratios)
    if not isinstance(params,list):
        valid = False
        valid_text = f'\n\nERROR - parameters from the given edge, speed, and speed_ratios are bad\n\n'
    if cycles:
        time *= 2 * cycles
    for temp in temperatures:
        
        if temp is not None:
            if 0<temp<350:
                valid = False
                valid_text += f"\n\nERROR - temperature of {temp} is out of range\n\n"
            if temp_wait > 30:
                valid = False
                valid_text += f"\n\nERROR - temperature wait time of {temp_wait} minutes is too long\n\n"
            if 0.1 > temp_ramp_speed or temp_ramp_speed > 100:
                valid = False
                valid_text += f"\n\nERROR - temperature ramp speed of {temp_ramp_speed} is not True/False\n\n"
    
    
    if isinstance(temperatures,list) and not sim_mode:
        yield from bps.mv(tem_tempstage.ramp_rate,temp_ramp_speed)
    if diode_range=='high' and not sim_mode:
        yield from setup_diode_i400()
    elif diode_range=='low' and not sim_mode:
        yield from High_Gain_diode_i400()
    if max(edge) > 1200 and grating == 'rsoxs':
        valid = False
        valid_text += f'\n\nERROR - energy is not appropriate for this grating\n\n'
    if not valid:
        # don't go any further, even in simulation mode, because we know the inputs are wrong
        if not sim_mode:
            raise ValueError(valid_text)
        else:
            return valid_text
        # if we are still valid - try to continue
    for temp in temperatures:
        if temp_wait and not sim_mode:
            yield from bps.mv(tem_tempstage,temp)
        elif not sim_mode:
            yield from bps.mv(tem_tempstage.setpoint,temp)
        for grazing_angle in angles:
            for pol in polarizations:
                if mode == "sample":
                    if pol < grazing_angle:
                        valid = False
                        valid_text += "\n\nERROR - sample frame polarization less than grazing angle is not possible\n\n"
                        if not sim_mode:
                            print('\n\nERROR - sample frame polarization less than grazing angle is not possible\n\n Skipping this scan')
                            next
                    pol=epu_angle_from_grazing(pol, grazing_angle)
                valid_text = yield from NEXAFS_fly_scan_core(
                                    params,
                                    cycles=cycles,
                                    openshutter=True,
                                    pol=pol,
                                    angle=grazing_angle,
                                    grating=grating,
                                    sim_mode=sim_mode,
                                    md=md,)

    return valid_text


def get_nexafs_scan_params(edge,speed = "normal", speed_ratios = None):
    """
    creates fly NEXAFS scan parameters, given an edge (which includes thresholds for different speed regions) base speed (eV/sec) and speed ratios between the different regions 
    Args:
        edge: String or tuple of 2 or more numbers (the only required entry)
            if string, this should be a key in the lookup tables refering to an absorption edge energy
            if tuple, this is the thresholds of the different ranges, i.e. start of pre edge, start of main edge, start of post edge, end etc.
                the length of the tuple should correspond to 1- the speed ratios (or a default can be chosen if between 2 and 6 thresholds are given)
        speed: String or Number (normal if not defined)
            if string, this should be in the lookup table of standard speeds for scans
            if number, this is the base speed in eV/sec
        speed_ratios: string or tuple of numbers
            if string, this should be in the lookup table of standard intervals
            if a tuple, this must have one less element than the edge tuple (either explicitely entered or from the lookup table)
                the values are the ratio of energy steps between the different regions defined by edge
                
    """
    
    edge_names = {"c":"Carbon",
              "carbonk": "Carbon",
              "ck": "Carbon",
              "n": "Nitrogen",
              "nitrogenk": "Nitrogen",
              "nk": "Nitrogen",
              "f": "Fluorine",
              "fluorinek": "Fluorine",
              "fk": "Fluorine",
              "o": "Oxygen",
              "oxygenk": "Oxygen",
              "ok": "Oxygen",
              "ca": "Calcium",
              "calciumk": "Calcium",
              "cak": "Calcium",
             }


     # these define the default edges of the intervals
    edges = {"carbon":(250,282,297,350),
             "oxygen":(500,525,540,560),
             "fluorine":(650,680,700,740),
             "aluminium":(1500,1560,1580,1600),
             "nitrogen":(370,397,407,440),
             "zincl": (1000,1015,1035,1085),
             "sulfurl":(150,160,170,200),
             "calcium":(320,345,355,380)
            }
     # these are the default interval ratios for each section
    ratios_table = {
                     "default 4":(5,1,5),
                     "default 5":(5,1,2,5),
                     "default 6":(5,2,1,2,5),
                     "default 2":(1,),
                     "default 3":(5,1),
                    }

    speed_table = {"normal": 0.2,
                   "quick":0.4,
                   "fast":0.5,
                   "very fast":1,
                   "slow":0.1,
                   "very slow":0.05,
                  }
    edge_input = edge
    if isinstance(edge,str):
        if edge.lower() in edge_names.keys():
            edge = edge_names[edge.lower()]
            edge_input = edge.lower()
        if edge.lower() in edges.keys():
            edge = edges[edge.lower()]
    if not isinstance(edge,tuple):
        raise TypeError(f"invalid edge {edge} - no key of that name was found")
    
    if isinstance(speed,str):
        if speed.lower() in speed_table.keys():
            speed = speed_table[speed.lower()]
    if not isinstance(speed, (float,int)):
        raise TypeError(f"frame number {frame} was not found or is not a valid number")
    
    if speed_ratios == None:
        if str(edge_input).lower() in ratios_table.keys():
            speed_ratios = ratios_table[edge_input.lower()]
        elif f"default {len(edge)}" in ratios_table.keys():
            speed_ratios = ratios_table[f"default {len(edge)}"]
        else:
            speed_ratios = (1,)*(len(edge)-1)
    else:
        if not isinstance(speed_ratios,(tuple)):
            speed_ratios = ratios_table[speed_ratios]
    if not isinstance(speed_ratios,(tuple)):
        raise TypeError(f"invalid ratios {speed_ratios}")
    if len(speed_ratios) + 1 != len(edge):
        raise ValueError(f'got the wrong number of intervals {len(speed_ratios)} expected {len(edge)-1}')
    scan_params = []
    time = 0
    for i, ratio in enumerate(speed_ratios):
        scan_params += [(edge[i],edge[i+1],float(ratio)*float(speed))]
        time +=abs(edge[i+1] - edge[i]) / (float(ratio)*float(speed))

    return scan_params, time