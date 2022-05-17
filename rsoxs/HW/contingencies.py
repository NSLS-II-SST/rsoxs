import logging
from bluesky.suspenders import (
SuspendBoolHigh, SuspendFloor, SuspendBoolLow, SuspendWhenChanged
)
from sst_funcs.printing import run_report
from ..Functions.contingencies import (
    beamdown_notice,
    beamup_notice,
    enc_clr_gx,
    enc_clr_x,
    OSEmailHandler,
    MakeSafeHandler,
)
from sst_hw.gatevalves import gvll
from sst_hw.shutters import psh4, psh1
from ..HW.signals import ring_current
from ..HW.motors import sam_X
from sst_hw.vacuum import rsoxs_pg_main
from ..HW.detectors import start_det_cooling,stop_det_cooling
from ..startup import RE


run_report(__file__)


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
    psh1.state,
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


suspend_current = SuspendWhenChanged(
    rsoxs_pg_main,
    expected_value='LO<E-03',
    allow_resume=True,
    sleep=30,
    tripped_message="Pressure in the Chamber is above the threshold for having cooling on",
    pre_plan=stop_det_cooling,
    post_plan=start_det_cooling,
)




RE.install_suspender(suspend_current)

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
