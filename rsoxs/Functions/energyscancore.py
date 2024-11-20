from cycler import cycler
from itertools import chain
from bluesky.utils import Msg, short_uid as _short_uid
from bluesky.protocols import Readable, Flyable
import bluesky.utils as utils
from bluesky.plan_stubs import trigger_and_read, move_per_step, stage, unstage
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.plan_stubs import (
    checkpoint,
    abs_set,
    sleep,
    trigger,
    read,
    wait,
    create,
    save,
    unstage,
)
from bluesky.preprocessors import finalize_decorator
from bluesky.preprocessors import rewindable_wrapper, finalize_wrapper
from bluesky.utils import short_uid, separate_devices, all_safe_rewind
from collections import defaultdict
from bluesky import preprocessors as bpp
from bluesky import FailedStatus
import numpy as np
import redis_json_dict
from functools import partial
from ophyd import Device, Signal
from ophyd.status import StatusTimeoutError
import warnings
from copy import deepcopy
from ..HW.energy import (
    en,
    mono_en,
    epu_gap,
    grating_to_250,
    grating_to_rsoxs,
    grating_to_1200,
    set_polarization,
)
from ..HW.energy import (
    #Mono_Scan_Speed_ev,
    #Mono_Scan_Start,
    #Mono_Scan_Start_ev,
    #Mono_Scan_Stop,
    #Mono_Scan_Stop_ev,
    get_gap_offset,
)
from ..HW.motors import (
    sam_X,
    sam_Y,
    sam_Z,
    sam_Th,
)
from sst_hw.mirrors import mir3
from ..HW.detectors import waxs_det#, saxs_det
from ..HW.signals import DiodeRange,Beamstop_WAXS,Beamstop_SAXS,Izero_Mesh,Sample_TEY, Beamstop_SAXS_int,Beamstop_WAXS_int,DownstreamLargeDiode, DownstreamLargeDiode_int, Izero_Mesh_int,Sample_TEY_int, ring_current
from ..HW.lakeshore import tem_tempstage
from ..Functions.alignment import rotate_now
from ..Functions.common_procedures import set_exposure
from ..Functions.fly_alignment import find_optimum_motor_pos, db, return_NullStatus_decorator #bec, 

from .flystream_wrapper import flystream_during_wrapper
from sst_hw.diode import (
    Shutter_open_time,
    Shutter_control,
    Shutter_enable,
    Shutter_trigger,
    shutter_open_set
)
from sst_funcs.printing import run_report


from ..startup import rsoxs_config, RE
from bluesky.utils import ensure_generator, short_uid as _short_uid, single_gen
from bluesky.preprocessors import plan_mutator



run_report(__file__)



import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.utils import short_uid





SLEEP_FOR_SHUTTER = 1






def cleanup():
    # make sure the shutter is closed, and the scanlock if off after a scan, even if it errors out
    yield from bps.mv(en.scanlock, 0)
    yield from bps.mv(Shutter_control, 0)
    

def NEXAFS_step_scan_core(
    dets=None,    # a list of detectors to run at each step - must be scalar type detectors wtih set_exp functions
    energy=None,  # optional energy object to set energy commands to - sets to energy by default, but allows for simulation
    lockscan = True, # whether to lock the harmonic and other energy components during a scan
    grating="no change", # what grating to use for this scan

    energies=None,# a list of energies to run through in the inner loop
    times=None,   # exposure times for each energy (same length as energies) (cycler add to energies)

    polarizations=None, # polarizations to run as an outer loop (cycler multiply with previous)
    
    locations=None,       # locations to run together as an outer loop  (cycler multiply with previous) list of location dicts
    temperatures=None,       # locations to run as an outer loop  (cycler multiply with previous generally, but optionally add to locations - see next)
    temp_wait = True,

    temps_with_locations = False, # indicates to move locations and temperatures at the same time, not multiplying exposures (they must be the same length!)

    enscan_type=None,     # optional extra string name to describe this type of scan - will make timing
    master_plan=None,   # if this is lying within an outer plan, that name can be stored here
    sim_mode=False,  # if true, check all inputs but do not actually run anything
    md=None,  # md to pass to the scan
    signals = None,
    check_exp = False,
    **kwargs #extraneous settings from higher level plans are ignored
):
    # grab locals
    if dets is None:
        dets = [Beamstop_SAXS_int,Beamstop_WAXS_int, DownstreamLargeDiode_int, Izero_Mesh_int,Sample_TEY_int]
    if energies is None:
        energies = []
    if times is None:
        times = []
    if polarizations is None:
        polarizations = []
    if md is None:
        md = {}
    if energy is None:
        energy = en.energy
    arguments = dict(locals())
    del arguments["md"]  # no recursion here!
    arguments["energy"] = arguments["energy"].name
    if md is None:
        md = {}
    md.setdefault("acq_history", [])

    for argument in arguments:
        if isinstance(argument,np.ndarray):
            argument = list(argument)
    md["acq_history"].append({"plan_name": "NEXAFS_step_scan_core", "arguments": arguments})
    md.update({"plan_name": enscan_type, "master_plan": master_plan,'plan_args' :arguments })
    # print the current sample information
    # sample()  # print the sample information  Removing this because RE will no longer be loaded with sample data
    # set the exposure times to be hinted for the detector which will be used

    # validate inputs
    valid = True
    validation = ""
    newdets = []
    detnames = []
    for det in dets:
        if not isinstance(det, Device):
            try:
                det_dev = globals()[det]
                newdets.append(det_dev)
                detnames.append(det_dev.name)
            except Exception:
                valid = False
                validation += f"detector {det} is not an ophyd device\n"
        else:
            newdets.append(det)
            detnames.append(det.name)
    if len(newdets) < 1:
        valid = False
        validation += "No detectors are given\n"
    if min(energies) < 70 or max(energies) > 2200:
        valid = False
        validation += "energy input is out of range for SST 1\n"
    if grating == "1200":
        if min(energies) < 150:
            valid = False
            validation += "energy is to low for the 1200 l/mm grating\n"
    elif grating == "250":
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    elif grating == "rsoxs":
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    else:
        valid = False
        validation += "invalid grating was chosen"
    if max(times) > 60:
        valid = False
        validation += "exposure times greater than 60 seconds are not valid\n"
    if min(polarizations) < -1 or max(polarizations) > 180:
        valid = False
        validation += f"a provided polarization is not valid\n"
    if isinstance(temperatures,list):
        if len(temperatures)==0:
            temperatures = None
        if min(temperatures,default=35) < 20 or max(temperatures,default=35) > 300:
            valid = False
            validation += f"temperature out of range\n"
    else:
        temperatures = None
        temps_with_locations=False
    if not isinstance(energy, Device):
        valid = False
        validation += f"energy object {energy} is not a valid ophyd device\n"
    motor_positions=[]
    if isinstance(locations,list):
        if len(locations)>0:
            motor_positions = [{d['motor']: d['position'] for d in location} for location in locations]
            angles = {d.get('angle', None) for d in motor_positions}
            angles.discard(None)
            xs = {d.get('x', None) for d in motor_positions}
            xs.discard(None)
            if min(xs,default=0) < -13 or max(xs,default=0) > 13:
                valid = False
                validation += f"X motor is out of vaild range\n"
            ys = {d.get('y', None) for d in motor_positions}
            ys.discard(None)
            if min(ys,default=0) < -190 or max(ys,default=0) > 355:
                valid = False
                validation += f"Y motor is out of vaild range\n"
            zs = {d.get('z', None) for d in motor_positions}
            zs.discard(None)
            if min(zs,default=0) < -13 or max(zs,default=0) > 13:
                valid = False
                validation += f"Z motor is out of vaild range\n"
            temzs = {d.get('temz', None) for d in motor_positions}
            temzs.discard(None)
            if min(temzs,default=0) < 0 or max(temzs,default=0) > 150:
                valid = False
                validation += f"TEMz motor is out of vaild range\n"
            if max(temzs,default=0) > 100 and min(ys,default=50) < 20:
                valid = False
                validation += f"potential clash between TEY and sample bar\n"
    else:
        locations = None
        temps_with_locations = False
    if(temps_with_locations):
        if len(temperatures)!= len(locations):
            valid = False
            validation += f"temperatures and locations are different lengths, cannot be simultaneously changed\n"
    if sim_mode:
        if valid:
            retstr = f"scanning {detnames} from {min(energies)} eV to {max(energies)} eV on the {grating} l/mm grating\n"
            retstr += f"    in {len(times)} steps with exposure times from {min(times)} to {max(times)} seconds\n"
            return retstr
        else:
            return validation

    if not valid:
        raise ValueError(validation)
    for det in newdets:
        det.exposure_time.kind = "hinted"
    # set the grating
    if 'hopg_loc' in md.keys():
        print('hopg location found')
        hopgx = md['hopg_loc']['x']
        hopgy = md['hopg_loc']['y']
        hopgth = md['hopg_loc']['th']
    else:
        print('no hopg location found')
        hopgx = None
        hopgy = None
        hopgth = None
    print(f'checking grating is {grating}')
    if grating == "1200":
        yield from grating_to_1200(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "250":
        yield from grating_to_250(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "rsoxs":
        yield from grating_to_rsoxs(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    # set up the scan cycler
    sigcycler = cycler(energy, energies)
    yield from bps.mv(en.scanlock, 0)
    yield from bps.sleep(0.5)
    yield from bps.mv(energy, energies[0])  # move to the initial energy (unlocked)
    if lockscan:
        yield from bps.mv(en.scanlock, 1)  # lock the harmonic, grating, m3_pitch everything based on the first energy
    old_n_exp = {}
    for det in newdets:
        sigcycler += cycler(det.exposure_time, times.copy()) # cycler for changing each detector exposure time
    if isinstance(polarizations, (list, redis_json_dict.redis_json_dict.ObservableSequence)):
        sigcycler = cycler(en.polarization, list(polarizations))*sigcycler # cycler for polarization changes (multiplied means we do everything above for each polarization)

    #print(f'locations {locations}')
    #print(f'temperatures {temperatures}')
    
    if(temps_with_locations):
        angles = [d.get('th', None) for d in motor_positions]
        xs = [d.get('x', None) for d in motor_positions]
        ys = [d.get('y', None) for d in motor_positions]
        zs = [d.get('z', None) for d in motor_positions]
        loc_temp_cycler = cycler(sam_X,xs)
        loc_temp_cycler += cycler(sam_Y,ys) # adding means we run the cyclers simultaenously, 
        loc_temp_cycler += cycler(sam_Z,zs)
        loc_temp_cycler += cycler(sam_Th,angles)
        if(temp_wait):
            loc_temp_cycler += cycler(tem_tempstage,temperatures) 
        else:
            loc_temp_cycler += cycler(tem_tempstage.setpoint,temperatures)
        sigcycler = loc_temp_cycler*sigcycler # add cyclers for temperature and location changes (if they are linked) one of everything above (energies, polarizations) for each temp/location
    else:
        if isinstance(locations,list):
            angles = [d.get('th', None) for d in motor_positions]
            xs = [d.get('x', None) for d in motor_positions]
            ys = [d.get('y', None) for d in motor_positions]
            zs = [d.get('z', None) for d in motor_positions]
            loc_cycler = cycler(sam_X,xs)
            loc_cycler += cycler(sam_Y,ys)
            loc_cycler += cycler(sam_Z,zs)
            loc_cycler += cycler(sam_Th,angles)
            sigcycler = loc_cycler*sigcycler # run every energy for every polarization and every polarization for every location
        if isinstance(temperatures,list):
            if(temp_wait):
                sigcycler = cycler(tem_tempstage,temperatures)*sigcycler # run every location for each temperature step
            else:
                sigcycler = cycler(tem_tempstage.setpoint,temperatures)*sigcycler # run every location for each temperature step


    #print(sigcycler)
    exps = {}
    
    yield from bps.mv(Shutter_control, 1) # open the shutter for the run
    yield from finalize_wrapper(
        bp.scan_nd(newdets, 
                   sigcycler, 
                   md=md,
                   ),
        cleanup()
    )



def new_en_scan_core(
    dets=None,    # a list of detectors to run at each step - get from md by default
    energy=None,  # optional energy object to set energy commands to - sets to energy by default, but allows for simulation
    lockscan = True, # whether to lock the harmonic and other energy components during a scan
    grating="no change", # what grating to use for this scan

    energies=None,# a list of energies to run through in the inner loop
    times=None,   # exposure times for each energy (same length as energies) (cycler add to energies)

    repeats = 1, # number of images to take at each step

    polarizations=None, # polarizations to run as an outer loop (cycler multiply with previous)
    
    locations=None,       # locations to run together as an outer loop  (cycler multiply with previous) list of location dicts
    temperatures=None,       # locations to run as an outer loop  (cycler multiply with previous generally, but optionally add to locations - see next)
    temp_wait = True,

    temps_with_locations = False, # indicates to move locations and temperatures at the same time, not multiplying exposures (they must be the same length!)

    enscan_type=None,     # optional extra string name to describe this type of scan - will make timing
    master_plan=None,   # if this is lying within an outer plan, that name can be stored here
    sim_mode=False,  # if true, check all inputs but do not actually run anything
    md=None,  # md to pass to the scan
    signals = [Beamstop_WAXS_int, Beamstop_SAXS_int, Izero_Mesh_int, Sample_TEY_int,mono_en,epu_gap,ring_current],
    check_exposure = False,
    **kwargs #extraneous settings from higher level plans are ignored
):
    ## Used for RSoXS scattering scans
    # warning about all kwargs that are being ignored
    for kwarg,value in kwargs.items():
        if kwarg not in ['uid','sample_id','priority','group','configuration','type']:
            warnings.warn(f"argument {kwarg} with value {value} is being ignored because new_en_scan_core does not understand how to use it",stacklevel=2)
    # grab localsfil
    if signals is None:
        signals = []
    if dets is None:
        if md['RSoXS_Main_DET'] == 'WAXS':
            dets = ['waxs_det']
        else:
            dets = ['saxs_det']

    if energies is None:
        energies = []
    if times is None:
        times = []
    if polarizations is None:
        polarizations = []
    if md is None:
        md = {}
    if energy is None:
        energy = en.energy
    arguments = dict(locals())
    del arguments["md"]  # no recursion here!
    arguments["signals"] = [signal.name for signal in arguments["signals"]]
    arguments["energy"] = arguments["energy"].name
    if md is None:
        md = {}
    md.setdefault("acq_history", [])

    for argument in arguments:
        if isinstance(argument,np.ndarray):
            argument = list(argument)
    md["acq_history"].append({"plan_name": "en_scan_core", "arguments": arguments})
    md.update({"plan_name": enscan_type, "master_plan": master_plan,'plan_args' :arguments })
    # print the current sample information
    # sample()  # print the sample information  Removing this because RE will no longer be loaded with sample data
    # set the exposure times to be hinted for the detector which will be used

    # validate inputs
    valid = True
    validation = ""
    newdets = []
    detnames = []
    for det in dets:
        if not isinstance(det, Device):
            try:
                det_dev = globals()[det]
                newdets.append(det_dev)
                detnames.append(det_dev.name)
            except Exception:
                valid = False
                validation += f"detector {det} is not an ophyd device\n"
        else:
            newdets.append(det)
            detnames.append(det.name)
    
    goodsignals = []
    signames = []
    for signal in signals:
        if not isinstance(signal, (Device,Signal)):
            try:
                signal_dev = globals()[signal]
                goodsignals.append(signal_dev)
                signames.append(signal_dev.name)
            except Exception:
                valid = False
                validation += f"signal {signal} is not an ophyd signal\n"
        else:
            goodsignals.append(signal)
            signames.append(signal.name)
        #signals.extend([det.cam.acquire_time])
    goodsignals.extend([Shutter_open_time])
    if len(newdets) != 1: # shutter can only work with a single lead detector
        valid = False
        validation += f"a number of detectors that is not 1 was given :{len(newdets)}\n"
    if min(energies) < 70 or max(energies) > 2200:
        valid = False
        validation += "energy input is out of range for SST 1\n"
    if grating in ["1200",1200]:
        if min(energies) < 150:
            valid = False
            validation += "energy is to low for the 1200 l/mm grating\n"
    elif grating in ["250",250]:
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    elif grating == "rsoxs":
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    else:
        valid = False
        validation += "invalid grating was chosen"
    if max(times) > 10:
        valid = False
        validation += "exposure times greater than 10 seconds are not valid\n"
    if min(polarizations) < -1 or max(polarizations) > 180:
        valid = False
        validation += f"a provided polarization is not valid\n"
    if isinstance(temperatures,list):
        if len(temperatures)==0:
            temperatures = None
        if min(temperatures,default=35) < 20 or max(temperatures,default=35) > 300:
            valid = False
            validation += f"temperature out of range\n"
    else:
        temperatures = None
        temps_with_locations=False
    if not isinstance(energy, Device):
        valid = False
        validation += f"energy object {energy} is not a valid ophyd device\n"
    motor_positions=[]
    if isinstance(locations,list):
        if len(locations)>0:
            motor_positions = [{d['motor']: d['position'] for d in location} for location in locations]
            angles = {d.get('angle', None) for d in motor_positions}
            angles.discard(None)
            xs = {d.get('x', None) for d in motor_positions}
            xs.discard(None)
            if min(xs,default=0) < -13 or max(xs,default=0) > 13:
                valid = False
                validation += f"X motor is out of vaild range\n"
            ys = {d.get('y', None) for d in motor_positions}
            ys.discard(None)
            if min(ys,default=0) < -190 or max(ys,default=0) > 355:
                valid = False
                validation += f"Y motor is out of vaild range\n"
            zs = {d.get('z', None) for d in motor_positions}
            zs.discard(None)
            if min(zs,default=0) < -13 or max(zs,default=0) > 13:
                valid = False
                validation += f"Z motor is out of vaild range\n"
            # temxs = {d.get('temx', None) for d in motor_positions}
            # temxs.discard(None)
            # if min(xs) < -13 or max(xs) > 13:
            #     valid = False
            #     validation += f"X motor is out of vaild range\n"
            # temys = {d.get('temy', None) for d in motor_positions}
            # temys.discard(None)
            # if min(xs) < -13 or max(xs) > 13:
            #     valid = False
            #     validation += f"X motor is out of vaild range\n"
            temzs = {d.get('temz', None) for d in motor_positions}
            temzs.discard(None)
            if min(temzs,default=0) < 0 or max(temzs,default=0) > 150:
                valid = False
                validation += f"TEMz motor is out of vaild range\n"
            if max(temzs,default=0) > 100 and min(ys,default=50) < 20:
                valid = False
                validation += f"potential clash between TEY and sample bar\n"
    else:
        locations = None
        temps_with_locations = False
    if(temps_with_locations):
        if len(temperatures)!= len(locations):
            valid = False
            validation += f"temperatures and locations are different lengths, cannot be simultaneously changed\n"
    if sim_mode:
        if valid:
            retstr = f"scanning {detnames} from {min(energies)} eV to {max(energies)} eV on the {grating} l/mm grating\n"
            retstr += f"    in {len(times)} steps with exposure times from {min(times)} to {max(times)} seconds\n"
            return retstr
        else:
            return validation

    if not valid:
        raise ValueError(validation)
    for det in newdets:
        det.cam.acquire_time.kind = "hinted"
    # set the grating
    if 'hopg_loc' in md.keys():
        print('hopg location found')
        hopgx = md['hopg_loc']['x']
        hopgy = md['hopg_loc']['y']
        hopgth = md['hopg_loc']['th']
    else:
        print('no hopg location found')
        hopgx = None
        hopgy = None
        hopgth = None
    print(f'checking grating is {grating}')
    if grating == "1200":
        yield from grating_to_1200(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "250":
        yield from grating_to_250(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "rsoxs":
        yield from grating_to_rsoxs(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    # set up the scan cycler
    sigcycler = cycler(energy, energies)
    shutter_times = [i * 1000 for i in times]
    yield from bps.mv(en.scanlock, 0)
    yield from bps.sleep(0.5)
    yield from bps.mv(energy, energies[0])  # move to the initial energy (unlocked)

    if lockscan:
        yield from bps.mv(en.scanlock, 1)  # lock the harmonic, grating, m3_pitch everything based on the first energy
    old_n_exp = {}
    for det in newdets:
        old_n_exp[det.name] = det.number_exposures
        det.number_exposures = repeats
        sigcycler += cycler(det.cam.acquire_time, times.copy()) # cycler for changing each detector exposure time
    for sig in goodsignals:
        if hasattr(sig,'exposure_time'):
            sigcycler += cycler(sig.exposure_time, times.copy()) # any ophyd signal devices should have their exposure times set here
            # TODO: potentially shorten the exposure times by some constant to allow for shutter opening and closing times
    sigcycler += cycler(Shutter_open_time, shutter_times) # cycler for changing the shutter opening time
    if isinstance(polarizations,(list, redis_json_dict.redis_json_dict.ObservableSequence)):
        sigcycler = cycler(en.polarization, list(polarizations))*sigcycler # cycler for polarization changes (multiplied means we do everything above for each polarization)

    #print(f'locations {locations}')
    #print(f'temperatures {temperatures}')
    
    if(temps_with_locations):
        angles = [d.get('th', None) for d in motor_positions]
        xs = [d.get('x', None) for d in motor_positions]
        ys = [d.get('y', None) for d in motor_positions]
        zs = [d.get('z', None) for d in motor_positions]
        loc_temp_cycler = cycler(sam_X,xs)
        loc_temp_cycler += cycler(sam_Y,ys) # adding means we run the cyclers simultaenously, 
        loc_temp_cycler += cycler(sam_Z,zs)
        loc_temp_cycler += cycler(sam_Th,angles)
        if(temp_wait):
            loc_temp_cycler += cycler(tem_tempstage,temperatures) 
        else:
            loc_temp_cycler += cycler(tem_tempstage.setpoint,temperatures)
        sigcycler = loc_temp_cycler*sigcycler # add cyclers for temperature and location changes (if they are linked) one of everything above (energies, polarizations) for each temp/location
    else:
        if isinstance(locations,list):
            angles = [d.get('th', None) for d in motor_positions]
            xs = [d.get('x', None) for d in motor_positions]
            ys = [d.get('y', None) for d in motor_positions]
            zs = [d.get('z', None) for d in motor_positions]
            loc_cycler = cycler(sam_X,xs)
            loc_cycler += cycler(sam_Y,ys)
            loc_cycler += cycler(sam_Z,zs)
            loc_cycler += cycler(sam_Th,angles)
            sigcycler = loc_cycler*sigcycler # run every energy for every polarization and every polarization for every location
        if isinstance(temperatures,list):
            if(temp_wait):
                sigcycler = cycler(tem_tempstage,temperatures)*sigcycler # run every location for each temperature step
            else:
                sigcycler = cycler(tem_tempstage.setpoint,temperatures)*sigcycler # run every location for each temperature step


    exps = {}
    yield from finalize_wrapper(bp.scan_nd(goodsignals, 
                sigcycler, 
                md=md,
                per_step=partial(one_nd_sticky_exp_step,
                                    remember=exps,
                                    take_reading=partial(take_exposure_corrected_reading,
                                                        lead_detector = newdets[0],
                                                        shutter = Shutter_control,
                                                        check_exposure=check_exposure))
                ),
        cleanup()
    )
    for det in newdets:
        det.number_exposures = old_n_exp[det.name]


def NEXAFS_fly_scan_core(
    scan_params,
    openshutter=True,
    pol=0,
    grating="best",
    enscan_type=None,
    master_plan=None,
    angle=None,
    cycles=0,
    locked = True,
    md=None,
    sim_mode=False,
    **kwargs #extraneous settings from higher level plans are ignored
):
    # grab locals
    if md is None:
        md = {}
    arguments = dict(locals())
    del arguments["md"]  # no recursion here!
    if md is None:
        md = {}
    md.setdefault("acq_history", [])

    for argument in arguments:
        if isinstance(argument,np.ndarray):
            argument = list(argument)
    md["acq_history"].append(
        {"plan_name": "NEXAFS_fly_scan_core", "arguments": arguments}
    )
    md.update({"plan_name": enscan_type, "master_plan": master_plan})
    # validate inputs
    valid = True
    validation = ""
    energies = np.empty(0)
    speeds = []
    scan_params = deepcopy(scan_params)
    for scanparam in scan_params:
        (sten, enden, speed) = scanparam
        energies = np.append(energies, np.linspace(sten, enden, 10))
        speeds.append(speed)
    if len(energies) < 10:
        valid = False
        validation += f"scan parameters {scan_params} could not be parsed\n"
    if min(energies) < 70 or max(energies) > 2200:
        valid = False
        validation += "energy input is out of range for SST 1\n"
    if grating in ["1200",1200]:
        if min(energies) < 150:
            valid = False
            validation += "energy is to low for the 1200 l/mm grating\n"
    elif grating in ["250",250]:
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    elif grating == "rsoxs":
        if max(energies) > 1300:
            valid = False
            validation += "energy is too high for 250 l/mm grating\n"
    else:
        valid = False
        validation += "invalid grating was chosen"
    if pol < -1 or pol > 180:
        valid = False
        validation += f"polarization of {pol} is not valid\n"
    if angle is not None:
        if -155 > angle or angle > 195:
            valid = False
            validation += f"angle of {angle} is out of range\n"
    if sim_mode:
        if valid:
            retstr = f"fly scanning from {min(energies)} eV to {max(energies)} eV on the {grating} l/mm grating\n"
            retstr += f"    at speeds from {max(speeds)} to {max(speeds)} ev/second\n"
            return retstr
        else:
            return validation
    if not valid:
        raise ValueError(validation)
    if angle is not None:
        print(f'moving angle to {angle}')
        yield from rotate_now(angle)
    if 'hopg_loc' in md.keys():
        hopgx = md['hopg_loc']['x']
        hopgy = md['hopg_loc']['y']
        hopgth = md['hopg_loc']['th']
    else:
        hopgx = None
        hopgy = None
        hopgth = None
    if grating == "1200":
        yield from grating_to_1200(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "250":
        yield from grating_to_250(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    elif grating == "rsoxs":
        yield from grating_to_rsoxs(hopgx=hopgx,hopgy=hopgy,hopgtheta=hopgth)
    if np.isnan(pol):
        pol = en.polarization.setpoint.get()
    (en_start, en_stop, en_speed) = scan_params[0]
    yield from bps.mv(en.scanlock, 0) # unlock parameters
    print("Moving to initial position before scan start")
    yield from bps.mv(en.energy, en_start+10, en.polarization, pol)  # move to the initial energy
    samplepol = en.sample_polarization.setpoint.get()
    if locked:
        yield from bps.mv(en.scanlock, 1) # lock parameters for scan, if requested
    yield from bps.mv(en.energy, en_start-0.10 )  # move to the initial energy
    print(f"Effective sample polarization is {samplepol}")
    for kwarg,value in kwargs.items():
        if kwarg not in ['uid','sample_id','priority','group','configuration','type']:
            warnings.warn(f"argument {kwarg} with value {value} is being ignored because NEXAFS_fly_scan_core does not understand how to use it",stacklevel=2)
    if cycles>0:
        rev_scan_params = []
        for (start, stop, speed) in scan_params:
            rev_scan_params = [(stop, start, speed)]+rev_scan_params
        scan_params += rev_scan_params
        scan_params *= int(cycles)

    uid = ""
    if openshutter:
        yield from bps.mv(Shutter_enable, 0)
        yield from bps.mv(Shutter_control, 1)
    uid = (yield from finalize_wrapper(flyer_scan_energy(list(chain.from_iterable(scan_params)), md=md, locked=locked, polarization=pol),cleanup()))

    return uid


def flyer_scan_energy(scan_params, md={},locked=True,polarization=0):
    """
    Specific scan for SST-1 monochromator fly scan, while catching up with the undulator

    scan proceeds as:
    1.) set up the flying parameters in the monochromator
    2.) move to the starting position in both undulator and monochromator
    3.) begin the scan (take baseline, begin monitors)
    4.) read the current mono readback
    5.) set the undulator to move to the corresponding position
    6.) if the mono is still running (not at end position), return to step 4
    7.) if the mono is done, load the next parameters and start at step 1
    8.) if no more parameters, end the scan

    Parameters
    ----------
    scan_params : a list of tuples consisting of:
        (start_en : eV to begin the scan,
        stop_en : eV to stop the scan,
        speed_en : eV / second to move the monochromator)
        the stop energy of each tuple should match the start of the next to make a continuous scan
            although this is not strictly enforced to allow for flexibility
    pol : polarization to run the scan
    grating : grating to run the scan
    md : dict, optional
        metadata

    """
    detectors = [Beamstop_WAXS_int,  Izero_Mesh_int, Sample_TEY_int]


    _md = {
        "detectors": [detector.name for detector in detectors],
        "motors": [en.name],
        "plan_name": "flyer_scan_energy",
        "hints": {},
    }
    _md.update(md or {})
    flyers = [d for d in detectors + [en] if isinstance(d, Flyable)]
    readers = [d for d in detectors + [en] if isinstance(d, Readable)]
    for reader in readers:
        if hasattr(reader,'set_exposure'):
            reader.set_exposure(0.5)

    en.preflight(*scan_params,locked=locked,time_resolution=0.5)

    @bpp.stage_decorator(readers)
    @bpp.run_decorator(md=_md)
    def inner_flyscan():
        status = en.fly()

        while not status.done:
            yield from trigger_and_read(readers)

        en.land()

    return (yield from flystream_during_wrapper(inner_flyscan(), flyers,stream=False))




def trigger_and_read_with_shutter(devices, lead_detector=None, shutter=None, name='primary'):
    """
    Trigger and read a list of detectors and bundle readings into one Event.

    based on trigger_and_read, but adding parameter for the "lead" detector, which is triggered first,
    and a shutter which will be waited for (controlled by the lead detector) 
    once the shutter opens, all the rest of the devices are triggered and read


    Parameters
    ----------
    devices : iterable
        devices to trigger (if they have a trigger method) and then read
        NOT INCLUDING the lead detector
    lead_detector : device with a trigger method which should be triggered first
        and which will open the shutter at some point
    shutter : device with set and waiting enabled which can be waited for after 
        triggering the lead detector
    name : string, optional
        event stream name, a convenient human-friendly identifier; default
        name is 'primary'

    Yields
    ------
    msg : Msg
        messages to 'trigger', 'wait' and 'read'
    """

    devices = separate_devices(devices)  # remove redundant entries
    rewindable = all_safe_rewind(devices)  # if devices can be re-triggered

    def inner_trigger_and_read():
        grp = _short_uid('trigger')
        yield from bps.abs_set(shutter, 1, just_wait=True, group='shutter') # start waiting for the shutter to open
        yield from bps.trigger(lead_detector, group='measure') # trigger the lead_detector, which will eventually open the shutter
        yield from bps.wait(group='shutter') # wait for the shutter to open
        # begin motor movement
        no_wait = True
        for obj in devices:
            if hasattr(obj, 'trigger'):
                no_wait = False
                yield from trigger(obj, group=grp)
        if not no_wait: # wait for signals to return (lead_detector may not have finished yet, but that's ok)
            yield from wait(group=grp)
        yield from create('primary') # creation time of primary step is not when the detector returns, but closer to when the shutter closes


        ret = {}  # collect and return readings to give plan access to them
        for obj in devices: # read all signals
            reading = (yield from read(obj))
            if reading is not None:
                ret.update(reading)
        yield from bps.wait(group='measure') # wait for the detector to finish
        reading = (yield from read(lead_detector)) # read the lead detector
        if reading is not None:
            ret.update(reading)
        yield from save()
        return ret
    from .preprocessors import rewindable_wrapper
    return (yield from rewindable_wrapper(inner_trigger_and_read(),
                                          rewindable))



def take_exposure_corrected_reading(detectors=None, take_reading=trigger_and_read_with_shutter, lead_detector=None, shutter=None, check_exposure=False):
    # this is a replacement of trigger and read, that continues to trigger increasing or decreasing the
    # explsure time until limits are reached or neither under exposing or over exposing
    if detectors == None:
        detectors = []
    yield from take_reading(list(detectors), lead_detector=lead_detector)
    if(check_exposure):
        under_exposed = False
        over_exposed = False
        for det in detectors:
            if not hasattr(det,'under_exposed'):
                continue
            if det.under_exposed.get():
                under_exposed = True
            if not hasattr(det,'saturated'):
                continue
            if det.saturated.get():
                over_exposed = True
        while(under_exposed or over_exposed):
            yield Msg("checkpoint")
            old_time = Shutter_open_time.get()
            if(under_exposed and not over_exposed):
                if old_time<200:
                    new_time = old_time * 10
                elif old_time<1000:
                    new_time = old_time * 4
                elif old_time<5000:
                    new_time = old_time * 2
                else:
                    print('underexposed, but maximum exposure time reached')
                    break
                print(f'underexposed at {old_time}ms, trying again at {new_time}ms')
            elif(over_exposed and not under_exposed):
                new_time = round(old_time / 10)
                if new_time < 2:
                    print('over exposed, but minimum exposure time reached')
                    break
                print(f'over exposed at {old_time}ms, trying again at {new_time}ms')
            else:
                print(f'contradictory saturated and under exposed, no change in exposure will be made')
                break
            Shutter_open_time.set(round(new_time)).wait()
            if hasattr(lead_detector,'cam'):
                    lead_detector.cam.acquire_time.set(new_time/1000).wait()
            for det in detectors:
                if hasattr(det,'exposure_time'):
                    det.exposure_time.set(new_time/1000).wait()
            yield from take_reading(list(detectors), lead_detector=lead_detector,shutter=shutter)
            under_exposed = False
            over_exposed = False
            for det in detectors:
                if not hasattr(det,'under_exposed'):
                    continue
                if det.under_exposed.get():
                    under_exposed = True
                if not hasattr(det,'saturated'):
                    continue
                if det.saturated.get():
                    over_exposed = True


def one_nd_sticky_exp_step(detectors, step, pos_cache, take_reading=trigger_and_read_with_shutter,remember=None):
    """
    Inner loop of an N-dimensional step scan

    This is the default function for ``per_step`` param`` in ND plans.

    Parameters
    ----------
    detectors : iterable
        devices to read
    step : dict
        mapping motors to positions in this step
    pos_cache : dict
        mapping motors to their last-set positions
    take_reading : plan, optional
        function to do the actual acquisition ::

           def take_reading(dets, name='primary'):
                yield from ...

        Callable[List[OphydObj], Optional[str]] -> Generator[Msg], optional

        Defaults to `trigger_and_read`
    remember :  pass a dict to remember the last exposure correction
    """
    yield Msg("checkpoint")
    if remember == None:
        remember = {}
    motors = step.keys()
    yield from move_per_step(step, pos_cache)
    input_time = Shutter_open_time.get()
    if 'last_correction' in remember:
        new_time = input_time
        if remember['last_correction'] != 1 and 0.0005 < remember['last_correction'] < 50000:
            new_time = round(input_time * remember['last_correction'])
        if(2 < new_time < 10000):
            print(f"last exposure correction was {remember['last_correction']}, so applying that to {input_time}ms gives an exposure time of {new_time}ms")
            yield from bps.mov(Shutter_open_time,new_time)
            for detector in detectors:
                if hasattr(detector,'cam'):
                    yield from bps.mv(detector.cam.acquire_time, new_time/1000)

    yield from take_reading(list(detectors) + list(motors))
    output_time = Shutter_open_time.get()
    remember['last_correction'] = float(output_time) / float(input_time)




def cdsaxs_scan(det=waxs_det,angle_mot = sam_Th,shutter = Shutter_control,start_angle=50,end_angle=85,exp_time=9,md=None):
    _md = deepcopy(dict(RE.md))
    if md == None:
        md = {}
    _md.update(md)
    
    
    _md.update({'plan_info':f'CDSAXS_{start_angle/2}to{end_angle/2}_{exp_time}sec'})
    yield from bps.mv(Shutter_open_time,exp_time*1000)
    yield from bps.mv(det.cam.acquire_time, exp_time)
    yield from bps.mv(angle_mot,start_angle)
    old_velo = angle_mot.velocity.get()
    if np.abs(end_angle - start_angle)/old_velo < exp_time:
        yield from bps.mv(angle_mot.velocity,np.abs((end_angle - start_angle)/exp_time))
    @bpp.run_decorator(md=_md)
    @bpp.stage_decorator([det])
    def _inner_scan():
        yield from bps.abs_set(shutter, 1, just_wait=True, group='shutter') # start waiting for the shutter to open
        yield from bps.trigger(det, group='measure') # trigger the detector, which will eventually open the shutter
        yield from bps.wait(group='shutter') # wait for the shutter to open
        yield from bps.abs_set(angle_mot,end_angle,group='measure') # begin motor movement
        yield from bps.wait(group='measure') # wait for the detector to finish
        yield from create('primary')
        reading = (yield from read(det))
        yield from save()
        return reading
    def _cleanup():
        yield from bps.mv(angle_mot.velocity,old_velo)
    return (yield from bpp.contingency_wrapper(_inner_scan(),final_plan=_cleanup))

