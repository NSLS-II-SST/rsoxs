import bluesky.plan_stubs as bps
from sst.CommonFunctions.functions import run_report
from sst.Base.slits import Slits


run_report(__file__)


slits1 = Slits(
    "XF:07ID2-ES1{Slt1-Ax:", name="Upstream Scatter Slits", kind="hinted", concurrent=1
)
slits2 = Slits(
    "XF:07ID2-ES1{Slt2-Ax:", name="Middle Scatter Slits", kind="hinted", concurrent=1
)
slits3 = Slits(
    "XF:07ID2-ES1{Slt3-Ax:", name="Final Scatter Slits", kind="hinted", concurrent=1
)


def set_slit_offsets():
    yield from bps.mv(
        slits3.bottom.user_offset,
        -1.39,
        slits3.top.user_offset,
        -1.546,
        slits3.outboard.user_offset,
        -0.651,
        slits3.inboard.user_offset,
        0.615,
        slits2.inboard.user_offset,
        -0.84,
        slits2.outboard.user_offset,
        -1.955,
        slits2.bottom.user_offset,
        -1.548,
        slits2.top.user_offset,
        -2.159,
        slits1.inboard.user_offset,
        -0.273,
        slits1.outboard.user_offset,
        -2.2050,
        slits1.top.user_offset,
        -1.54,
        slits1.bottom.user_offset,
        -0.86,
    )
