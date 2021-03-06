import logging
import bluesky.plan_stubs as bps
from bluesky.suspenders import (
SuspendBoolHigh, SuspendFloor, SuspendCeil, SuspendBoolLow, SuspendWhenChanged
)
from sst_funcs.printing import run_report
from ..Functions.contingencies import (
    beamdown_notice,
    beamup_notice,
    enc_clr_gx,
    enc_clr_x,
    OSEmailHandler,
    MakeSafeHandler,
    det_down_notice,
    temp_bad_notice,
    temp_ok_notice
)
from sst_hw.gatevalves import gvll
from sst_hw.shutters import psh4, FEsh1
from ..HW.signals import ring_current
from ..HW.motors import sam_X
from sst_hw.vacuum import rsoxs_pg_main
from ..HW.detectors import start_det_cooling,stop_det_cooling,saxs_det,waxs_det
from ..startup import RE


run_report(__file__)


def waxs_back_on():
    yield from bps.mv(
        waxs_det.cam.temperature,-80,
        waxs_det.cam.enable_cooling,1,
        waxs_det.cam.bin_x,4,
        waxs_det.cam.bin_y,4)



def saxs_back_on():
    yield from bps.mv(
        saxs_det.cam.temperature,-80,
        saxs_det.cam.enable_cooling,1,
        saxs_det.cam.bin_x,4,
        saxs_det.cam.bin_y,4)

suspend_gvll = SuspendBoolLow(
    gvll.state,
    sleep=30,
    tripped_message="Gate valve to load lock is closed, waiting for it to open",
)

suspend_shutter4 = SuspendBoolHigh(
    psh4.state,
    sleep=30,
    tripped_message="Shutter 4 Closed, waiting for it to open",
    pre_plan=beamdown_notice,
    post_plan=beamup_notice,
)

suspend_shutter1 = SuspendBoolHigh(
    FEsh1.state,
    sleep=30,
    tripped_message="Front End Shutter Closed, waiting for it to open",
    pre_plan=beamdown_notice,
    post_plan=beamup_notice,
)

RE.install_suspender(suspend_shutter1)
# RE.install_suspender(suspend_shutter4)
# RE.install_suspender(suspend_gvll)

suspend_current = SuspendFloor(
    ring_current,
    resume_thresh=350,
    suspend_thresh=250,
    sleep=30,
    tripped_message="Beam Current is below threshold, will resume when above 350 mA",
    pre_plan=beamdown_notice,
    post_plan=beamup_notice,
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


suspend_saxs_temp_low = SuspendFloor(
    saxs_det.cam.temperature_actual,
    resume_thresh=-85,
    suspend_thresh=-90,
    sleep=30,
    tripped_message="the detector temperature is below -90C, will resume when above -85C\n this likely means the detector has died and needs to be restarted",
    pre_plan=det_down_notice,
    post_plan=saxs_back_on,
)



suspend_saxs_temp_high = SuspendCeil(
    saxs_det.cam.temperature_actual,
    resume_thresh=-78,
    suspend_thresh=-75,
    sleep=30,
    tripped_message="the detector temperature is above -75C, will resume when below -78C",
    pre_plan=det_down_notice,
    post_plan=temp_ok_notice,
)


def waxs_back_on():
    yield from bps.mv(
        waxs_det.cam.temperature,-80,
        waxs_det.cam.enable_cooling,1,
        waxs_det.cam.bin_x,4,
        waxs_det.cam.bin_y,4)



def saxs_back_on():
    yield from bps.mv(
        saxs_det.cam.temperature,-80,
        saxs_det.cam.enable_cooling,1,
        saxs_det.cam.bin_x,4,
        saxs_det.cam.bin_y,4)


suspend_pressure = SuspendWhenChanged(
    rsoxs_pg_main,
    expected_value='LO<E-03',
    allow_resume=True,
    sleep=30,
    tripped_message="Pressure in the Chamber is above the threshold for having cooling on",
    pre_plan=stop_det_cooling,
    post_plan=start_det_cooling,
)




RE.install_suspender(suspend_current)
RE.install_suspender(suspend_pressure)
RE.install_suspender(suspend_waxs_temp_low)
RE.install_suspender(suspend_waxs_temp_high)
RE.install_suspender(suspend_saxs_temp_low)
RE.install_suspender(suspend_saxs_temp_high)




suspendx = SuspendBoolHigh(
    sam_X.enc_lss,
    sleep=40,
    tripped_message="Sample X has lost encoder position, resetting, please wait, scan will "
    "resume automatically.",
    pre_plan=enc_clr_x,
)
suspendgx = SuspendBoolHigh(
    sam_X.enc_lss,
    sleep=40,
    tripped_message="Grating X has lost encoder position, resetting, please wait, scan will "
    "resume automatically.",
    pre_plan=enc_clr_gx,
)
RE.install_suspender(suspendx)


# if there is no scatter, pause


logger = logging.getLogger("bluesky")
mail_handler = OSEmailHandler()
mail_handler.setLevel(
    "ERROR"
)  # Only email for if the level is ERROR or higher (CRITICAL).
logger.addHandler(mail_handler)

safe_handler = MakeSafeHandler()
safe_handler.setLevel("ERROR")  # is this correct?
logger.addHandler(safe_handler)


def turn_on_checks():
    RE.install_suspender(suspend_shutter1)
    # RE.install_suspender(suspend_shutter4)
    # RE.install_suspender(suspend_gvll)
    RE.install_suspender(suspend_current)
    RE.install_suspender(suspendx)
    logger.addHandler(safe_handler)
    logger.addHandler(mail_handler)


def turn_off_checks():
    RE.remove_suspender(suspend_shutter1)
    # RE.remove_suspender(suspend_shutter4)
    # RE.remove_suspender(suspend_gvll)
    RE.remove_suspender(suspend_current)
    RE.remove_suspender(suspendx)
    logger.removeHandler(safe_handler)
    logger.removeHandler(mail_handler)
