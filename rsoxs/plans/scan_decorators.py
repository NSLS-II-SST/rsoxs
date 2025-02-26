from nbs_bl.plans.scan_decorators import wrap_metadata
from nbs_bl.utils import merge_func
import bluesky.plan_stubs as bps
from functools import partial
from nbs_bl.hw import Shutter_control, Shutter_open_time, waxs_det, en
from bluesky.preprocessors import finalize_wrapper

from nbs_bl.beamline import GLOBAL_BEAMLINE
from .per_steps import take_exposure_corrected_reading, one_nd_sticky_exp_step, trigger_and_read_with_shutter


def post_scan_hardware_reset():
    ## Make sure the shutter is closed, and the scanlock if off after a scan, even if it errors out
    yield from bps.mv(en.scanlock, 0)
    yield from bps.mv(Shutter_control, 0)


def rsoxs_waxs_decorator(func):
    """
    A decorator that sets up scans for RSoXS. Adds the ability to use the Greateyes detector, and open or close the shutter.

    Parameters
    ----------
    func : callable
        The function to wrap

    Returns
    -------
    callable
        The wrapped function with RSoXS metadata added
    """

    @merge_func(func)
    def _inner(*args, use_2d_detector=False, extra_dets=[], dwell=1, n_exposures=1, open_shutter=True, **kwargs):
        """
        Parameters
        ----------
        use_2d_detector : bool
            Whether to use the Greateyes 2D detector for WAXS/SAXS
        open_shutter : bool
            Whether to open the shutter for the scan. If True, the shutter will be opened before the scan and closed after the scan.
            If False, the shutter will be closed for the duration of the scan. Does not apply to scans using the WAXS detector,
            which have their own shutter control.
        n_exposures : int, optional
            Number of exposures for the Greateyes detector to take per step
        """
        print("RSoXS decorator applied to scan")
        _extra_dets = []
        _extra_dets.extend(extra_dets)

        if use_2d_detector:
            if dwell > 0.001 and dwell < 1000:
                waxs_det.set_exptime(dwell)
                Shutter_open_time.set(dwell * 1000).wait()
                for det in GLOBAL_BEAMLINE.detectors.active:
                    if hasattr(det, "exposure_time"):
                        det.exposure_time.set(
                            max(0.3, dwell - 0.5)
                        ).wait()  ## Intended to only count signal when shutter is open, but will not go below exposure time = 0.3
                    else:
                        print("Invalid time, exposure time not set")

            old_n_exp = waxs_det.number_exposures
            waxs_det.number_exposures = n_exposures
            _extra_dets = [waxs_det]
            _extra_dets.extend(extra_dets)
            if "per_shot" in func.__signature__.parameters:
                rsoxs_per_shot = partial(
                    trigger_and_read_with_shutter, shutter=Shutter_control, lead_detector=waxs_det
                )
                return (
                    yield from finalize_wrapper(
                        plan=func(*args, extra_dets=_extra_dets, per_shot=rsoxs_per_shot, dwell=None, **kwargs),
                        final_plan=post_scan_hardware_reset(),
                    )
                )
            else:
                rsoxs_per_step = rsoxs_per_step = partial(
                    one_nd_sticky_exp_step,
                    take_reading=partial(
                        take_exposure_corrected_reading,
                        shutter=Shutter_control,
                        check_exposure=False,
                        lead_detector=waxs_det,
                    ),
                )
                return (
                    yield from finalize_wrapper(
                        plan=func(*args, extra_dets=_extra_dets, per_step=rsoxs_per_step, dwell=None, **kwargs),
                        final_plan=post_scan_hardware_reset(),
                    )
                )
        else:
            if open_shutter:
                yield from bps.mv(Shutter_control, 1)  # open the shutter for the run
            else:
                yield from bps.mv(Shutter_control, 0)  # close the shutter for the run
            return (
                yield from finalize_wrapper(
                    plan=func(*args, extra_dets=extra_dets, dwell=dwell, **kwargs),
                    final_plan=post_scan_hardware_reset(),
                )
            )

    return _inner
