import numpy as np

from ..startup import RE

import bluesky.plan_stubs as bps
from nbs_bl.printing import run_report
from nbs_bl.hw import (
    mir1,
    en,
    mir3,
    psh10,
    Exit_Slit,
    slits1,
    Shutter_Y,
    Izero_Y,
    slits2,
    slits3,
    Det_W,
    #Det_S,
    BeamStopS,
    BeamStopW,
    sam_Th,
    sam_Z,
    sam_Y,
    sam_X,
    TEMZ,
    mir4OLD,
    dm7
)

from ..HW.energy import mono_en, grating_to_1200




def load_configuration(configuration_name):
    yield from move_motors(configuration_name)

    if "NEXAFS" in configuration_name:
        mdToUpdate = {
            "RSoXS_Config": configuration_name,
            "RSoXS_Main_DET": "Beamstop_WAXS",
            "RSoXS_WAXS_SDD": None,
            "RSoXS_WAXS_BCX": None,
            "RSoXS_WAXS_BCY": None,
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        }
        RE.md.update(mdToUpdate)
    
    else:
        mdToUpdate = {
            "RSoXS_Config": "WAXS_OpenBeamImages",
            "RSoXS_Main_DET": "WAXS",
            "RSoXS_WAXS_SDD": 39.19,
            "RSoXS_WAXS_BCX": 467.5,
            "RSoXS_WAXS_BCY": 513.4,
            "WAXS_Mask": [(367, 545), (406, 578), (880, 0), (810, 0)],
            "RSoXS_SAXS_SDD": None,
            "RSoXS_SAXS_BCX": None,
            "RSoXS_SAXS_BCY": None,
        }
        RE.md.update(mdToUpdate)


def move_motors(configuration_name):
    ## configuration is a string that is a key in the default_configurations dictionary
    configuration_setpoints = default_configurations[configuration_name]
    
    ## Sort by order
    configuration_setpoints_sorted = sorted(configuration_setpoints, key=lambda x: x["order"])
    
    ## Then move in that order
    for order in np.arange(0, int(configuration_setpoints_sorted[-1]["order"] + 1), 1):
        move_list = []
        for indexMotor, motor in enumerate(configuration_setpoints_sorted):
            if motor["order"] == order: move_list.extend([motor["motor"], motor["position"]])
        yield from bps.mv(*move_list)


## TODO: this is an example of a function I would want available in bsui_local, but wouldn't be available on a personal computer
def view_positions(configuration_name):
    ## Prints positions of motors in that configuration without moving anything
    configuration_setpoints = default_configurations[configuration_name]
    for indexMotor, motor in enumerate(configuration_setpoints):
        print(motor["motor"].read())



position_RSoXSDiagnosticModule_OutOfBeamPath = 145
position_RSoXSSlitAperture_FullyOpen = 10
position_BeamstopWAXS_InBeamPath = 69.6  ## Out is 3
position_CameraWAXS_InBeamPath = 2
position_CameraWAXS_OutOfBeamPath = -94


default_configurations = {

    "NoBeam": [
        {"motor": slits1.vsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits1.hsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits2.vsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits2.hsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits3.vsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits3.hsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
    ],


    "MirrorConfiguration_RSoXS": [
        {"motor": mir1.x, "position": -0.55, "order": 0},
        {"motor": mir1.y, "position": -18, "order": 1},
        {"motor": mir1.z, "position": 0, "order": 2},
        {"motor": mir1.pitch, "position": 0.45, "order": 3},
        {"motor": mir1.roll, "position": 0, "order": 4},
        {"motor": mir1.yaw, "position": 0, "order": 5},

        {"motor": mir3.x, "position": 22.1, "order": 0},
        {"motor": mir3.y, "position": 18, "order": 1},
        {"motor": mir3.z, "position": 0, "order": 2},
        {"motor": mir3.pitch, "position": 7.93, "order": 3},
        {"motor": mir3.roll, "position": 0, "order": 4},
        {"motor": mir3.yaw, "position": 0, "order": 5},
    ],


    "WAXS_OpenBeamImages": [
        {"motor": en, "position": 150, "order": 0},
        {"motor": Exit_Slit, "position": -0.01, "order": 0},
        {"motor": Izero_Y, "position": position_RSoXSDiagnosticModule_OutOfBeamPath, "order": 0},
        {"motor": Shutter_Y, "position": 2.2, "order": 0},
        {"motor": slits1.vsize, "position": 0.02, "order": 0},
        {"motor": slits1.vcenter, "position": -0.55, "order": 0},
        {"motor": slits1.hsize, "position": 0.04, "order": 0},
        {"motor": slits1.hcenter, "position": -0.18, "order": 0},
        {"motor": slits2.vsize, "position":  position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits2.vcenter, "position": -0.873, "order": 0},
        {"motor": slits2.hsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits2.hcenter, "position": -0.1, "order": 0},
        {"motor": slits3.vsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits3.vcenter, "position": -0.45, "order": 0},
        {"motor": slits3.hsize, "position": position_RSoXSSlitAperture_FullyOpen, "order": 0},
        {"motor": slits3.hcenter, "position": 0.15, "order": 0},
        {"motor": BeamStopW, "position": position_BeamstopWAXS_InBeamPath, "order": 1},
        {"motor": Det_W, "position": position_CameraWAXS_InBeamPath, "order": 1},
    ],

    "WAXSNEXAFS": [
        {"motor": TEMZ, "position": 1, "order": 0},
        {"motor": slits1.vsize, "position": 0.02, "order": 0},
        {"motor": slits1.vcenter, "position": -0.55, "order": 0},
        {"motor": slits1.hsize, "position": 0.04, "order": 0},
        {"motor": slits1.hcenter, "position": -0.18, "order": 0},
        {"motor": slits2.vsize, "position":  0.21, "order": 0},
        {"motor": slits2.vcenter, "position": -0.873, "order": 0},
        {"motor": slits2.hsize, "position": 0.4, "order": 0},
        {"motor": slits2.hcenter, "position": -0.1, "order": 0},
        {"motor": slits3.vsize, "position": 1, "order": 0},
        {"motor": slits3.vcenter, "position": -0.45, "order": 0},
        {"motor": slits3.hsize, "position": 1, "order": 0},
        {"motor": slits3.hcenter, "position": 0.15, "order": 0},
        {"motor": Shutter_Y, "position": 2.2, "order": 0},
        {"motor": Izero_Y, "position": -31, "order": 0},
        {"motor": Det_W, "position": position_CameraWAXS_OutOfBeamPath, "order": 1},
        {"motor": BeamStopW, "position": position_BeamstopWAXS_InBeamPath, "order": 1},
        {"motor": Exit_Slit, "position": -3.05, "order": 2},
    ],

    "WAXS": [
        {"motor": TEMZ, "position": 1, "order": 0},
        {"motor": slits1.vsize, "position": 0.02, "order": 0},
        {"motor": slits1.vcenter, "position": -0.55, "order": 0},
        {"motor": slits1.hsize, "position": 0.04, "order": 0},
        {"motor": slits1.hcenter, "position": -0.18, "order": 0},
        {"motor": slits2.vsize, "position":  0.21, "order": 0},
        {"motor": slits2.vcenter, "position": -0.873, "order": 0},
        {"motor": slits2.hsize, "position": 0.4, "order": 0},
        {"motor": slits2.hcenter, "position": -0.1, "order": 0},
        {"motor": slits3.vsize, "position": 1, "order": 0},
        {"motor": slits3.vcenter, "position": -0.45, "order": 0},
        {"motor": slits3.hsize, "position": 1, "order": 0},
        {"motor": slits3.hcenter, "position": 0.15, "order": 0},
        {"motor": Shutter_Y, "position": 2.2, "order": 0},
        {"motor": Izero_Y, "position": -31, "order": 0},
        {"motor": Det_W, "position": position_CameraWAXS_InBeamPath, "order": 1},
        {"motor": BeamStopW, "position": position_BeamstopWAXS_InBeamPath, "order": 1},
        {"motor": Exit_Slit, "position": -3.05, "order": 2},
    ],
    
}


def all_out():
    yield from psh10.close()
    print("Retracting Slits to 1 cm gap")
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
    print("Moving the rest of RSoXS components")
    yield from bps.mv(
        Shutter_Y,
        44,
        Izero_Y,
        144,
        Det_W,
        position_CameraWAXS_OutOfBeamPath,
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
        en.polarization, #TODO - remove this to another step with try except for PV access error
        0,
        Exit_Slit,
        -0.05,
        TEMZ,
        1
        #dm7, ## PK 20240625 - commenting out because it throws an error while running nmode #TODO - check with cherno about moving mirror 4 back as well
        #80 ## PK 20240528: Changed from -80 to 80 because while running nmode, I got LimitError.  I think the negative sign is a typo and DM7 is supposed to move up to get out of the way.
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

