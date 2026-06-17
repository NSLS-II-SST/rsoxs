import IPython
import bluesky.plan_stubs as bps
import bluesky_darkframes
from bluesky.suspenders import SuspendFloor, SuspendCeil

from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from nbs_bl.hw import Det_W, sam_Th, sam_X, sam_Y

from rsoxs.plans.plan_stubs import skinnystage, skinnyunstage
from ..Functions.contingencies import (
    det_down_notice,
    temp_bad_notice,
    temp_ok_notice,
)


RE = bl.run_engine

WAXS_MODE_NAMESPACE_NAMES = (
    "dark_plan",
    "waxs_back_on",
    "dark_frame_preprocessor_waxs",
    "dark_frame_preprocessor_waxs_spirals",
    "waxs_spiral_mode",
    "waxs_normal_mode",
    "suspend_waxs_temp_low",
    "suspend_waxs_temp_high",
)

_waxs_mode_namespace = None
_waxs_mode_objects = {}


def dark_plan(det):
    yield from skinnyunstage(det)
    n_exp = det.cam.num_images.get()
    # Sets number of exposures to 1 so that it only takes one dark image regardless of however many repeat light images are taken.
    # Disables shutter because the shutter needs to be closed to take a dark image.
    yield from bps.mv(det.cam.num_images, 1, det.cam.shutter_mode, 0)
    yield from skinnystage(det)
    det.log.debug("Skinnystaged", det.name)
    yield from bps.trigger(det, group="darkframe-trigger")
    yield from bps.wait("darkframe-trigger")
    snapshot = bluesky_darkframes.SnapshotDevice(det)
    yield from skinnyunstage(det)

    # If the shutter is to be used for light images, it is enabled
    if det.useshutter:
        yield from bps.mv(det.cam.shutter_mode, 2)
    # Desired number of exposures is restored for light images
    yield from bps.mv(det.cam.num_images, n_exp)
    yield from skinnystage(det)
    return snapshot


def waxs_back_on():
    waxs_det = bl["waxs_det"]
    yield from bps.mv(
        waxs_det.cam.temperature,
        -80,
        waxs_det.cam.enable_cooling,
        1,
        waxs_det.cam.bin_x,
        4,
        waxs_det.cam.bin_y,
        4,
    )


def activate_waxs_mode():
    """
    Activate WAXS detector helpers.

    Returns
    -------
    bool
        True if WAXS setup completed.
    """
    namespace = _get_ipython_namespace()
    _load_waxs_detector(namespace=namespace)
    objects = _build_waxs_mode_objects()
    objects["waxs_normal_mode"]()
    _install_waxs_namespace(objects, namespace)
    return True


def deactivate_waxs_mode():
    """
    Deactivate WAXS detector helpers.

    Returns
    -------
    bool
        True if WAXS cleanup completed.
    """
    _remove_waxs_preprocessors()
    _remove_waxs_namespace()
    return True


def _get_ipython_namespace():
    ip = IPython.get_ipython()
    if ip is None:
        return None
    return ip.user_global_ns


def _load_waxs_detector(namespace=None):
    if "waxs_det" in bl.devices:
        return bl["waxs_det"]
    if bl.is_device_deferred("waxs_det"):
        bl.load_deferred_device("waxs_det", namespace=namespace)
    return bl["waxs_det"]


def _build_waxs_mode_objects():
    waxs_det = bl["waxs_det"]

    dark_frame_preprocessor_waxs = bluesky_darkframes.DarkFramePreprocessor(
        dark_plan=dark_plan,
        detector=waxs_det,
        max_age=180,
        locked_signals=[
            waxs_det.cam.acquire_time,
            Det_W.user_setpoint,
            waxs_det.cam.bin_x,
            waxs_det.cam.bin_y,
            sam_X.user_setpoint,
            sam_Th.user_setpoint,
            sam_Y.user_setpoint,
        ],
        limit=100,
    )
    dark_frame_preprocessor_waxs_spirals = bluesky_darkframes.DarkFramePreprocessor(
        dark_plan=dark_plan,
        detector=waxs_det,
        max_age=120,
        locked_signals=[
            waxs_det.cam.acquire_time,
            Det_W.user_setpoint,
            waxs_det.cam.bin_x,
            waxs_det.cam.bin_y,
        ],
        limit=10,
    )

    def waxs_spiral_mode():
        _replace_waxs_preprocessor(
            dark_frame_preprocessor_waxs_spirals,
            dark_frame_preprocessor_waxs,
        )

    def waxs_normal_mode():
        _replace_waxs_preprocessor(
            dark_frame_preprocessor_waxs,
            dark_frame_preprocessor_waxs_spirals,
        )

    suspend_waxs_temp_low = SuspendFloor(
        waxs_det.cam.temperature_actual,
        resume_thresh=-85,
        suspend_thresh=-90,
        sleep=30,
        tripped_message="the detector temperature is below -90C, will resume when above -85C\n this likely means the detector has died and needs to be restarted",
        pre_plan=det_down_notice,
        post_plan=waxs_back_on,
    )
    suspend_waxs_temp_high = SuspendCeil(
        waxs_det.cam.temperature_actual,
        resume_thresh=-78,
        suspend_thresh=-75,
        sleep=30,
        tripped_message="the detector temperature is above -75C, will resume when below -78C",
        pre_plan=temp_bad_notice,
        post_plan=temp_ok_notice,
    )

    return {
        "dark_plan": dark_plan,
        "waxs_back_on": waxs_back_on,
        "dark_frame_preprocessor_waxs": dark_frame_preprocessor_waxs,
        "dark_frame_preprocessor_waxs_spirals": dark_frame_preprocessor_waxs_spirals,
        "waxs_spiral_mode": waxs_spiral_mode,
        "waxs_normal_mode": waxs_normal_mode,
        "suspend_waxs_temp_low": suspend_waxs_temp_low,
        "suspend_waxs_temp_high": suspend_waxs_temp_high,
    }


def _replace_waxs_preprocessor(preprocessor, other_preprocessor):
    _remove_preprocessor(other_preprocessor)
    _remove_preprocessor(preprocessor)
    RE.preprocessors.append(preprocessor)


def _remove_waxs_preprocessors():
    for name in (
        "dark_frame_preprocessor_waxs",
        "dark_frame_preprocessor_waxs_spirals",
    ):
        preprocessor = _waxs_mode_objects.get(name, None)
        if preprocessor is not None:
            _remove_preprocessor(preprocessor)


def _remove_preprocessor(preprocessor):
    try:
        RE.preprocessors.remove(preprocessor)
    except ValueError:
        pass


def _install_waxs_namespace(objects, namespace):
    global _waxs_mode_namespace
    _waxs_mode_namespace = namespace
    _waxs_mode_objects.clear()
    _waxs_mode_objects.update(objects)
    globals().update(objects)
    if namespace is not None:
        namespace.update(objects)


def _remove_waxs_namespace():
    namespace = _waxs_mode_namespace
    for name, obj in list(_waxs_mode_objects.items()):
        if namespace is not None and namespace.get(name, None) is obj:
            namespace.pop(name, None)
        if globals().get(name, None) is obj and name not in {"dark_plan", "waxs_back_on"}:
            globals().pop(name, None)
    _waxs_mode_objects.clear()
