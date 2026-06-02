import bluesky.plan_stubs as bps
from rsoxs.plans.plan_stubs import skinnystage, skinnyunstage
import bluesky.plans as bp
from bluesky.preprocessors import make_decorator
import bluesky_darkframes

from nbs_bl.hw import (
    en, 
    shutter_control, 
    shutter_open_time, 
    #Det_S, 
    Det_W, 
    sam_Th, 
    sam_X, 
    sam_Y, 
    #waxs_det,
)
from nbs_bl.plans.scans import nbs_count
from nbs_bl.printing import boxed_text, run_report
from ..HW.signals import default_sigs
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl

run_report(__file__)


# saxs_det = RSOXSGreatEyesDetector('XF:07ID1-ES:1{GE:1}', name='Small Angle CCD Detector',
#                                   read_attrs=['tiff', 'stats1.total', 'saturated','under_exposed','cam']
#                                   )

# saxs_det.cam.read_attrs = ['acquire_time']
# saxs_det.transform_type = 3
# saxs_det.cam.ensure_nonblocking()
# saxs_det.setup_cam()
# #

# to simulate, use this line, and comment out the relevent detector above
# saxs_det = SimGreatEyes(name="Simulated SAXS camera")

## TODO: the stop_det_cooling, start_det_cooling, set_exposure, and exposure functions probably can be removed, as they are in devices/detectors.py in the RSoXSGreatEyesDetector class.
## Once the camera is fully working, try commenting these out and testing.
## Actually, start_det_cooling and stop_det_cooling are used in Jamie's new suspenders, so maybe they should be kept.  Understand why we use these instead of the functions in the RSoXSGreatEyesDetector class.

def stop_det_cooling():
    # yield from saxs_det.cooling_off()
    waxs_det = bl["waxs_det"]
    yield from waxs_det.cooling_off_plan()


def start_det_cooling():
    # yield from saxs_det.set_temp(-80)
    waxs_det = bl["waxs_det"]
    yield from waxs_det.set_temp_plan(-80)


def set_exposure(exposure):
    waxs_det = bl["waxs_det"]

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
    waxs_det = bl["waxs_det"]
    return "   " + waxs_det.exposure()  # + "\n   " + waxs_det.exposure()




# adding for testing

count = bp.count





