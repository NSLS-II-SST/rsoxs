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
    Mono_Scan_Speed_ev,
    Mono_Scan_Start,
    Mono_Scan_Start_ev,
    Mono_Scan_Stop,
    Mono_Scan_Stop_ev,
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
from ..HW.signals import DiodeRange,Beamstop_WAXS,Beamstop_SAXS,Izero_Mesh,Sample_TEY, Beamstop_SAXS_int,Beamstop_WAXS_int, Izero_Mesh_int,Sample_TEY_int, ring_current
from ..HW.lakeshore import tem_tempstage
from ..Functions.alignment import rotate_now
from ..Functions.common_procedures import set_exposure
from ..Functions.fly_alignment import find_optimum_motor_pos, bec, db, return_NullStatus_decorator

from .flystream_wrapper import flystream_during_wrapper
from sst_hw.diode import (
    Shutter_open_time,
    Shutter_control,
    Shutter_enable,
    Shutter_trigger,
    shutter_open_set
)
from sst_funcs.printing import run_report


from ..startup import rsoxs_config

from bluesky.utils import ensure_generator, short_uid as _short_uid, single_gen
from bluesky.preprocessors import plan_mutator



run_report(__file__)



import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.utils import short_uid

def per_step_factory(fake_flyer):
    group = None
    target = None

    def per_step(detectors, step, pos_cache, take_reading=None):
        nonlocal group, target
        fly_target = step.pop(fake_flyer)
        if target != fly_target:
            if group is not None:
                yield from bps.wait(group=group)
            group = short_uid(label='fake_flyer')
            yield from bps.abs_set(fake_flyer, target)
        yield from bps.one_nd_step(detectors, step, pos_cache, take_reading=take_reading)

    def final():
        if group is not None:
            yield from bps.wait(group=group)

    return per_step, final


def my_scan(...):

    per_step, final = per_step_factory(lakeshore)

    yield from bp.scan_nd(..., per_step=per_step)
    yield from final()





SLEEP_FOR_SHUTTER = 1


def cleanup():
    # make sure the shutter is closed, and the scanlock if off after a scan, even if it errors out
    yield from bps.mv(en.scanlock, 0)
    yield from bps.mv(Shutter_control, 0)
    

@finalize_decorator(rsoxs_config.write_plan)
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
        dets = [Beamstop_SAXS_int,Beamstop_WAXS_int, Izero_Mesh_int,Sample_TEY_int]
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
    if isinstance(polarizations,list):
        sigcycler = cycler(en.polarization, polarizations)*sigcycler # cycler for polarization changes (multiplied means we do everything above for each polarization)

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



@finalize_decorator(rsoxs_config.write_plan)
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
    if len(newdets) < 1:
        valid = False
        validation += "No detectors are given\n"
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
    sigcycler += cycler(Shutter_open_time, shutter_times) # cycler for changing the shutter opening time
    if isinstance(polarizations,list):
        sigcycler = cycler(en.polarization, polarizations)*sigcycler # cycler for polarization changes (multiplied means we do everything above for each polarization)

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
    if check_exposure:
        yield from finalize_wrapper(flystream_during_wrapper(
            bp.scan_nd(newdets + goodsignals, 
                    sigcycler, 
                    md=md,
                    per_step=partial(one_nd_sticky_exp_step,remember=exps,take_reading=partial(take_exposure_corrected_reading,check_exposure=check_exposure))
                    ),
                    [Beamstop_WAXS_int, Izero_Mesh_int]),
                    #[Beamstop_WAXS_int, Beamstop_SAXS_int, Izero_Mesh_int, Sample_TEY_int]),
            cleanup()
        )
    else:
        yield from finalize_wrapper(flystream_during_wrapper(
            bp.scan_nd(newdets + goodsignals, 
                    sigcycler, 
                    md=md),
                    #[Beamstop_WAXS_int, Beamstop_SAXS_int, Izero_Mesh_int, Sample_TEY_int]),
                    [Beamstop_WAXS_int, Izero_Mesh_int]),
            cleanup()
        )
    for det in newdets:
        det.number_exposures = old_n_exp[det.name]


@finalize_decorator(rsoxs_config.write_plan)
def NEXAFS_old_fly_scan_core(
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
    signals = [Beamstop_WAXS, Beamstop_SAXS, Izero_Mesh, Sample_TEY]
    if np.isnan(pol):
        pol = en.polarization.setpoint.get()
    (en_start, en_stop, en_speed) = scan_params[0]
    yield from bps.mv(en.scanlock, 0) # unlock parameters
    print("Moving to initial position before scan start")
    yield from bps.mv(en.energy, en_start+10, en.polarization, pol )  # move to the initial energy
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
    uid = (yield from finalize_wrapper(fly_scan_eliot(scan_params,sigs=signals, md=md, locked=locked, polarization=pol),cleanup()))

    return uid



@finalize_decorator(rsoxs_config.write_plan)
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
    signals = [Beamstop_WAXS, Beamstop_SAXS, Izero_Mesh, Sample_TEY]
    if np.isnan(pol):
        pol = en.polarization.setpoint.get()
    (en_start, en_stop, en_speed) = scan_params[0]
    yield from bps.mv(en.scanlock, 0) # unlock parameters
    print("Moving to initial position before scan start")
    yield from bps.mv(en.energy, en_start+10, en.polarization, pol )  # move to the initial energy
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
    uid = (yield from finalize_wrapper(flyer_scan_energy(list(chain.from_iterable(scan_params)),sigs=signals, md=md, locked=locked, polarization=pol),cleanup()))

    return uid


def fly_scan_eliot(scan_params, sigs=[], polarization=0, locked = 1, *, md={}):
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
    _md = {
        "detectors": [mono_en.name],
        "motors": [mono_en.name],
        "plan_name": "fly_scan_eliot",
        "hints": {},
    }
    _md.update(md or {})
    devices = [mono_en]+sigs

    def check_end(start,end,current):
        if start>end:
            return end - current < 0
        else:
            return current - end < 0

    @bpp.monitor_during_decorator([mono_en])
    @bpp.stage_decorator(list(devices))
    @bpp.run_decorator(md=_md)
    def inner_scan_eliot():
        # start the scan parameters to the monoscan PVs
        yield Msg("checkpoint")
        if np.isnan(polarization):
            pol = en.polarization.setpoint.get()
        else:
            yield from set_polarization(polarization)
            pol = polarization

        for (start_en, end_en, speed_en) in scan_params:
            step = 0
            print(f"starting fly from {start_en} to {end_en} at {speed_en} eV/second")
            yield Msg("checkpoint")
            print("Preparing mono for fly")
            yield from bps.mv(
                Mono_Scan_Start_ev, start_en,
                Mono_Scan_Stop_ev,end_en,
                Mono_Scan_Speed_ev,speed_en,
            )
            gap_offset = get_gap_offset(start_en,end_en,speed_en)
            yield from bps.mv(en.offset_gap,gap_offset)
            # move to the initial position
            #if step > 0:
            #    yield from wait(group="EPU")
            yield from bps.abs_set(mono_en, start_en, group="mono")
            print("moving to starting position")
            yield from wait(group="mono")
            print("Mono in start position")
            yield from bps.mv(epu_gap, en.gap(start_en, pol, locked))
            yield from bps.abs_set(epu_gap, en.gap(start_en, pol, locked), group="EPU")
            yield from wait(group="EPU")
            print("EPU in start position")
            if step == 0:
                monopos = mono_en.readback.get()
                yield from bps.abs_set(
                    epu_gap,
                    en.gap(monopos, pol, locked),
                    wait=False,
                    group="EPU",
                )
                yield from wait(group="EPU")
            # start the mono scan
            print("starting the fly")
            yield from bps.sleep(.5)
            yield from bps.mv(Mono_Scan_Start, 1)
            monopos = mono_en.readback.get()
            
            while check_end(start_en,end_en,monopos) :
                monopos = mono_en.readback.get()
                yield from bps.abs_set(
                    epu_gap,
                    en.gap(monopos, pol, locked),
                    wait=False,
                    group="EPU",
                )
                yield from create("primary")
                for obj in devices:
                    yield from read(obj)
                yield from save()
                yield from wait(group="EPU")
            print(f"Mono reached {monopos} which appears to be near {end_en}")
            step += 1

    return (yield from inner_scan_eliot())



def flyer_scan_energy(scan_params, sigs=[], md={},locked=True,polarization=0):
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
    detectors = [Beamstop_WAXS_int, Beamstop_SAXS_int, Izero_Mesh_int, Sample_TEY_int]


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

    return (yield from flystream_during_wrapper(inner_flyscan(), flyers))



def fly_scan_dets(scan_params,dets, polarization=0, locked = 1, *, md={}):
    """
    Specific scan for SST-1 monochromator fly scan, while catching up with the undulator
    this specific plan in in progress and is not operational yet

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
    _md = {
        "detectors": [mono_en.name,Shutter_control.name],
        "motors": [mono_en.name,Shutter_control.name],
        "plan_name": "fly_scan_RSoXS",
        "hints": {},
    }
    _md.update(md or {})

    devices = [mono_en]
    @bpp.monitor_during_decorator([mono_en]) # add shutter
    #@bpp.stage_decorator(list(devices)) # staging the detector # do explicitely
    @bpp.run_decorator(md=_md)
    def inner_scan_eliot():
        # start the scan parameters to the monoscan PVs
        for det in dets:
            yield from bps.stage(det)
            yield from abs_set(det.cam.image_mode, 2) # set continuous mode
        yield Msg("checkpoint")
        if np.isnan(polarization):
            pol = en.polarization.setpoint.get()
        else:
            yield from set_polarization(polarization)
            pol = polarization
        step = 0
        for (start_en, end_en, speed_en) in scan_params:
            print(f"starting fly from {start_en} to {end_en} at {speed_en} eV/second")
            yield Msg("checkpoint")
            print("Preparing mono for fly")
            yield from bps.mv(
                Mono_Scan_Start_ev,
                start_en,
                Mono_Scan_Stop_ev,
                end_en,
                Mono_Scan_Speed_ev,
                speed_en,
            )
            # move to the initial position
            if step > 0:
                yield from wait(group="EPU")
            yield from bps.abs_set(mono_en, start_en, group="EPU")
            print("moving to starting position")
            yield from wait(group="EPU")
            print("Mono in start position")
            yield from bps.mv(epu_gap, en.gap(start_en, pol, locked))
            print("EPU in start position")
            if step == 0:
                monopos = mono_en.readback.get()
                yield from bps.abs_set(
                    epu_gap,
                    en.gap(monopos, pol, locked),
                    wait=False,
                    group="EPU",
                )
                yield from wait(group="EPU")
            print("Starting detector stream")
            # start the detectors collecting in continuous mode
            for det in dets:
                yield from trigger(det, group="det_trigger")
            # start the mono scan
            print("starting the fly")
            yield from bps.mv(Mono_Scan_Start, 1)
            monopos = mono_en.readback.get()
            while np.abs(monopos - end_en) > 0.1:
                yield from wait(group="EPU")
                monopos = mono_en.readback.get()
                yield from bps.abs_set(
                    epu_gap,
                    en.gap(monopos, pol, locked),
                    wait=False,
                    group="EPU",
                )
                yield from create("primary")
                for obj in devices:
                    yield from read(obj)
                yield from save()
            print(f"Mono reached {monopos} which appears to be near {end_en}")
            print("Stopping Detector stream")
            for det in dets:
                
                yield from abs_set(det.cam.acquire, 0)
            for det in dets:
                yield from read(det)
                yield from save(det)

            step += 1
        for det in dets:
            yield from unstage(det)
            yield from abs_set(det.cam.image_mode, 1)

    return (yield from inner_scan_eliot())

# example code from Tom
# def my_custom(motors, dectectors, positions, my, stuff):
#     ...

# yield from scan_nd(..., per_step=partial(my_custom, my='a', stuff='b'))
# 
# 
# 
# reading = yield from trigger_and_read(dets)
# while try_again(reading):
#     yield from adjust_eposure()
#     reading = yield from trigger_and_read(dets)



def take_exposure_corrected_reading(detectors=None, check_exposure=False):
    if detectors == None:
        detectors = []
    yield from trigger_and_read(list(detectors))
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
            for det in detectors:
                if hasattr(det,'cam'):
                    det.cam.acquire_time.set(new_time/1000).wait()
            yield from trigger_and_read(list(detectors))
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


def one_nd_sticky_exp_step(detectors, step, pos_cache, take_reading=trigger_and_read,remember=None):
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
