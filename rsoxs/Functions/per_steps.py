
from bluesky.preprocessors import finalize_decorator
from bluesky.preprocessors import rewindable_wrapper, finalize_wrapper
from bluesky.utils import short_uid, separate_devices, all_safe_rewind
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
from sst_hw.diode import (
    Shutter_open_time,
    Shutter_control,
    Shutter_enable,
    Shutter_trigger,
    shutter_open_set
)
from bluesky.utils import Msg, short_uid as _short_uid

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
