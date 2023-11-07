from ophyd.sim import NullStatus

from bluesky.preprocessors import monitor_during_wrapper,  finalize_wrapper, finalize_decorator

from bluesky.protocols import Readable, Flyable
import bluesky.utils as utils
from bluesky.utils import Msg, short_uid as _short_uid, single_gen, ensure_generator
from bluesky.preprocessors import plan_mutator


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
