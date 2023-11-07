from ophyd.sim import NullStatus

from bluesky.preprocessors import monitor_during_wrapper,  finalize_wrapper, finalize_decorator

from bluesky.protocols import Readable, Flyable
import bluesky.utils as utils
from bluesky.utils import Msg, short_uid as _short_uid, single_gen, ensure_generator
from bluesky.preprocessors import plan_mutator
from bluesky.plan_stubs import trigger_and_read, move_per_step, stage, unstage
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky import preprocessors as bpp
import pandas as pd
import numpy as np
from copy import deepcopy

from sst_hw.diode import Shutter_control, Shutter_enable
from ..startup import RE, db, bec, db0, sd, rsoxs_config
from ..HW.energy import en

from ..HW.signals import Beamstop_SAXS, Beamstop_WAXS, Beamstop_WAXS_int
from ..HW.motors import (
    sam_X,
    sam_Y,
    sam_Th,
    sam_Z,
    Shutter_Y,
    Izero_Y,
    Det_S,
    Det_W,
    BeamStopW,
    BeamStopS)
from .alignment import load_configuration, rsoxs_config,correct_bar

def flystream_during_wrapper(plan, flyers, stream=True):
    """
    Kickoff and collect "flyer" (asynchronously collect) objects during runs.
    This is a preprocessor that insert messages immediately after a run is
    opened and before it is closed.
    Parameters
    ----------
    plan : iterable or iterator
        a generator, list, or similar containing `Msg` objects
    flyers : collection
        objects that support the flyer interface
    Yields
    ------
    msg : Msg
        messages from plan with 'kickoff', 'wait' and 'collect' messages
        inserted
    See Also
    --------
    :func:`bluesky.plans.fly`
    """
    grp1 = _short_uid('flyers-kickoff')
    grp2 = _short_uid('flyers-complete')
    kickoff_msgs = [Msg('kickoff', flyer, group=grp1) for flyer in flyers]
    complete_msgs = [Msg('complete', flyer, group=grp2) for flyer in flyers]
    collect_msgs = [Msg('collect', flyer, stream=stream) for flyer in flyers]
    if flyers:
        # If there are any flyers, insert a 'wait' Msg after kickoff, complete
        kickoff_msgs += [Msg('wait', None, group=grp1)]
        complete_msgs += [Msg('wait', None, group=grp2)]

    def insert_after_open(msg):
        if msg.command == 'open_run':
            def new_gen():
                yield from ensure_generator(kickoff_msgs)
            return single_gen(msg), new_gen()
        else:
            return None, None

    def insert_before_close(msg):
        if msg.command == 'close_run':
            def new_gen():
                yield from ensure_generator(complete_msgs)
                yield from ensure_generator(collect_msgs)
                yield msg
            return new_gen(), None
        else:
            return None, None

    # Apply nested mutations.
    plan1 = plan_mutator(plan, insert_after_open)
    plan2 = plan_mutator(plan1, insert_before_close)
    return (yield from plan2)



time_offset_defaults = {'en_monoen_readback_monitor':-0.0}

def fly_max(
    detectors,
    signals,
    motor,
    start,
    stop,
    velocities,
    range_ratio=10,
    open_shutter=True,
    snake=False,
    peaklist=[],
    time_offsets = time_offset_defaults,
    end_on_max = True,
    md=None,
    motor_signal=None,
    rb_offset = 0,
    **kwargs,
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
    signals : list of strings
        detector fields whose output is to maximize
        (the first will be maximized, but secondardy maxes will be recorded during the scans for the first - 
        if the maxima are not in the same range this will not be useful)
    motor : object
        any 'settable' object (motor, temp controller, etc.)
    start : float
        start of range
    stop : float
        end of range, note: start < stop
    velocities : list of floats
        list of speeds to set motor to during run.
    range_ratio : float
        how much less range for subsequent scans (default 10)
    snake : bool, optional
        if False (default), always scan from start to stop
    md : dict, optional
        metadata
    time_offsets : dict, optional
        stream names time offsets dictionary in seconds

    """

    _md = {
        "detectors": [det.name for det in detectors],
        "motors": [motor.name],
        "plan_args": {
            "detectors": list(map(repr, detectors)),
            "motor": repr(motor),
            "signals" : list(signals),
            "start": start,
            "stop": stop,
            "velocities": velocities,
            "range_ratio": range_ratio,
            "snake": snake,
        },
        "plan_name": "fly_max",
        "hints": {},
    }
    _md.update(md or {})
    try:
        dimensions = [(motor.hints["fields"], "primary")]
    except (AttributeError, KeyError):
        pass
    else:
        _md["hints"].setdefault("dimensions", dimensions)
    for detector in detectors:
        detector.kind='hinted'
    if motor_signal == None:
        motor_signal = motor.name
    motor.kind='hinted'
    #bec.enable_plots()
    max_val = max((start,stop))
    min_val = min((start,stop))
    direction = 1

    for velocity in velocities:
        range = np.abs(start-stop)
        start -= rb_offset
        stop -= rb_offset
        print(f'starting scan from {start} to {stop} at {velocity}')
        yield from ramp_motor_scan(start,stop,motor, detectors, velocity=velocity, open_shutter=open_shutter,md=_md)
        yield from bps.sleep(5)
        signal_dict = find_optimum_motor_pos(db, -1, motor_name=motor_signal, signal_names=signals, time_offsets = time_offsets)
        print(f'maximum signal of {signals[0]} found at {signal_dict[signals[0]][motor_signal]}')
        low_side = max((min_val,signal_dict[signals[0]][motor_signal] - (range/(2*range_ratio))))
        high_side = min((max_val,signal_dict[signals[0]][motor_signal] + (range/(2*range_ratio))))
        if snake:
            direction *=-1
        if(direction>0):
            start = low_side
            stop = high_side
        else:
            start = high_side
            stop = low_side
    if end_on_max:
        yield from bps.mv(motor, signal_dict[signals[0]][motor_signal]- rb_offset)

    peaklist.append(signal_dict)
    for detector in detectors:
        detector.kind = 'normal'
    motor.kind='normal'
    bec.disable_plots
    return signal_dict


def return_NullStatus_decorator(plan):
    def wrapper(*args, **kwargs):
        yield from plan(*args, **kwargs)
        return NullStatus()
    return wrapper


def ramp_motor_scan(start_pos, stop_pos,motor=None, detector_channels=None,sleep = 0.2,velocity = None,open_shutter=False,md=None):
    yield from bps.mv(motor, start_pos)
    yield from bps.sleep(sleep)
    if velocity is not None:
        old_motor_velocity = motor.velocity.get()
        yield from bps.mv(motor.velocity, velocity)
    @return_NullStatus_decorator
    def _move_plan():
        yield from bps.mv(motor, stop_pos)
        yield from bps.sleep(sleep)
    ramp_plan = fly_plan(motor,start_pos, stop_pos,flyer_list=detector_channels,md=md)
    def _cleanup():
        yield from bps.mv(Shutter_control, 0)
        if velocity is not None:
            yield from bps.mv(motor.velocity, old_motor_velocity)
            yield from bps.sleep(sleep)
    if open_shutter:
        yield from bps.mv(Shutter_enable, 0)
        yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(ramp_plan,_cleanup())


def ramp_plan_with_multiple_monitors(go_plan, monitor_list, inner_plan_func,
                                     take_pre_data=True, timeout=None, period=None, md=None):
    final_monitor_list = []
    num_monitors = 0
    for monitor in monitor_list:
        if monitor not in sd.monitors:
            final_monitor_list.append(monitor)
            num_monitors+=1
        else:
            final_monitor_list.append(None)
            
    
    mon1 = final_monitor_list[0]
    mon_rest = final_monitor_list[1:]
    
    ramp_plan = bp.ramp_plan(go_plan, mon1, inner_plan_func,
                                take_pre_data=take_pre_data, timeout=timeout, period=period, md=md)
    if (num_monitors>0 and type(mon1) == type(None)) or (num_monitors>1 and type(mon1) != type(None)):
        yield from monitor_during_wrapper(ramp_plan, mon_rest)
    else:
        yield from ramp_plan


def process_monitor_scan(db, uid, time_offsets=None):
    if time_offsets == None:
        time_offsets = {}
    hdr = db.v2[uid]
    df = pd.DataFrame()
    for stream_name in hdr:
        if 'monitor' not in stream_name:
            print(stream_name)
            continue
        column_name = stream_name.replace('_monitor', '')
        newdf = pd.DataFrame({'time':hdr[stream_name]['timestamps'][column_name].read(),column_name:hdr[stream_name]['data'][column_name].read()}).set_index('time')
        newdf.index += time_offsets.get(stream_name,0.0)
        df = pd.concat((df, newdf))
    #df = df[~df.index.duplicated(keep='first')].sort_index().interpolate(method='index').ffill().bfill()

    df = df.groupby('time').mean().sort_index().interpolate(method='index').ffill().bfill()

    return df


def fly_plan(motor, *scan_params, exposure_time=0.5, flyer_list=[],md=None):
    _md = {
        "detectors": [detector.name for detector in flyer_list],
        "motors": [motor.name],
        "plan_name": "fly_plan",
        "hints": {},
    }
    _md.update(md or {})

    flyers = [d for d in flyer_list + [motor] if isinstance(d, Flyable)]
    readers = [d for d in flyer_list + [motor] if isinstance(d, Readable)]
    for reader in readers:
        if hasattr(reader,'set_exposure'):
            reader.set_exposure(exposure_time)

    motor.preflight(*scan_params)

    @bpp.stage_decorator(readers)
    @bpp.run_decorator(md=_md)
    def inner_flyscan():
        status = motor.fly()

        while not status.done:
            yield from trigger_and_read(readers)

        motor.land()

    return (yield from flystream_during_wrapper(inner_flyscan(), flyers))


def find_optimum_motor_pos(db, uid, motor_name='RSoXS Sample Up-Down', signal_names=['RSoXS Au Mesh Current','SAXS Beamstop'], time_offsets = None):
    df = process_monitor_scan(db, uid, time_offsets)
    max_signal_dict = {}
    for monitor in signal_names:
        idx = df[monitor].idxmax()
        max_signal_dict[monitor] = {}
        max_signal_dict[monitor]['time'] =  idx 
        max_signal_dict[monitor][motor_name] = df[motor_name][idx]
        max_signal_dict[monitor][monitor] = df[monitor][idx]
    return max_signal_dict




@finalize_decorator(rsoxs_config.write_plan)
#RE(fly_find_fiducials(f2=[3.5,-1,-2.4,1.5],f1=[2.0,-0.9,-1.5,0.8],y1=-187.5,y2=2)) # new encoders
#def fly_find_fiducials(f2=[7.5,5,-2.5,0],f1=[4.6, 4, 1, 1.1],y2=2.5,y1=-188):
def fly_find_fiducials(f2=[3.5,-1,-2.4,1.5],f1=[2.0,-0.9,-1.5,0.8],y1=-187.5,y2=2):
    thoffset = 0
    angles = [-90 + thoffset, 0 + thoffset, 90 + thoffset, 180 + thoffset]
    xrange = 3.5
    startxss = [f2, f1]
    yield from bps.mv(Shutter_enable, 0)
    yield from bps.mv(Shutter_control, 0)
    yield from load_configuration("WAXSNEXAFS")
    Beamstop_WAXS_int.kind = "hinted"
    bec.enable_plots()
    startys = [y2, y1]  # af2 first because it is a safer location
    maxlocs = []
    for startxs, starty in zip(startxss, startys):
        yield from bps.mv(sam_Y, starty, sam_X, startxs[1], sam_Th, 0, sam_Z, 0)
        peaklist = []
        yield from fly_max([Beamstop_WAXS_int],
                           ['WAXS Beamstop'],
                           sam_Y,
                           starty-1,
                           starty+1,
                           velocities=[.2],
                           open_shutter=True,
                           peaklist=peaklist)
        maxlocs.append(peaklist[-1]['WAXS Beamstop']["RSoXS Sample Up-Down"])
        yield from bps.mv(sam_Y, peaklist[-1]['WAXS Beamstop']["RSoXS Sample Up-Down"])
        for startx, angle in zip(startxs, angles):
            yield from bps.mv(sam_X, startx, sam_Th, angle)
            yield from bps.mv(Shutter_control, 1)
            peaklist = []
            yield from fly_max([Beamstop_WAXS_int],
                                ['WAXS Beamstop'],
                                sam_X,
                                startx - 0.5 * xrange,
                                startx + 0.5 * xrange,
                                velocities=[.2],
                                open_shutter=True,
                                peaklist=peaklist)
            maxlocs.append(peaklist[-1]['WAXS Beamstop']["RSoXS Sample Outboard-Inboard"])
    print(maxlocs)  # [af2y,af2xm90,af2x0,af2x90,af2x180,af1y,af1xm90,af1x0,af1x90,af1x180]
    accept = input(f"Do you want to apply this correction (y,n)?")
    if accept in ['y','Y','yes']:
        back = False
        rsoxs_config.read()
        for samp in rsoxs_config['bar']:
            if samp['front'] ==False:
                back = True
        correct_bar(maxlocs,include_back=back)
    bec.disable_plots()
