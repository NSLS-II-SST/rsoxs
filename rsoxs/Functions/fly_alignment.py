from ophyd.sim import NullStatus

from bluesky.preprocessors import monitor_during_wrapper,  finalize_wrapper
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import pandas as pd
import numpy as np

from sst_hw.diode import Shutter_control, Shutter_enable
from ..startup import db, bec, sd
from ..HW.energy import en

from ..HW.signals import Beamstop_SAXS
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
from .alignment import load_configuration

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
    bec.enable_plots()
    max_val = max((start,stop))
    min_val = min((start,stop))
    direction = 1

    for velocity in velocities:
        range = np.abs(start-stop)
        print(f'starting scan from {start} to {stop} at {velocity}')
        yield from ramp_motor_scan(start,stop,motor, detectors, velocity=velocity, open_shutter=open_shutter)
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
        yield from bps.mv(motor, signal_dict[signals[0]][motor_signal])

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


def ramp_motor_scan(start_pos, stop_pos,motor=None, detector_channels=None,sleep = 0.2,velocity = None,open_shutter=False):
    yield from bps.mv(motor, start_pos)
    yield from bps.sleep(sleep)
    if velocity is not None:
        old_motor_velocity = motor.velocity.get()
        yield from bps.mv(motor.velocity, velocity)
    @return_NullStatus_decorator
    def _move_plan():
        yield from bps.mv(motor, stop_pos)
        yield from bps.sleep(sleep)
    ramp_plan = ramp_plan_with_multiple_monitors(_move_plan(), [motor] + detector_channels, bps.null)
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
    hdr = db[uid]
    df = {}
    for stream_name in hdr.stream_names:
        if 'monitor' not in stream_name:
            print(stream_name)
            continue
        t = hdr.table(stream_name=stream_name)
        this_time = t['time'].astype(dtype=int).values * 1e-9 + time_offsets.get(stream_name,0.0)
        if not 'time' in df.keys():
            df['time'] = this_time

        column_name = stream_name.replace('_monitor', '')
        this_data = t[column_name].values
        df[column_name] = np.interp(df['time'], this_time, this_data)

    return pd.DataFrame(df)


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




def fly_find_fiducials(f2=[7.5, 3.5, -2.5, 1.1]):
    thoffset = 0
    angles = [-90 + thoffset, 0 + thoffset, 90 + thoffset, 180 + thoffset]
    xrange = 3.5
    startxss = [f2, [4.2, 3.5, 1, 1.1]]
    yield from bps.mv(Shutter_enable, 0)
    yield from bps.mv(Shutter_control, 0)
    yield from load_configuration("SAXSNEXAFS")
    Beamstop_SAXS.kind = "hinted"
    bec.enable_plots()
    startys = [3, -187.0]  # af2 first because it is a safer location
    maxlocs = []
    for startxs, starty in zip(startxss, startys):
        yield from bps.mv(sam_Y, starty, sam_X, startxs[1], sam_Th, 0, sam_Z, 0)
        peaklist = []
        yield from fly_max([Beamstop_SAXS],
                           ['SAXS Beamstop'],
                           sam_Y,
                           starty-1,
                           starty+1,
                           velocities=[.2],
                           open_shutter=True,
                           peaklist=peaklist)
        maxlocs.append(peaklist[-1]['SAXS Beamstop']["RSoXS Sample Up-Down"])
        yield from bps.mv(sam_Y, peaklist[-1]['SAXS Beamstop']["RSoXS Sample Up-Down"])
        for startx, angle in zip(startxs, angles):
            yield from bps.mv(sam_X, startx, sam_Th, angle)
            yield from bps.mv(Shutter_control, 1)
            peaklist = []
            yield from fly_max([Beamstop_SAXS],
                                ['SAXS Beamstop'],
                                sam_X,
                                startx - 0.5 * xrange,
                                startx + 0.5 * xrange,
                                velocities=[.2],
                                open_shutter=True,
                                peaklist=peaklist)
            maxlocs.append(peaklist[-1]['SAXS Beamstop']["RSoXS Sample Outboard-Inboard"])
    print(maxlocs)  # [af2y,af2xm90,af2x0,af2x90,af2x180,af1y,af1xm90,af1x0,af1x90,af1x180]
    bec.disable_plots()
