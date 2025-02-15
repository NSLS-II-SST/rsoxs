import numpy as np

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


def move_motors(configuration_name):
    ## configuration is a string that is a key in the default_configurations dictionary
    configuration_setpoints = default_configurations[configuration_name]
    
    ## Sort by order
    configuration_setpoints_sorted = sorted(configuration_setpoints, key=lambda x: x["order"])
    
    ## Then move in that order
    for order in np.arange(0, int(configuration_setpoints_sorted[-1]["order"]), 1):
        move_list = []
        for indexMotor, motor in enumerate(configuration_setpoints_sorted):
            if motor["order"] == order: move_list.extend([motor["motor"], motor["position"]])
        yield from bps.mv(*move_list)


def view_positions(configuration_name):
    ## Prints positions of motors in that configuration without moving anything
    configuration_setpoints = default_configurations[configuration_name]
    for indexMotor, motor in enumerate(configuration_setpoints):
        print(motor["motor"].read())



default_configurations = {

    "NoBeam": [
        {"motor": slits1.vsize, "position": 10, "order": 0},
        {"motor": slits1.hsize, "position": 10, "order": 0},
        {"motor": slits2.vsize, "position": 10, "order": 0},
        {"motor": slits2.hsize, "position": 10, "order": 0},
        {"motor": slits3.vsize, "position": 10, "order": 0},
        {"motor": slits3.hsize, "position": 10, "order": 0},
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
    
}

