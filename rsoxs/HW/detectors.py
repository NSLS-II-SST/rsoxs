import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.preprocessors import make_decorator
import bluesky_darkframes

from ..devices.detectors import RSOXSGreatEyesDetector, SimGreatEyes
from nbs_bl.hw import en, shutter_control, shutter_open_time, Det_S, Det_W, sam_Th, sam_X, sam_Y, waxs_det
from nbs_bl.printing import boxed_text, run_report
from ..Functions.per_steps import trigger_and_read_with_shutter
from ..startup import RE
from functools import partial
from ..HW.signals import default_sigs

run_report(__file__)


# saxs_det = RSOXSGreatEyesDetector('XF:07ID1-ES:1{GE:1}', name='Small Angle CCD Detector',
#                                   read_attrs=['tiff', 'stats1.total', 'saturated','under_exposed','cam']
#                                   )

# saxs_det.cam.read_attrs = ['acquire_time']
# saxs_det.transform_type = 3
# saxs_det.cam.ensure_nonblocking()
# saxs_det.setup_cam()
# #
"""
waxs_det = RSOXSGreatEyesDetector(
   "XF:07ID1-ES:1{GE:2}",
   name="Wide Angle CCD Detector",
   read_attrs=['tiff', 'stats1.total', 'saturated','under_exposed','cam'],
)

waxs_det.cam.read_attrs = ["acquire_time"]
waxs_det.transform_type = 1
waxs_det.cam.ensure_nonblocking()
waxs_det.setup_cam()

# saxs_det.stats1.name = "SAXS fullframe"
waxs_det.stats1.name = "WAXS fullframe"
"""

# to simulate, use this line, and comment out the relevent detector above
# saxs_det = SimGreatEyes(name="Simulated SAXS camera")


def stop_det_cooling():
    # yield from saxs_det.cooling_off()
    yield from waxs_det.cooling_off_plan()


def start_det_cooling():
    # yield from saxs_det.set_temp(-80)
    yield from waxs_det.set_temp_plan(-80)


def set_exposure(exposure):
    if exposure > 0.001 and exposure < 1000:
        # saxs_det.set_exptime(exposure)
        waxs_det.set_exptime(exposure)
        shutter_open_time.set(exposure * 1000).wait()
        for sig in default_sigs:
            if hasattr(sig, "exposure_time"):
                sig.exposure_time.set(max(0.3, exposure - 0.5)).wait()
    else:
        print("Invalid time, exposure time not set")


def exposure():
    return "   " + waxs_det.exposure()  # + "\n   " + waxs_det.exposure()


def snapshot(secs=0, count=1, name=None, energy=None, detn="waxs", n_exp=1):
    """
    snap of detectors to clear any charge from light hitting them - needed before starting scans or snapping images
    :return:
    """
    sw = {"waxs": waxs_det}  # , "waxs": waxs_det}
    det = sw[detn]
    if count == 1:
        counts = ""
    elif count <= 0:
        count = 1
        counts = ""
    else:
        count = round(count)
        counts = "s"
    if secs <= 0:
        secs = det.cam.acquire_time.get()

    if secs == 1:
        secss = ""
    else:
        secss = "s"

    if isinstance(energy, float):
        yield from bps.mv(en, energy)

    boxed_text(
        "Snapshot",
        "Taking {} snapshot{} of {} second{} with {} named {} at {} eV".format(
            count, counts, secs, secss, det.name, name, energy
        ),
        "red",
    )
    samsave = RE.md["sample_name"]
    if secs:
        set_exposure(secs)
    if name is not None:
        RE.md["sample_name"] = name
    # yield from bp.count([det, en.energy], num=count)
    # print(det)
    # print(bp.count)
    # print(count)
    det.number_exposures = n_exp
    yield from bp.count(
        [det] + default_sigs, num=count, per_shot=partial(trigger_and_read_with_shutter, shutter=shutter_control)
    )
    if name is not None:
        RE.md["sample_name"] = samsave


# adding for testing

count = bp.count


def dark_plan(det):
    yield from det.skinnyunstage()
    # yield from bps.mv(det.cam.shutter_mode, 0)
    n_exp = det.cam.num_images.get()
    yield from bps.mv(det.cam.num_images, 1, det.cam.shutter_mode, 0)

    yield from det.skinnystage()
    yield from bps.trigger(det, group="darkframe-trigger")
    yield from bps.wait("darkframe-trigger")
    snapshot = bluesky_darkframes.SnapshotDevice(det)

    yield from det.skinnyunstage()
    if det.useshutter:
        yield from bps.mv(det.cam.shutter_mode, 2)
    yield from bps.mv(det.cam.num_images, n_exp)
    yield from det.skinnystage()
    return snapshot


# dark_frame_preprocessor_saxs = bluesky_darkframes.DarkFramePreprocessor(
#     dark_plan=dark_plan,
#     detector=saxs_det,
#     max_age=300,
#     locked_signals=[
#         saxs_det.cam.acquire_time,
#         Det_S.user_setpoint,
#         saxs_det.cam.bin_x,
#         saxs_det.cam.bin_y,
#     ],
#     limit=20,
# )


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


dark_frames_enable_waxs = make_decorator(dark_frame_preprocessor_waxs)()
# dark_frames_enable_saxs = make_decorator(dark_frame_preprocessor_saxs)()
