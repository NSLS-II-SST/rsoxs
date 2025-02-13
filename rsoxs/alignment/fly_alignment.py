from nbs_bl.plans.maximizers import fly_max
from bluesky.preprocessors import finalize_wrapper
import bluesky.plan_stubs as bps
from nbs_bl.hw import Shutter_control, Shutter_enable
import numpy as np


def rsoxs_fly_max(
    detectors,
    motor,
    start,
    stop,
    velocities,
    max_channel=None,
    range_ratio=10,
    open_shutter=True,
    snake=False,
    end_on_max=True,
    md=None,
    rb_offset=0,
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
    motor : object
        any 'settable' object (motor, temp controller, etc.)
    start : float
        start of range
    stop : float
        end of range, note: start < stop
    velocities : list of floats
        list of speeds to set motor to during run.
    max_channel : list of strings
        detector fields whose output is to maximize. If not given, the first detector is used.
        (the first will be maximized, but secondardy maxes will be recorded during the scans for the first -
        if the maxima are not in the same range this will not be useful)
    range_ratio : float
        how much less range for subsequent scans (default 10)
    snake : bool, optional
        if False (default), always scan from start to stop
    md : dict, optional
        metadata
    time_offsets : dict, optional
        stream names time offsets dictionary in seconds
    **kwargs : dict, optional
        additional arguments to pass to fly_scan

    """
    if max_channel is None:
        max_channel = [detectors[0].name]
    _md = {
        "detectors": [det.name for det in detectors],
        "motors": [motor.name],
        "plan_args": {
            "detectors": list(map(repr, detectors)),
            "motor": repr(motor),
            "signals": list(max_channel),
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
    motor_signal = motor.name
    max_val = max((start, stop))
    min_val = min((start, stop))
    direction = 1

    def _cleanup():
        yield from bps.mv(Shutter_control, 0)

    for velocity in velocities:
        range = np.abs(start - stop)
        start -= rb_offset
        stop -= rb_offset
        print(f"starting scan from {start} to {stop} at {velocity}")
        if open_shutter:
            yield from bps.mv(Shutter_enable, 0)
            yield from bps.mv(Shutter_control, 1)
        signal_dict = yield from finalize_wrapper(
            fly_max(
                detectors,
                motor,
                start,
                stop,
                velocity,
                md=_md,
                max_channel=max_channel,
                end_on_max=False,
                **kwargs,
            ),
            _cleanup(),
        )
        print(signal_dict)
        print(f"maximum signal of {max_channel[0]} found at {signal_dict[max_channel[0]][motor_signal]}")
        low_side = max((min_val, signal_dict[max_channel[0]][motor_signal] - (range / (2 * range_ratio))))
        high_side = min((max_val, signal_dict[max_channel[0]][motor_signal] + (range / (2 * range_ratio))))
        if snake:
            direction *= -1
        if direction > 0:
            start = low_side
            stop = high_side
        else:
            start = high_side
            stop = low_side
    if end_on_max:
        yield from bps.mv(motor, signal_dict[max_channel[0]][motor_signal] - rb_offset)
    # bec.disable_plots
    return signal_dict
