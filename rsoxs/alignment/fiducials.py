import bluesky.plan_stubs as bps
from .fly_alignment import rsoxs_fly_max
from nbs_bl.hw import (
    Shutter_control,
    Shutter_enable,
    sam_X,
    sam_Y,
    sam_Th,
    sam_Z,
    Beamstop_WAXS_int,
)
from ..Functions.alignment import load_configuration, rsoxs_config, correct_bar


## For now, mostly pasting Eliot's fly_find-fiducials, but updating the fly_max function that is used for testing purposes
def fly_find_fiducials2(f2=[3.5, -1, -2.4, 1.5], f1=[2.0, -0.9, -1.5, 0.8], y1=-187.5, y2=2):
    thoffset = 0
    angles = [-90 + thoffset, 0 + thoffset, 90 + thoffset, 180 + thoffset]
    xrange = 3.5
    startxss = [f2, f1]
    yield from bps.mv(Shutter_enable, 0)
    yield from bps.mv(Shutter_control, 0)
    yield from load_configuration("WAXSNEXAFS")
    Beamstop_WAXS_int.kind = "hinted"
    # bec.enable_plots()
    startys = [y2, y1]  # af2 first because it is a safer location
    maxlocs = []
    for startxs, starty in zip(startxss, startys):
        yield from bps.mv(sam_Y, starty, sam_X, startxs[1], sam_Th, 0, sam_Z, 0)
        peaklist = []
        yield from rsoxs_fly_max(
            [Beamstop_WAXS_int],
            sam_Y,
            starty - 1,
            starty + 1,
            velocities=[0.2],
            open_shutter=True,
            peaklist=peaklist,
        )
        maxlocs.append(peaklist[-1]["WAXS Beamstop"]["manipulator_y"])
        yield from bps.mv(sam_Y, peaklist[-1]["WAXS Beamstop"]["manipulator_y"])
        for startx, angle in zip(startxs, angles):
            yield from bps.mv(sam_X, startx, sam_Th, angle)
            yield from bps.mv(Shutter_control, 1)
            peaklist = []
            yield from rsoxs_fly_max(
                [Beamstop_WAXS_int],
                sam_X,
                startx - 0.5 * xrange,
                startx + 0.5 * xrange,
                velocities=[0.2],
                open_shutter=True,
                peaklist=peaklist,
            )
            maxlocs.append(peaklist[-1]["WAXS Beamstop"]["manipulator_x"])
    print(maxlocs)  # [af2y,af2xm90,af2x0,af2x90,af2x180,af1y,af1xm90,af1x0,af1x90,af1x180]
    accept = input(f"Do you want to apply this correction (y,n)?")
    if accept in ["y", "Y", "yes"]:
        back = False
        for samp in rsoxs_config["bar"]:
            if samp["front"] == False:
                back = True
        correct_bar(maxlocs, include_back=back)
    # bec.disable_plots()
