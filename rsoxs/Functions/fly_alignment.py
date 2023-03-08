from ophyd.sim import NullStatus

from bluesky.preprocessors import monitor_during_wrapper,  finalize_wrapper
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import pandas as pd
import numpy as np

from sst_hw.diode import Shutter_control, Shutter_enable
from ..startup import db, bec, sd
from ..HW.energy import en


def fly_max(
    detectors,
    signals,
    motor,
    start,
    stop,
    velocity,
    step_factor=3.0,
    open_shutter=True,
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
    velocity : float
        speed to set motor to during run.
    step_factor : float, optional
        used in calculating new range after each pass
        unused for now
        note: step_factor > 1.0, default = 3
    snake : bool, optional
        if False (default), always scan from start to stop
    md : dict, optional
        metadata

    """
    signal = signals[0]
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
            "signals" : list(map(repr, signals)),
            "start": start,
            "stop": stop,
            "velocity": velocity,
            "step_factor": step_factor,
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
    bec.enable_plots()
    old_monitor_list = sd.monitors
    sd.monitors.clear()
    old_baseline = sd.baseline
    sd.baseline.clear()
    yield from bps.sleep(0.2)
    yield from ramp_motor_scan(start,stop,motor, detectors, velocity=velocity, open_shutter=open_shutter)
    max_signal, max_motor = find_optimum_motor_pos(db, -1, motor_name=motor.name, signal_name=signals[0])
    yield from bps.mv(motor, max_motor)
    peaklist.append([max_motor, max_signal])
    for detector in detectors:
        detector.kind = 'normal'
    bec.disable_plots
    sd.monitors =old_monitor_list
    sd.baseline = old_baseline
    return max_motor


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
    if open_shutter:
        yield from bps.mv(Shutter_enable, 0)
        yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(ramp_plan,_cleanup())


def ramp_plan_with_multiple_monitors(go_plan, monitor_list, inner_plan_func,
                                     take_pre_data=True, timeout=None, period=None, md=None):
    mon1 = monitor_list[0]
    mon_rest = monitor_list[1:]
    #TODO check if the monitors are already in sd.monitors, if so ignore them
    #make mon1 a none then?
    ramp_plan = bp.ramp_plan(go_plan, mon1, inner_plan_func,
                                take_pre_data=take_pre_data, timeout=timeout, period=period, md=md)

    yield from monitor_during_wrapper(ramp_plan, mon_rest)


def process_monitor_scan(db, uid):
    hdr = db[uid]
    df = {}
    for stream_name in hdr.stream_names:
        t = hdr.table(stream_name=stream_name)
        this_time = t['time'].astype(dtype=int).values * 1e-9
        if not 'time' in df.keys():
            df['time'] = this_time

        column_name = stream_name.replace('_monitor', '')
        this_data = t[column_name].values
        df[column_name] = np.interp(df['time'], this_time, this_data)

    return pd.DataFrame(df)


def find_optimum_motor_pos(db, uid, motor_name='hhm_pitch', signal_name='apb_ch1'):
    df = process_monitor_scan(db, uid)
    idx = df[signal_name].idxmax()
    
    motor_value = df[motor_name][idx]
    signal_value = df[signal_name][idx]
    return signal_value, motor_value

