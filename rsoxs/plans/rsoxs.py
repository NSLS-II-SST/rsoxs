import bluesky.plan_stubs as bps
from bluesky.preprocessors import finalize_wrapper
from functools import partial
from nbs_bl.hw import (
    en,
    Shutter_control,
    sam_X,
    sam_Y,
    waxs_det,
)

from nbs_bl.printing import run_report
from nbs_bl.plans.scans import nbs_count, nbs_gscan, nbs_spiral_square
from nbs_bl.plans.preprocessors import wrap_metadata
from nbs_bl.utils import merge_func
from nbs_bl.queueserver import GLOBAL_USER_STATUS
from nbs_bl.help import _add_to_import_list, add_to_plan_list, add_to_func_list

from .per_steps import take_exposure_corrected_reading, one_nd_sticky_exp_step

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

run_report(__file__)

GLOBAL_RSOXS_PLANS = GLOBAL_USER_STATUS.request_status_dict("RSOXS_PLANS", use_redis=True)
GLOBAL_RSOXS_PLANS.clear()


def add_to_rsoxs_list(f, key, **plan_info):
    """
    A function decorator that will add the plan to the built-in list
    """
    _add_to_import_list(f, "rsoxs")
    GLOBAL_RSOXS_PLANS[key] = {}
    GLOBAL_RSOXS_PLANS[key].update(plan_info)
    return f


@add_to_plan_list
@merge_func(nbs_count, use_func_name=False, omit_params=["*"])
def timeScan(*args, **kwargs):
    yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(plan=nbs_count(*args, **kwargs), final_plan=post_scan_hardware_reset())
    ## Main difference between Bluesky list_scan and scan_nd is that scan_nd has a cycler that can run the scan for all combinations of parameters (e.g., energy, polarization, positions, temperatures).  But for most cases here, it is simpler to use nested for loops, which accomplishes the same purpose.
## Use this to run counting scans
## Example use:
## RE(timeScan(num=10, delay=0, dwell=2))
## num is number of data points,delay is time between datapoints, dwell is exposure time per point


## TODO: this still does not work fully
@add_to_plan_list
@merge_func(timeScan, use_func_name=False) 
def timeScan_withWAXSCamera(*args, extra_dets=[], n_exposures=1, dwell=1, **kwargs):
    """
    Step scanned RSoXS function with WAXS Detector

    Parameters
    ----------
    n_exposures : int, optional
        If greater than 1, take multiple exposures per step
    """
    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    yield from bps.abs_set(waxs_det.cam.acquire_time, dwell)
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_step = partial(
        one_nd_sticky_exp_step,
        take_reading=partial(
            take_exposure_corrected_reading, shutter=Shutter_control, check_exposure=False, lead_detector=waxs_det
        ),
    )
    yield from timeScan(*args, extra_dets=_extra_dets, per_shot=rsoxs_per_step, dwell=dwell, **kwargs)
    waxs_det.number_exposures = old_n_exp
## Use this to run RSoXS step scans using the 2D detector




@add_to_plan_list
@merge_func(nbs_gscan, use_func_name=False, omit_params=["motor"])
def energyScan(*args, **kwargs):
    yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(plan=nbs_gscan(en.energy, *args, **kwargs), final_plan=post_scan_hardware_reset())
    ## Main difference between Bluesky list_scan and scan_nd is that scan_nd has a cycler that can run the scan for all combinations of parameters (e.g., energy, polarization, positions, temperatures).  But for most cases here, it is simpler to use nested for loops, which accomplishes the same purpose.
## Use this to run NEXAFS step scans


@add_to_plan_list
@merge_func(energyScan, use_func_name=False, omit_params=["per_step"]) ## TODO: Is per_step actually supposed to be omitted?  It ends up being used in the energy scan.  Is that the cause of the camera artifacts?
def energyScan_withWAXSCamera(*args, extra_dets=[], n_exposures=1, dwell=1, **kwargs):
    """
    Count scanned RSoXS function with WAXS Detector

    Parameters
    ----------
    n_exposures : int, optional
        If greater than 1, take multiple exposures per step
    """
    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    yield from bps.abs_set(waxs_det.cam.acquire_time, dwell)
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_step = partial(
        one_nd_sticky_exp_step,
        take_reading=partial(
            take_exposure_corrected_reading, shutter=Shutter_control, check_exposure=False, lead_detector=waxs_det
        ),
    )
    yield from energyScan(*args, extra_dets=_extra_dets, per_step=rsoxs_per_step, dwell=dwell, **kwargs)
    waxs_det.number_exposures = old_n_exp
## Use this to run RSoXS step scans using the 2D detector

## Example of a common use: 
## RE(energyScan_withWAXSCamera(*(250, 282, 1.45, 297, 0.3, 350, 1.45), dwell=2, n_exposures=1, group_name="Test"))
## dwell is the exposure time in seconds, n_exposures is the number of repeats


@add_to_plan_list
@merge_func(nbs_spiral_square, use_func_name=False, omit_params=["*"])
def spiralScan(*args, extra_dets=[], diameter=1.8, stepsize=0.3, dwell=1, n_exposures=1, energy=270, polarization=0, **kwargs):
    
    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    yield from bps.abs_set(waxs_det.cam.acquire_time, dwell)
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_step = partial(
        one_nd_sticky_exp_step,
        take_reading=partial(
            take_exposure_corrected_reading, shutter=Shutter_control, check_exposure=False, lead_detector=waxs_det
        ),
    )

    yield from finalize_wrapper(plan=nbs_spiral_square(
                                                        x_motor = sam_X,
                                                        y_motor = sam_Y,
                                                        x_center = sam_X.user_setpoint.get(),
                                                        y_center = sam_Y.user_setpoint.get(),
                                                        x_range = diameter,
                                                        y_range = diameter,
                                                        x_num = round(diameter/stepsize) + 1,
                                                        y_num = round(diameter/stepsize) + 1,
                                                        per_step = rsoxs_per_step,
                                                        extra_dets = _extra_dets,
                                                        energy=energy,
                                                        polarization=polarization
                                                        ), 
                                final_plan=post_scan_hardware_reset())
## spiral scans for to find good spot on sample



def post_scan_hardware_reset():
    ## Make sure the shutter is closed, and the scanlock if off after a scan, even if it errors out
    yield from bps.mv(en.scanlock, 0)
    yield from bps.mv(Shutter_control, 0)


def _wrap_rsoxs(element, edge):
    def decorator(func):
        return wrap_metadata({"element": element, "edge": edge, "scantype": "rsoxs"})(func)

    return decorator


def _rsoxs_factory(energy_grid, element, edge, key):
    @_wrap_rsoxs(element, edge)
    @wrap_metadata({"plan_name": key})
    @merge_func(rsoxs_step_scan, omit_params=["args"])
    def inner(**kwargs):
        """Parameters
        ----------
        repeat : int
            Number of times to repeat the scan
        **kwargs :
            Arguments to be passed to tes_gscan

        """

        yield from rsoxs_step_scan(*energy_grid, **kwargs)

    d = f"Perform an in-place RSoXS scan for {element} with energy pattern {energy_grid} \n"
    inner.__doc__ = d + inner.__doc__

    inner.__qualname__ = key
    inner.__name__ = key
    inner._edge = edge
    inner._short_doc = f"Do RSoXS for {element} from {energy_grid[0]} to {energy_grid[-2]}"
    return inner


@add_to_func_list
def load_rsoxs(filename):
    """
    Load RSoXS plans from a TOML file and inject them into the IPython user namespace.

    Parameters
    ----------
    filename : str
        Path to the TOML file containing XAS plan definitions
    """
    try:
        # Get IPython's user namespace
        ip = get_ipython()
        user_ns = ip.user_ns
    except (NameError, AttributeError):
        # Not running in IPython, just return the generated functions
        user_ns = None

    generated_plans = {}
    with open(filename, "rb") as f:
        regions = tomllib.load(f)
        for _key, value in regions.items():
            if "xas" in _key:
                key = _key.replace("xas", "rsoxs")
            else:
                key = _key
            name = value.get("name", key)
            region = value.get("region")
            element = value.get("element", "")
            edge = value.get("edge", "")
            rsoxs_func = _rsoxs_factory(region, element, edge, key)
            add_to_rsoxs_list(rsoxs_func, key, name=name, element=element, edge=edge, region=region)

            # Store the function
            generated_plans[key] = rsoxs_func

            # If we're in IPython, inject into user namespace
            if user_ns is not None:
                user_ns[key] = rsoxs_func

    # Return the generated plans dictionary in case it's needed
    return generated_plans
