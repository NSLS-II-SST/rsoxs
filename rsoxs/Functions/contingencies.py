import bluesky.plan_stubs as bps
import datetime, os
import logging

global no_notifications_until
from ..startup import RE
from ..HW.slackbot import rsoxs_bot
from ..HW.motors import sam_X
from sst_hw.motors import gratingx, mirror2x, mirror2, grating
from sst_funcs.printing import run_report


run_report(__file__)
bls_email = "egann@bnl.gov"

def pause_notices(until=None, **kwargs):
    # pause_notices turns off emails on errors either until a specified time or for a specified duration.
    #
    # for set end time, use until = string (compatible with strptime() in datetime)
    #
    # for duration, use parameters for the datetime.timedelta kwargs: hours= minutes= seconds= days=
    #

    global no_notifications_until
    if until is None and len(kwargs) is 0:
        print("You need to specify either a duration or a timeout.")
    elif until is None:
        no_notifications_until = datetime.datetime.now() + datetime.timedelta(**kwargs)
    elif until is not None:
        no_notifications_until = datetime.datetime.strptime(until)


def resume_notices():
    global no_notifications_until

    no_notifications_until = None


def send_notice(email, subject, msg):
    # os.system('echo '+msg+' | mail -s "'+subject+'" '+email)
    try:
        rsoxs_bot.send_message(subject + "\n" + msg)
    except Exception:
        pass


def send_email(email, subject, msg):
    os.system('echo '+msg+' | mail -s "'+subject+'" '+email)



def send_notice_plan(email, subject, msg):
    send_notice(email, subject, msg)
    yield from bps.sleep(0.1)


def enc_clr_x():
    send_notice(
        "egann@bnl.gov",
        "SST had a small problem",
        "the encoder loss has happened on the RSoXS beamline"
        "\rEverything is probably just fine",
    )
    xpos = sam_X.user_readback.get()
    yield from sam_X.clear_encoder_loss()
    yield from sam_X.home()
    yield from bps.sleep(30)
    yield from bps.mv(sam_X, xpos)


def enc_clr_gx():
    send_notice(
        "egann@bnl.gov",
        "SST had a small problem",
        "the encoder loss has happened on the RSoXS beamline"
        "\rEverything is probably just fine",
    )

    yield from gratingx.clear_encoder_loss()
    yield from gratingx.enable()
    yield from mirror2x.enable()
    yield from mirror2.enable()
    yield from grating.enable()


def det_down_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "<@U016YV35UAJ> SST-1 detector seems to have failed",
        "The temperature is reading below -90C which is a mistake"
        "\rScans have been paused until the detector and IOC are restarted."
    )
def det_up_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "SST-1 detector seems to have recovered",
        "\rScans should resume shortly."
    )

def temp_bad_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "SST-1 detector seems to be out of temperature range",
        "\rScans will pause until the detecor recovers."
    )

def temp_ok_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "SST-1 detector seems to have recovered",
        "\rScans should resume shortly."
    )

def beamdown_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "SST-1 has lost beam",
        "Beam to RSoXS has been lost."
        "\rYour scan has been paused automatically."
        "\rNo intervention needed, but thought you might "
        "like to know.",
    )
    send_email(
        bls_email + "," + user_email,
        "SST-1 has lost beam",
        "Beam to RSoXS has been lost."
        "\rYour scan has been paused automatically."
        "\rNo intervention needed, but thought you might "
        "like to know.",
    )

    yield from bps.null()


def beamup_notice():
    user_email = RE.md["user_email"]
    send_notice(
        bls_email + "," + user_email,
        "SST-1 beam restored",
        "Beam to RSoXS has been restored."
        "\rYour scan has resumed running."
        "\rIf able, you may want to check the data and "
        "make sure intensity is still OK. "
        "\rOne exposure may have been affected",
    )
    send_email(
        bls_email + "," + user_email,
        "SST-1 has lost beam",
        "Beam to RSoXS has been lost."
        "\rYour scan has been paused automatically."
        "\rNo intervention needed, but thought you might "
        "like to know.",
    )
    yield from bps.null()


class OSEmailHandler(logging.Handler):
    def emit(self, record):
        user_email = RE.md["user_email"]
        send_notice(
            bls_email + "," + user_email,
            "<@U016YV35UAJ> SST has thrown an exception",
            record.getMessage(),
        )  # record.stack_info


class MakeSafeHandler(logging.Handler):
    def emit(self, record):
        ...
        # print('close the shutter here')
        # NOTE: this seems to get run anytime there is any problem with bluesky whatso ever, so nothing dramatic should really be done here
        # @TODO insert code to make instrument 'safe', e.g. close shutter
