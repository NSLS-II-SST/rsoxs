## TODO: would like to change the name of this file to scans.py, but when I change the name and propagate everywhere, I still run into an error ModuleNotFoundError: No module named "rsoxs.plans.rsoxs"

import bluesky.plan_stubs as bps
from bluesky.preprocessors import finalize_wrapper
from functools import partial
from nbs_bl.hw import (
    en,
    Shutter_control,
    Shutter_open_time,
    sam_X,
    sam_Y,
    waxs_det,
)

from nbs_bl.beamline import GLOBAL_BEAMLINE
from nbs_bl.printing import run_report
from nbs_bl.plans.scans import nbs_count, nbs_gscan, nbs_spiral_square
from nbs_bl.plans.preprocessors import wrap_metadata
from nbs_bl.utils import merge_func
from nbs_bl.queueserver import GLOBAL_USER_STATUS
from nbs_bl.help import _add_to_import_list, add_to_plan_list, add_to_func_list, add_to_plan_list

from rsoxs_scans.defaultEnergyParameters import energyListParameters
from .per_steps import take_exposure_corrected_reading, one_nd_sticky_exp_step, trigger_and_read_with_shutter
from .mdConstructor import mdToUpdateConstructor

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


## Main difference between Bluesky list_scan and scan_nd is that scan_nd has a cycler that can run the scan for all combinations of parameters (e.g., energy, polarization, positions, temperatures).  But for most cases here, it is simpler to use nested for loops, which accomplishes the same purpose.

## count (time) scans. 
## Example use:  
## RE(nbs_count(num=10, use_2d_detector=False, delay=0, dwell=2)) ## Doesn't take images
## num is number of data points,delay is time between datapoints, dwell is exposure time per point
## RE(nbs_count(num=10, use_2d_detector=True, delay=0, dwell=2)) ## Takes images





@add_to_plan_list
@merge_func(nbs_spiral_square, use_func_name=False, omit_params=["*"])
def spiral_scan(*args, extra_dets=[], stepsize=0.3, widthX=1.8, widthY=1.8, dwell=1, n_exposures=1, energy=270, polarization=0, **kwargs):
    
    

    ## TODO: Works without beam, but test the next time I have beam to make sure that images look correct and that there is not light on top of the beamstop
    ## Eliot's set_exposure function
    if dwell > 0.001 and dwell < 1000:
        waxs_det.set_exptime(dwell)
        Shutter_open_time.set(dwell * 1000).wait()
        for det in GLOBAL_BEAMLINE.detectors.active:
            if hasattr(det,'exposure_time'):
                det.exposure_time.set(max(0.3,dwell-0.5)).wait() ## Intended to only count signal when shutter is open, but will not go below exposure time = 0.3
    else:
        print("Invalid time, exposure time not set")


    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    #yield from bps.abs_set(waxs_det.cam.acquire_time, dwell)
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_step = partial(
        one_nd_sticky_exp_step,
        #remember={},
        take_reading=partial(
            take_exposure_corrected_reading, shutter=Shutter_control, check_exposure=False, lead_detector=waxs_det
        ),
    )

    yield from finalize_wrapper(plan=nbs_spiral_square(
                                                        x_motor = sam_X,
                                                        y_motor = sam_Y,
                                                        x_center = sam_X.user_setpoint.get(),
                                                        y_center = sam_Y.user_setpoint.get(),
                                                        x_range = widthX,
                                                        y_range = widthY,
                                                        x_num = round(widthX/stepsize) + 1,
                                                        y_num = round(widthY/stepsize) + 1,
                                                        per_step = rsoxs_per_step,
                                                        extra_dets = _extra_dets,
                                                        energy=energy,
                                                        polarization=polarization,
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



## <functionName>? prints out the source code in Bluesky










## TODO: Delete everything below here after code has been tested.  No longer using these.
## ***********************************************************************************************************
@add_to_plan_list
@merge_func(nbs_count, use_func_name=False, omit_params=["*"])
def timeScan(*args, **kwargs):
    """
    Counting scans intended to measure variations in signals over time while no motors are being moved.

    Parameters
    ----------
    num : int, optional
        Number of datapoints to collect
    """

    md_ToUpdate = mdToUpdateConstructor(extraMD={
        "scanType": "timeScan"
    })

    yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(plan=nbs_count(*args, **kwargs, md=md_ToUpdate), final_plan=post_scan_hardware_reset())
## Main difference between Bluesky list_scan and scan_nd is that scan_nd has a cycler that can run the scan for all combinations of parameters (e.g., energy, polarization, positions, temperatures).  But for most cases here, it is simpler to use nested for loops, which accomplishes the same purpose.
## Example use:
## RE(timeScan(num=10, delay=0, dwell=2))
## num is number of data points,delay is time between datapoints, dwell is exposure time per point


## TODO: this still does not work fully
@add_to_plan_list
@merge_func(timeScan, use_func_name=False) 
def timeScan_withWAXSCamera(*args, extra_dets=[], n_exposures=1, dwell=1, **kwargs):
    
    ## TODO: Works without beam, but test the next time I have beam to make sure that images look correct and that there is not light on top of the beamstop
    ## Eliot's set_exposure function
    if dwell > 0.001 and dwell < 1000:
        waxs_det.set_exptime(dwell)
        Shutter_open_time.set(dwell * 1000).wait()
        for det in GLOBAL_BEAMLINE.detectors.active:
            if hasattr(det,'exposure_time'):
                det.exposure_time.set(max(0.3,dwell-0.5)).wait() ## Intended to only count signal when shutter is open, but will not go below exposure time = 0.3
    else:
        print("Invalid time, exposure time not set")

    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    #yield from bps.abs_set(waxs_det.cam.acquire_time, dwell) ## Taken care of in set_exposure but technically fine to uncomment.  Not sure what is the difference.between acquire_time and set_exptime
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_shot = partial(
        trigger_and_read_with_shutter, 
        shutter=Shutter_control,
        lead_detector=waxs_det
        )
    yield from timeScan(*args, extra_dets=_extra_dets, per_shot=rsoxs_per_shot, dwell=None, **kwargs)
    ## dwell=None ensures that nbs_bl does not set a default 1.0 s exposure
    waxs_det.number_exposures = old_n_exp
## Use this to run RSoXS step scans using the 2D detector




@add_to_plan_list
@merge_func(nbs_gscan, use_func_name=False, omit_params=["motor"])
def energyScan(energyParameters, *args, scanType="nexafs", **kwargs):
    
    if isinstance(energyParameters, str): energyParameters = energyListParameters[energyParameters]

    md_ToUpdate = mdToUpdateConstructor(extraMD={
        "scanType": scanType
    })
    
    yield from bps.mv(Shutter_control, 1)
    yield from finalize_wrapper(plan=nbs_gscan(en.energy, *energyParameters, *args, md=md_ToUpdate, **kwargs), final_plan=post_scan_hardware_reset())
    ## Main difference between Bluesky list_scan and scan_nd is that scan_nd has a cycler that can run the scan for all combinations of parameters (e.g., energy, polarization, positions, temperatures).  But for most cases here, it is simpler to use nested for loops, which accomplishes the same purpose.
## Use this to run NEXAFS step scans
## TODO: add the ability to run the scan up then down that list of energies.  Lucas would want that, and it would provide a good sanity check in many cases.


@add_to_plan_list
@merge_func(energyScan, use_func_name=False, omit_params=["per_step"]) ## TODO: Is per_step actually supposed to be omitted?  It ends up being used in the energy scan.  Is that the cause of the camera artifacts?
def energyScan_with2DDetector(*args, extra_dets=[], n_exposures=1, dwell=1, **kwargs):
    """
    Count scanned RSoXS function with WAXS Detector

    Parameters
    ----------
    n_exposures : int, optional
        If greater than 1, take multiple exposures per step
    """
    """
    ## Eliot's set_exposure function
    ## If using this, comment out the acquire_time part below and remove dwell=dwell in the final yield statement
    ## SEems like timescan and energy scan have different format for per_step vs. per_shot, but haven't understood fully
    ## For now, running snapwaxs before this seems to make it work
    ## TODO: When I next have beam, test this function
    if dwell > 0.001 and dwell < 1000:
        waxs_det.set_exptime(dwell)
        Shutter_open_time.set(dwell * 1000).wait()
        for det in GLOBAL_BEAMLINE.detectors.active:
            if hasattr(det,'exposure_time'):
                det.exposure_time.set(max(0.3,dwell-0.5)).wait()
    else:
        print("Invalid time, exposure time not set")

    """

    old_n_exp = waxs_det.number_exposures
    waxs_det.number_exposures = n_exposures
    yield from bps.abs_set(waxs_det.cam.acquire_time, dwell) ## Probably taken care of by set_exposure above
    _extra_dets = [waxs_det]
    _extra_dets.extend(extra_dets)
    rsoxs_per_step = partial(
        one_nd_sticky_exp_step,
        take_reading=partial(
            take_exposure_corrected_reading, 
            shutter=Shutter_control, 
            check_exposure=False, 
            lead_detector=waxs_det
        ),
    )
    yield from energyScan(*args, extra_dets=_extra_dets, per_step=rsoxs_per_step, dwell=dwell, **kwargs)
    waxs_det.number_exposures = old_n_exp
## Use this to run RSoXS step scans using the 2D detector

## Example of a common use: 
## RE(energyScan_withWAXSCamera(*(250, 282, 1.45, 297, 0.3, 350, 1.45), dwell=2, n_exposures=1, group_name="Test"))
## dwell is the exposure time in seconds, n_exposures is the number of repeats


## ***********************************************************************************************************