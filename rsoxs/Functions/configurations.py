import bluesky.plan_stubs as bps
from sst_funcs.printing import run_report
from ..HW.motors import (
    Shutter_Y,
    Izero_Y,
    Det_W,
    Det_S,
    BeamStopS,
    BeamStopW,
    sam_Th,
    sam_Z,
    sam_Y,
    sam_X,
)
from sst_hw.mirrors import mir1, mir3
from sst_hw.motors import Exit_Slit
from sst_hw.shutters import psh10
from ..HW.energy import en, mono_en, grating_to_1200
from ..HW.slits import slits1, slits2, slits3
from ..startup import RE

run_report(__file__)


# TODO lots of metadata manipulation here, and


def Shutter_in():
    yield from bps.mv(Shutter_Y, 2.2)


def Shutter_out():
    yield from bps.mv(Shutter_Y, 44)


def Izero_screen():
    yield from bps.mv(Izero_Y, 2)


def Izero_mesh():
    yield from bps.mv(Izero_Y, -29)


def Izero_diode():
    yield from bps.mv(Izero_Y, 35)


def Izero_out():
    yield from bps.mv(Izero_Y, 145)


def DetS_in():
    yield from bps.mv(Det_S, -15)


def DetS_edge():
    yield from bps.mv(Det_S, -50)


def DetS_out():
    yield from bps.mv(Det_S, -100)


def DetW_edge():
    yield from bps.mv(Det_W, -50)


def DetW_in():
    yield from bps.mv(Det_W, -10)


def DetW_out():
    yield from bps.mv(Det_W, -94)


def BSw_in():
    yield from bps.mv(BeamStopW, 71.4)


def BSw_out():
    yield from bps.mv(BeamStopW, 3)


def BSs_in():
    yield from bps.mv(BeamStopS, 67)


def BSs_out():
    yield from bps.mv(BeamStopS, 3)


def Detectors_out():
    yield from bps.mv(Det_S, -94, Det_W, -94)


def Detectors_edge():
    yield from bps.mv(Det_S, -50, Det_W, -50)


def BS_out():
    yield from bps.mv(BeamStopW, 3, BeamStopS, 3)


def slits_in_SAXS():
    yield from bps.mv(
        slits1.vsize,
        0.025,
        slits1.vcenter,
        -0.55,
        slits1.hsize,
        0.153,
        slits1.hcenter,
        0.7,
        slits2.vsize,
        0.4,
        slits2.vcenter,
        -0.9,
        slits2.hsize,
        0.5,
        slits2.hcenter,
        0.7,
        slits3.vsize,
        1,
        slits3.vcenter,
        -0.5,
        slits3.hsize,
        1,
        slits3.hcenter,
        0.9,
    )


def slits_out():
    yield from bps.mv(
        slits1.vsize,
        10,
        slits1.hsize,
        10,
        slits2.vsize,
        10,
        slits2.hsize,
        10,
        slits3.vsize,
        10,
        slits3.hsize,
        10,
    )


def slits_in_WAXS():
    yield from bps.mv(
        slits1.vsize,
        0.05,
        slits1.vcenter,
        -0.55,
        slits1.hsize,
        0.3,
        slits1.hcenter,
        0.55,
        slits2.vsize,
        0.45,
        slits2.vcenter,
        -1.05,
        slits2.hsize,
        0.5,
        slits2.hcenter,
        0.45,
        slits3.vsize,
        1.1,
        slits3.vcenter,
        -0.625,
        slits3.hsize,
        1.2,
        slits3.hcenter,
        0.55,
    )


def mirror3_NEXAFSpos():
    yield from bps.mv(mir3.Pitch, 8.04)
    yield from bps.sleep(3)
    yield from bps.mv(mir3.X, 27.9)
    yield from bps.sleep(3)
    yield from bps.mv(mir3.Y, 18.00)
    yield from bps.sleep(3)
    yield from bps.mv(mir3.Z, 0)
    yield from bps.sleep(3)
    yield from bps.mv(mir3.Roll, 0)
    yield from bps.sleep(3)
    yield from bps.mv(mir3.Yaw, 1)
    yield from bps.sleep(3)


def mirror_pos_NEXAFS():
    yield from bps.mv(mir1.Pitch, 0.66)
    yield from bps.mv(mir1.X, 0)
    yield from bps.mv(mir1.Y, -18)
    yield from bps.mv(mir1.Z, 0)
    yield from bps.mv(mir1.Roll, 3)
    yield from bps.mv(mir1.Yaw, 0)


def mirror_pos_rsoxs():
    yield from bps.mv(
        mir3.Pitch,
        7.92,
        mir3.X,
        26.5,
        mir3.Y,
        18,
        mir3.Z,
        0,
        mir3.Roll,
        0,
        mir3.Yaw,
        1,
        mir1.Pitch,
        0.7,
        mir1.X,
        0,
        mir1.Y,
        -18,
        mir1.Z,
        0,
        mir1.Roll,
        0,
        mir1.Yaw,
        0,
    )


def mirror1_NEXAFSpos():
    yield from bps.mv(
        mir3.Pitch,
        7.94,
        mir3.X,
        26.5,
        mir3.Y,
        18,
        mir3.Z,
        0,
        mir3.Roll,
        0,
        mir3.Yaw,
        1,
        mir1.Pitch,
        0.68,
        mir1.X,
        0,
        mir1.Y,
        -18,
        mir1.Z,
        0,
        mir1.Roll,
        0,
        mir1.Yaw,
        0,
    )


# SAXS slits for the new rsoxs grating
# ┌─── Upstream Scatter Slits ────────────────────────────────────────────────┐
# │      vertical   size   =   0.025 mm                                       │
# │      vertical   center =  -0.550 mm                                       │
# │      horizontal size   =   0.100 mm                                       │
# │      horizontal center =   0.700 mm                                       │
# └───────────────────────────────────────────────────────────────────────────┘
#
# RSoXS 2022-2/C-308244-NIST/Calibration/auto/2022-05-28/  [97]: slits2.wh()
# Middle Scatter Slits:
#
# ┌─── Middle Scatter Slits ──────────────────────────────────────────────────┐
# │      vertical   size   =   0.402 mm                                       │
# │      vertical   center =  -0.900 mm                                       │
# │      horizontal size   =   0.249 mm                                       │
# │      horizontal center =   0.648 mm                                       │
# └───────────────────────────────────────────────────────────────────────────┘
#
# RSoXS 2022-2/C-308244-NIST/Calibration/auto/2022-05-28/  [98]: slits3.wh()
# Final Scatter Slits:
#
# ┌─── Final Scatter Slits ───────────────────────────────────────────────────┐
# │      vertical   size   =   0.900 mm                                       │
# │      vertical   center =  -0.400 mm                                       │
# │      horizontal size   =   0.849 mm                                       │
# │      horizontal center =   0.900 mm
def SAXS():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 0.9, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 0.85, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 0},
            {"motor": Det_W, "position": -94, "order": 0},
            {"motor": Det_S, "position": -15, "order": 0},
            {"motor": BeamStopS, "position": 67.7, "order": 0},
            {"motor": BeamStopW, "position": 3, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "SAXS",
            "RSoXS_Main_DET": "SAXS",
            "SAXS_Mask": [(473, 472), (510, 471), (515, 1024), (476, 1024)],
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": 516,
            "RSoXS_SAXS_BCX": 493.4,
            "RSoXS_SAXS_BCY": 514.4,
        },
    ]


def SAXSNEXAFS():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 0.9, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 0.85, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 0},
            {"motor": Det_W, "position": -94, "order": 0},
            {"motor": Det_S, "position": -100, "order": 0},
            {"motor": BeamStopS, "position": 67.7, "order": 0},
            {"motor": BeamStopW, "position": 3, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "SAXSNEXAFS",
            "RSoXS_Main_DET": "Beamstop_SAXS",
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        },
    ]


def WAXSNEXAFS():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 0.9, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 0.85, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 0},
            {"motor": Det_W, "position": -94, "order": 1},
            {"motor": Det_S, "position": -100, "order": 1},
            {"motor": BeamStopW, "position": 71.4, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "WAXSNEXAFS",
            "RSoXS_Main_DET": "Beamstop_WAXS",
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        },
    ]


def WAXS():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 0.9, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 0.85, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 1},
            {"motor": Det_W, "position": -10, "order": 1},
            {"motor": BeamStopW, "position": 71.4, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "WAXS",
            "RSoXS_Main_DET": "WAXS",
            "RSoXS_WAXS_SDD": 39.19,
            "RSoXS_WAXS_BCX": 396.341,
            "RSoXS_WAXS_BCY": 549.99,
            "WAXS_Mask": [(367, 545), (406, 578), (880, 0), (810, 0)],
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        },
    ]


def SAXS_liquid():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 1.4, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 1.35, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 0},
            {"motor": Det_W, "position": -94, "order": 0},
            {"motor": Det_S, "position": -15, "order": 0},
            {"motor": BeamStopS, "position": 67.7, "order": 0},
            {"motor": BeamStopW, "position": 3, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "SAXS",
            "RSoXS_Main_DET": "SAXS",
            "SAXS_Mask": [(473, 472), (510, 471), (515, 1024), (476, 1024)],
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": 516,
            "RSoXS_SAXS_BCX": 493.4,
            "RSoXS_SAXS_BCY": 514.4,
        },
    ]


def WAXS_liquid():
    return [
        [
            {"motor": slits1.vsize, "position": 0.025, "order": 0},
            {"motor": slits1.vcenter, "position": -0.55, "order": 0},
            {"motor": slits1.hsize, "position": 0.1, "order": 0},
            {"motor": slits1.hcenter, "position": 0.7, "order": 0},
            {"motor": slits2.vsize, "position": 0.4, "order": 0},
            {"motor": slits2.vcenter, "position": -0.9, "order": 0},
            {"motor": slits2.hsize, "position": 0.25, "order": 0},
            {"motor": slits2.hcenter, "position": 0.65, "order": 0},
            {"motor": slits3.vsize, "position": 1.9, "order": 0},
            {"motor": slits3.vcenter, "position": -0.4, "order": 0},
            {"motor": slits3.hsize, "position": 1.35, "order": 0},
            {"motor": slits3.hcenter, "position": 0.9, "order": 0},
            {"motor": Shutter_Y, "position": 2.2, "order": 0},
            {"motor": Izero_Y, "position": -29, "order": 1},
            {"motor": Det_W, "position": -10, "order": 1},
            {"motor": BeamStopW, "position": 71.4, "order": 1},
            {"motor": Exit_Slit, "position": -3.05, "order": 2},
        ],
        {
            "RSoXS_Config": "WAXS",
            "RSoXS_Main_DET": "WAXS",
            "RSoXS_WAXS_SDD": 39.19,
            "RSoXS_WAXS_BCX": 396.341,
            "RSoXS_WAXS_BCY": 549.99,
            "WAXS_Mask": [(367, 545), (406, 578), (880, 0), (810, 0)],
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        },
    ]



def all_out():
    yield from psh10.close()
    print("Retracting Slits to 1 cm gap")
    yield from slits_out()
    print("Moving the rest of RSoXS components")
    yield from bps.mv(
        Shutter_Y,
        44,
        Izero_Y,
        144,
        Det_W,
        -94,
        Det_S,
        -100,
        BeamStopW,
        3,
        BeamStopS,
        3,
        sam_Y,
        345,
        sam_X,
        0,
        sam_Z,
        0,
        sam_Th,
        0,
        en.polarization,
        0,
        Exit_Slit,
        -0.05,
    )
    print("moving back to 1200 l/mm grating")
    yield from grating_to_1200()
    print("resetting cff to 2.0")
    yield from bps.mv(mono_en.cff, 2)
    print("moving to 270 eV")
    yield from bps.mv(en, 270)
    RE.md.update(
        {
            "RSoXS_Config": "inactive",
            "RSoXS_Main_DET": None,
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        }
    )
    print("All done - Happy NEXAFSing")
