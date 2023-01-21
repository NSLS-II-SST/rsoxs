import bluesky.plans as bp
from matplotlib import pyplot as plt
import queue
from PIL import Image
from operator import itemgetter
from copy import deepcopy
import collections
import numpy as np
import datetime
import bluesky.plan_stubs as bps
from ophyd import Device
from ..startup import RE, db, bec, db0
from ..HW.motors import sam_viewer
from ..HW.cameras import SampleViewer_cam
from sst_hw.diode import Shutter_enable, Shutter_control
from ..HW.signals import Beamstop_SAXS, Beamstop_WAXS, DiodeRange
from ..HW.detectors import saxs_det, waxs_det, set_exposure
from sst_hw.shutters import psh10
from ..HW.energy import en, set_polarization, grating_to_1200, grating_to_250, grating_to_rsoxs
from sst_funcs.printing import run_report
from ..HW.slackbot import rsoxs_bot
from ..HW.motors import (
    sam_X,
    sam_Y,
    sam_Th,
    sam_Z,
    Shutter_Y,
    Izero_Y,
    Det_S,
    Det_W,
    BeamStopW,
    BeamStopS,
    TEMX,
    TEMY,
    TEMZ,
)
from . import configurations
from ..HW.slits import slits1, slits2, slits3
from sst_hw.motors import Exit_Slit
from sst_funcs.printing import boxed_text, colored
from .common_functions import args_to_string
from .configurations import (
    WAXSNEXAFS,
    WAXS,
    SAXS,
    SAXSNEXAFS,
    SAXS_liquid,
    WAXS_liquid,
)

run_report(__file__)


def user():
    title = "User metadata - stored in every scan:"
    text = ""
    if len(f'{RE.md["proposal_id"]}') > 0:
        text += "   proposal ID:           " + colored(
            "{}".format(str(RE.md["proposal_id"])).center(50, " "), "yellow"
        )
    if len(str(RE.md["SAF"])) > 0:
        text += "\n   SAF ID:              " + colored("{}".format(str(RE.md["SAF"])).center(50, " "), "yellow")
    if len(RE.md["user_name"]) > 0:
        text += "\n   User Name:           " + colored("{}".format(RE.md["user_name"]).center(50, " "), "yellow")
    if len(RE.md["user_email"]) > 0:
        text += "\n   User Email:          " + colored("{}".format(RE.md["user_name"]).center(50, " "), "yellow")
    if len(RE.md["user_id"]) > 0:
        text += "\n   User ID:             " + colored(
            "{}".format(str(RE.md["user_id"])).center(50, " "), "yellow"
        )
    if len(RE.md["institution"]) > 0:
        text += "\n   Institution:         " + colored("{}".format(RE.md["institution"]).center(50, " "), "yellow")
    if len(RE.md["project_name"]) > 0:
        text += "\n   project:             " + colored(
            "{}".format(RE.md["project_name"]).center(50, " "), "yellow"
        )
    if len(RE.md["project_desc"]) > 0:
        text += "\n   Project Description: " + colored(
            "{}".format(RE.md["project_desc"]).center(50, " "), "yellow"
        )
    boxed_text(title, text, "green", 80, shrink=False)


def sample():
    title = "Sample metadata - stored in every scan:"
    text = ""
    if len(str(RE.md["proposal_id"])) > 0:
        text += "   proposal ID:           " + colored("{}".format(RE.md["proposal_id"]).center(48, " "), "cyan")
    if len(str(RE.md["SAF"])) > 0:
        text += "\n   SAF id:                " + colored("{}".format(RE.md["SAF"]).center(48, " "), "cyan")
    if len(str(RE.md["user_name"])) > 0:
        text += "\n   User Name:             " + colored("{}".format(RE.md["user_name"]).center(48, " "), "cyan")
    if len(str(RE.md["institution"])) > 0:
        text += "\n   Institution:           " + colored("{}".format(RE.md["institution"]).center(48, " "), "cyan")
    if len(str(RE.md["sample_name"])) > 0:
        text += "\n   Sample Name:           " + colored("{}".format(RE.md["sample_name"]).center(48, " "), "cyan")
    if len(str(RE.md["sample_priority"])) > 0:
        text += "\n   Sample Priority:       " + colored(
            "{}".format(RE.md["sample_priority"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["sample_desc"])) > 0:
        text += "\n   Sample Description:    " + colored("{}".format(RE.md["sample_desc"]).center(48, " "), "cyan")
    if len(str(RE.md["sample_id"])) > 0:
        text += "\n   Sample ID:             " + colored(
            "{}".format(str(RE.md["sample_id"])).center(48, " "), "cyan"
        )
    if len(str(RE.md["sample_set"])) > 0:
        text += "\n   Sample Set:            " + colored("{}".format(RE.md["sample_set"]).center(48, " "), "cyan")
    if len(str(RE.md["sample_date"])) > 0:
        text += "\n   Sample Creation Date:  " + colored("{}".format(RE.md["sample_date"]).center(48, " "), "cyan")
    if len(str(RE.md["project_name"])) > 0:
        text += "\n   Project name:          " + colored(
            "{}".format(RE.md["project_name"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["project_desc"])) > 0:
        text += "\n   Project Description:   " + colored(
            "{}".format(RE.md["project_desc"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["samp_user_id"])) > 0:
        text += "\n   Creator User ID:       " + colored(
            "{}".format(str(RE.md["samp_user_id"])).center(48, " "), "cyan"
        )
    if len(str(RE.md["bar_loc"]["spot"])) > 0:
        text += "\n   Location on Bar:       " + colored(
            "{}".format(RE.md["bar_loc"]["spot"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["bar_loc"]["th"])) > 0:
        text += "\n   Angle of incidence:    " + colored(
            "{}".format(RE.md["bar_loc"]["th"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["composition"])) > 0:
        text += "\n   Composition(formula):  " + colored("{}".format(RE.md["composition"]).center(48, " "), "cyan")
    if len(str(RE.md["density"])) > 0:
        text += "\n   Density:               " + colored(
            "{}".format(str(RE.md["density"])).center(48, " "), "cyan"
        )
    if len(str(RE.md["components"])) > 0:
        text += "\n   List of Components:    " + colored("{}".format(RE.md["components"]).center(48, " "), "cyan")
    if len(str(RE.md["thickness"])) > 0:
        text += "\n   Thickness:             " + colored(
            "{}".format(str(RE.md["thickness"])).center(48, " "), "cyan"
        )
    if len(str(RE.md["sample_state"])) > 0:
        text += "\n   Sample state:          " + colored(
            "{}".format(RE.md["sample_state"]).center(48, " "), "cyan"
        )
    if len(str(RE.md["notes"])) > 0:
        text += "\n   Notes:                 " + colored("{}".format(RE.md["notes"]).center(48, " "), "cyan")
    boxed_text(title, text, "red", 80, shrink=False)


def newuser():
    print(
        "This information will tag future data until this changes, please be as thorough as possible\n"
        "current values in parentheses, leave blank for no change"
    )

    proposal_id = input("Your proposal id ({}): ".format(RE.md["proposal_id"]))
    if proposal_id != "":
        RE.md["proposal_id"] = proposal_id

    SAF_id = input("Your SAF id ({}): ".format(RE.md["SAF"]))
    if SAF_id != "":
        RE.md["SAF"] = SAF_id

    institution = input("Your institution ({}): ".format(RE.md["institution"]))
    if institution != "":
        RE.md["institution"] = institution

    user_name = input("Your name ({}): ".format(RE.md["user_name"]))
    if user_name != "":
        RE.md["user_name"] = user_name

    user_email = input("Your email for beamline status notifications ({}): ".format(RE.md["user_email"]))
    if user_email != "":
        RE.md["user_email"] = user_email

    project_name = input("Your project ({}): ".format(RE.md["project_name"]))
    if project_name != "":
        RE.md["project_name"] = project_name

    project_desc = input("Your project description ({}): ".format(RE.md["project_desc"]))
    if project_desc != "":
        RE.md["project_desc"] = project_desc
    # if new, add user to database get unique ID.
    user_id = "0"
    RE.md["user_id"] = user_id
    user()
    return user_dict()


def get_location(motor_list):
    locs = []
    for motor in motor_list:
        locs.append({"motor": motor, "position": motor.user_readback.get(), "order": 0})
    return locs


def sample_set_location(sample_dict):
    sample_dict["location"] = get_sample_location()  # set the location metadata
    sample_recenter_sample(
        sample_dict
    )  # change the x0, y0, theta to result in this new position (including angle)
    return sample_dict


def get_sample_location():
    locs = []
    locs.append({"motor": "x", "position": sam_X.user_readback.get(), "order": 0})
    locs.append({"motor": "y", "position": sam_Y.user_readback.get(), "order": 0})
    locs.append({"motor": "z", "position": sam_Z.user_readback.get(), "order": 0})
    locs.append({"motor": "th", "position": sam_Th.user_readback.get(), "order": 0})
    #  locs = get_location([sam_X,sam_Y,sam_Z,sam_Th])
    return locs


def move_to_location(locs=get_sample_location()):
    for item in locs:
        item.setdefault("order", 0)
    locs = sorted(locs, key=itemgetter("order"))
    orderlist = [o for o in collections.Counter([d["order"] for d in locs]).keys()]

    switch = {
        "x": sam_X,
        "y": sam_Y,
        "z": sam_Z,
        "th": sam_Th,
        sam_X: sam_X,
        sam_Y: sam_Y,
        sam_Z: sam_Z,
        sam_Th: sam_Th,
        slits1.vsize: slits1.vsize,
        slits1.hsize: slits1.hsize,
        slits2.vsize: slits2.vsize,
        slits2.hsize: slits2.hsize,
        slits3.vsize: slits3.vsize,
        slits3.hsize: slits3.hsize,
        slits1.vcenter: slits1.vcenter,
        slits1.hcenter: slits1.hcenter,
        slits2.vcenter: slits2.vcenter,
        slits2.hcenter: slits2.hcenter,
        slits3.vcenter: slits3.vcenter,
        slits3.hcenter: slits3.hcenter,
        Shutter_Y: Shutter_Y,
        Izero_Y: Izero_Y,
        Det_W: Det_W,
        Det_S: Det_S,
        BeamStopS: BeamStopS,
        BeamStopW: BeamStopW,
        Exit_Slit: Exit_Slit,
    }
    for order in orderlist:
        outputlist = [
            [switch[items["motor"]], float(items["position"])] for items in locs if items["order"] == order
        ]
        flat_list = [item for sublist in outputlist for item in sublist]
        yield from bps.mv(*flat_list)


def get_location_from_config(config):
    config_func = getattr(configurations, config)
    return config_func()[0]


def get_md_from_config(config):
    config_func = getattr(configurations, config)
    return config_func()[1]


def load_configuration(config, sim_mode=False):
    """
    :param config: string containing a name of a configuration
    :return:
    """
    if sim_mode:
        return f"moved to {config} configuration"
    yield from move_to_location(get_location_from_config(config))
    RE.md.update(get_md_from_config(config))


def get_sample_dict(acq=[], locations=None):
    if locations is None:
        locations = get_sample_location()
    sample_name = RE.md["sample_name"]
    sample_priority = RE.md["sample_priority"]
    sample_desc = RE.md["sample_desc"]
    sample_id = RE.md["sample_id"]
    sample_set = RE.md["sample_set"]
    sample_date = RE.md["sample_date"]
    project_name = RE.md["project_name"]
    proposal_id = RE.md["proposal_id"]
    saf_id = RE.md["SAF"]
    institution = RE.md["institution"]
    project_desc = RE.md["project_desc"]
    samp_user_id = RE.md["samp_user_id"]
    composition = RE.md["composition"]
    bar_loc = RE.md["bar_loc"]
    density = RE.md["density"]
    grazing = RE.md["grazing"]
    bar_spot = RE.md["bar_spot"]
    front = RE.md["front"]
    height = RE.md["height"]
    angle = RE.md["angle"]
    components = RE.md["components"]
    thickness = RE.md["thickness"]
    sample_state = RE.md["sample_state"]
    notes = RE.md["notes"]

    return {
        "sample_name": sample_name,
        "sample_desc": sample_desc,
        "sample_id": sample_id,
        "sample_priority": sample_priority,
        "proposal_id": proposal_id,
        "SAF": saf_id,
        "institution": institution,
        "sample_set": sample_set,
        "sample_date": sample_date,
        "project_name": project_name,
        "project_desc": project_desc,
        "samp_user_id": samp_user_id,
        "composition": composition,
        "bar_loc": bar_loc,
        "density": density,
        "grazing": grazing,
        "bar_spot": bar_spot,
        "front": front,
        "height": height,
        "angle": angle,
        "components": components,
        "thickness": thickness,
        "sample_state": sample_state,
        "notes": notes,
        "location": locations,
        "acquisitions": acq,
    }


def user_dict(
    user_id=RE.md["user_id"],
    proposal_id=RE.md["proposal_id"],
    saf_id=RE.md["SAF"],
    institution=RE.md["institution"],
    user_name=RE.md["user_name"],
    project_name=RE.md["project_name"],
    project_desc=RE.md["project_desc"],
):
    return {
        "user_id": user_id,
        "proposal_id": proposal_id,
        "saf_id": saf_id,
        "institution": institution,
        "user_name": user_name,
        "project_name": project_name,
        "project_desc": project_desc,
    }


def load_sample(sam_dict, sim_mode=False):
    """
    move to a sample location and load the metadata with the sample information

    :param sam_dict: sample dictionary containing all metadata and sample location
    :return:
    """

    if sim_mode:
        return f"move to {sam_dict['sample_name']}"
    RE.md.update(sam_dict)
    yield from move_to_location(locs=sam_dict["location"])
    yield from bps.sleep(0)


def load_user_dict_to_md(user_dict):
    RE.md.update(user_dict)


def newsample():
    """
    ceate a new sample dictionary interactively

    :return: a sample dictionary
    """
    print(
        "This information will tag future data until this changes, please be as thorough as possible\n"
        "current values in parentheses, leave blank for no change"
    )
    sample_name = input("Your sample name  - be concise ({}): ".format(RE.md["sample_name"]))
    if sample_name != "":
        RE.md["sample_name"] = sample_name

    sample_priority = input(
        "Your sample priority  - 0 - highest to 100-lowest ({}): ".format(RE.md["sample_priority"])
    )
    if sample_priority != "":
        RE.md["sample_priority"] = sample_priority

    sample_desc = input("Describe your sample - be thorough ({}): ".format(RE.md["sample_desc"]))
    if sample_desc != "":
        RE.md["sample_desc"] = sample_desc

    sample_id = input("Your sample id - if you have one ({}): ".format(RE.md["sample_id"]))
    if sample_id != "":
        RE.md["sample_id"] = sample_id

    proposal_id = input("Your Proposal ID from PASS ({}): ".format(RE.md["proposal_id"]))
    if proposal_id != "":
        RE.md["proposal_id"] = proposal_id

    institution = input("Your Institution ({}): ".format(RE.md["institution"]))
    if institution != "":
        RE.md["institution"] = institution

    saf_id = input("Your SAF ID number from PASS ({}): ".format(RE.md["SAF"]))
    if saf_id != "":
        RE.md["SAF"] = saf_id

    sample_set = input("What set does this sample belong to ({}): ".format(RE.md["sample_set"]))
    if sample_set != "":
        RE.md["sample_set"] = sample_set

    sample_date = input("Sample creation date ({}): ".format(RE.md["sample_date"]))
    if sample_date != "":
        RE.md["sample_date"] = sample_date

    project_name = input("Is there an associated project name ({}): ".format(RE.md["project_name"]))
    if project_name != "":
        RE.md["project_name"] = project_name

    project_desc = input("Describe the project ({}): ".format(RE.md["project_desc"]))
    if project_desc != "":
        RE.md["project_desc"] = project_desc

    samp_user_id = input("Associated User ID ({}): ".format(RE.md["samp_user_id"]))
    if samp_user_id != "":
        RE.md["samp_user_id"] = samp_user_id

    bar_loc = input("Location on the Bar ({}): ".format(RE.md["bar_loc"]["spot"]))
    if bar_loc != "":
        RE.md["bar_loc"]["spot"] = bar_loc
        RE.md["bar_spot"] = bar_loc

    th = input(
        "Angle desired for sample acquisition (-180 for transmission from back) ({}): ".format(
            RE.md["bar_loc"]["th"]
        )
    )
    if th != "":
        RE.md["bar_loc"]["th"] = float(th)
        RE.md["angle"] = float(th)

    composition = input("Sample composition or chemical formula ({}): ".format(RE.md["composition"]))
    if composition != "":
        RE.md["composition"] = composition

    density = input("Sample density ({}): ".format(RE.md["density"]))
    if density != "":
        RE.md["density"] = density

    components = input("Sample components ({}): ".format(RE.md["components"]))
    if components != "":
        RE.md["components"] = components

    thickness = input("Sample thickness ({}): ".format(RE.md["thickness"]))
    if thickness != "":
        RE.md["thickness"] = thickness

    sample_state = input('Sample state "Broken/Fresh" ({}): '.format(RE.md["sample_state"]))
    if sample_state != "":
        RE.md["sample_state"] = sample_state

    notes = input("Sample notes ({}): ".format(RE.md["notes"]))
    if notes != "":
        RE.md["notes"] = notes

    grazing = input("Is the sample for grazing incidence? ({}): ".format(RE.md["grazing"]))
    if grazing != "":
        RE.md["grazing"] = bool(grazing)
    front = input("Is the sample on the front of the bar? ({}): ".format(RE.md["front"]))
    if front != "":
        RE.md["front"] = bool(front)
    height = input("Sample height? ({}): ".format(RE.md["height"]))
    if height != "":
        RE.md["height"] = float(height)

    RE.md["acquisitions"] = []

    loc = input(
        "New Location? (if blank use current location x={:.2f},y={:.2f},z={:.2f},th={:.2f}): ".format(
            sam_X.user_readback.get(),
            sam_Y.user_readback.get(),
            sam_Z.user_readback.get(),
            sam_Th.user_readback.get(),
        )
    )
    if loc is not "":
        locs = []
        xval = input("X ({:.2f}): ".format(sam_X.user_readback.get()))
        if xval != "":
            locs.append({"motor": "x", "position": xval, "order": 0})
        else:
            locs.append({"motor": "x", "position": sam_X.user_readback.get(), "order": 0})
        yval = input("Y ({:.2f}): ".format(sam_Y.user_readback.get()))
        if yval != "":
            locs.append({"motor": "y", "position": yval, "order": 0})
        else:
            locs.append({"motor": "y", "position": sam_Y.user_readback.get(), "order": 0})

        zval = input("Z ({:.2f}): ".format(sam_Z.user_readback.get()))
        if zval != "":
            locs.append({"motor": "z", "position": zval, "order": 0})
        else:
            locs.append({"motor": "z", "position": sam_Z.user_readback.get(), "order": 0})

        thval = input("Theta ({:.2f}): ".format(sam_Th.user_readback.get()))
        if thval != "":
            locs.append({"motor": "th", "position": thval, "order": 0})
        else:
            locs.append({"motor": "th", "position": sam_Th.user_readback.get(), "order": 0})
        return get_sample_dict(locations=locs, acq=[])
    else:
        return get_sample_dict(acq=[])  # uses current location by default


def list_samples(bar):
    text = "  i  Sample Name"
    for index, sample in enumerate(bar):
        text += "\n {} {}".format(index, sample["sample_name"])
        acqs = bar[index]["acquisitions"]
        for acq in acqs:
            text += "\n   {} of {} in {} config, priority {}".format(
                acq["type"],
                acq["edge"],
                acq["configuration"],
                acq["priority"],
            )
    boxed_text("Samples on bar", text, "lightblue", shrink=False)


def sanatize_angle(samp, force=False):
    # translates a requested angle (something in sample['angle']) into an actual angle depending on the kind of sample
    if type(samp["angle"]) == int or type(samp["angle"]) == float:
        goodnumber = True  # make the number fall in the necessary range
    else:
        goodnumber = False  # make all transmission 90 degrees from the back, and all grading 20 deg
    if force and -155 < samp["angle"] < 195:
        samp["bar_loc"]["th"] = samp["angle"]
        return
    if samp["grazing"]:
        # the sample is intended for grazing incidence, so angles should be interpreted to mean
        # 0 - parallel with the face of the sample
        # 90 - normal to the sample
        # 110 - 20 degrees from normal in one direction
        # 70 - 20 degrees from normal in the other direction
        # valid input angles are 0 - 180
        if samp["front"]:
            # sample is on the front of the bar, so valid outputs are between -90 and 90
            if goodnumber:
                samp["bar_loc"]["th"] = float(90 - np.mod(samp["angle"] + 3600, 180))
            else:
                samp["bar_loc"]["th"] = 70  # default grazing incidence samples to 20 degrees incidence angle
                samp["angle"] = 70
                # front grazing sample angle is interpreted as grazing angle
        else:
            if goodnumber:
                angle = float(np.mod(435 - np.mod(-samp["angle"] + 3600, 180), 360) - 165)
                if angle < -155:
                    angle = float(np.mod(435 - np.mod(samp["angle"] + 3600, 180), 360) - 165)
                samp["bar_loc"]["th"] = angle
            else:
                samp["bar_loc"]["th"] = 110
                samp["angle"] = 110
            # back grazing sample angle is interpreted as grazing angle but subtracted from 180
    else:
        if samp["front"]:
            if goodnumber:
                samp["bar_loc"]["th"] = float(np.mod(345 - np.mod(90 + samp["angle"] + 3600, 180) + 90, 360) - 165)
                if samp["bar_loc"]["x0"] < -1.8 and np.abs(samp["angle"]) > 30:
                    # transmission from the left side of the bar at a incident angle more than 20 degrees,
                    # flip sample around to come from the other side - this can take a minute or two
                    samp["bar_loc"]["th"] = float(
                        np.mod(345 - np.mod(90 - samp["angle"] + 3600, 180) + 90, 360) - 165
                    )
                if samp["bar_loc"]["th"] >= 195:
                    samp["bar_loc"]["th"] = 180
                if samp["bar_loc"]["th"] <= -155:
                    samp["bar_loc"]["th"] = -150
            else:
                samp["bar_loc"]["th"] = 180
                samp["angle"] = 180
        else:
            if goodnumber:
                samp["bar_loc"]["th"] = float(np.mod(90 + samp["angle"] + 3600, 180) - 90)
                if samp["bar_loc"]["x0"] > -1.8 and np.abs(samp["angle"]) > 30:
                    # transmission from the right side of the bar at a incident angle more than 20 degrees,
                    # flip to come from the left side
                    samp["bar_loc"]["th"] = float(np.mod(90 - samp["angle"] + 3600, 180) - 90.0)
            else:
                samp["bar_loc"]["th"] = 0
                samp["angle"] = 0

    if samp["bar_loc"]["th"] >= 195:
        samp["bar_loc"]["th"] = 195.0
    if samp["bar_loc"]["th"] <= -155:
        samp["bar_loc"]["th"] = -155.0


def sample_by_value_match(bar, key, string):
    results = [d for (index, d) in enumerate(bar) if d[key].find(string) >= 0]
    if len(results) == 1:
        return results[0]
    elif len(results) < 1:
        print("No Match")
        return None
    elif len(results) > 1:
        print("More than one result found, returning them all")
        return results


def sample_by_name(bar, name):
    return sample_by_value_match(bar, "sample_name", name)


def alignment_rel_scan(det, motor, start_rel, end_rel, steps):
    savemd = RE.md.deepcopy()


def offset_bar(bar, xoff, yoff, zoff, thoff):
    for samp in bar:
        for mot in samp["location"]:
            if mot["motor"] == "x":
                mot["position"] += xoff
            if mot["motor"] == "y":
                mot["position"] += yoff
            if mot["motor"] == "z":
                mot["position"] += zoff
            if mot["motor"] == "th":
                mot["position"] += thoff
        sample_recenter_sample(samp)


def default_sample(name):
    return {
        "institution": "NIST",
        "acquisitions": [],
        "components": "",
        "composition": "",
        "bar_loc": {"spot": "A0"},
        "bar_spot": "0C",
        "front": True,
        "grazing": False,
        "height": 0.0,
        "angle": 90,
        "density": "",
        "location": [],
        "project_desc": "Calibration",
        "sample_id": name,
        "sample_name": name,
        "sample_desc": name,
        "project_name": "Calibration",
        "notes": "",
        "sample_set": "",
        "sample_state": "back",
    }


# Spiral searches


def samxscan():
    yield from psh10.open()
    yield from bp.rel_scan([Beamstop_SAXS], sam_X, -2, 2, 41)
    yield from psh10.close()


def spiralsearch(
    diameter=0.6,
    stepsize=0.2,
    energy=270,
    pol=0,
    angle=None,
    exposure=1,
    master_plan=None,
    enscan_type='spiral',
    dets=[],
    sim_mode=False,
    grating=None,
    md=None,
):
    """conduct a spiral grid pattern of exposures

    Parameters
    ----------
    diameter : float, optional
        _description_, by default 0.6
    stepsize : float, optional
        _description_, by default 0.2
    energy : int, optional
        _description_, by default 270
    pol : int, optional
        _description_, by default 0
    angle : _type_, optional
        _description_, by default None
    exposure : int, optional
        _description_, by default 1
    master_plan : _type_, optional
        _description_, by default None
    dets : list, optional
        _description_, by default []
    sim_mode : bool, optional
        _description_, by default False
    grating : _type_, optional
        _description_, by default None

    Returns
    -------
    _type_
        _description_

    Yields
    ------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    valid = True
    validation = ""
    newdets = []
    if md is None:
        md = {}
    arguments = dict(locals())
    del arguments["md"]  # no recursion here!
    md.setdefault("plan_history", [])
    md["plan_history"].append(
        {"plan_name": "spiralsearch", "arguments": arguments}
    )
    md.update({"plan_name": enscan_type, "master_plan": master_plan,'plan_args' :arguments })
    for det in dets:
        if not isinstance(det, Device):
            try:
                newdets.append(globals()[det])
            except Exception:
                valid = False
                validation += f"detector {det} is not an ophyd device\n"
    if len(newdets) < 1:
        valid = False
        validation += "No detectors are given\n"

    if angle is not None:
        if -155 > angle or angle > 195:
            valid = False
            validation += f"angle of {angle} is out of range\n"
    if sim_mode:
        if valid:
            retstr = f"scanning {newdets} at {energy} eV \n"
            retstr += f"    with a diameter of {diameter} mm  and stepsize of {stepsize} mm\n"
            return retstr
        else:
            return validation
    if grating not in [None, "1200", 1200, "250", 250, "rsoxs"]:
        valid = False
        validation = f"invalid choice of grating {grating}"
    if not valid:
        raise ValueError(validation)

    if grating in [1200, "1200"]:
        yield from grating_to_1200()
    elif grating in [250, "250"]:
        yield from grating_to_250()
    elif grating == "rsoxs":
        yield from grating_to_rsoxs()
    yield from bps.mv(en, energy)
    yield from set_polarization(pol)
    set_exposure(exposure)  # TODO: make this yield from ...
    x_center = sam_X.user_setpoint.get()
    y_center = sam_Y.user_setpoint.get()
    num = round(diameter / stepsize) + 1

    if angle is not None:
        print(f"moving angle to {angle}")
        yield from rotate_now(angle)

    yield from bp.spiral_square(
        newdets,
        sam_X,
        sam_Y,
        x_center=x_center,
        y_center=y_center,
        x_range=diameter,
        y_range=diameter,
        x_num=num,
        y_num=num,
        md={"plan_name": "spiralsearch", "master_plan": master_plan},
    )


def spiralsearch_all(barin=[], diameter=0.5, stepsize=0.2):
    for samp in barin:
        yield from load_sample(samp)
        RE.md["project_name"] = "spiral_searches"
        sample()
        rsoxs_bot.send_message(f'running spiral scan on {samp["proposal_id"]} {samp["sample_name"]}')
        yield from spiralsearch(diameter, stepsize, master_plan="spiralsearch_all")


def spiralsearchwaxs_all(barin=[], diameter=0.5, stepsize=0.2):
    for samp in barin:
        yield from load_sample(samp)
        RE.md["project_name"] = "spiral_searches"
        yield from spiralsearchwaxs(diameter, stepsize, master_plan="spiralsearchwaxs_all")


def map_bar_from_spirals(bar, num_previous_scans=150):
    """
    Interactively ask users to pick best location from spiral scans.
    will go through all samples on bar and try to find a matching spiral scan taken within the last
    hours defined by time_limit.
    Asking for the number of the best location
    @param bar: list of sample dictionaries
    @param num_previous_scans: number of previous scans to search backward
    @return: alters the locations of samples in bar if requested
    """
    samps = []
    scans = db0(plan_name="spiral_square")
    for i, sc in enumerate(scans):
        if "exit_status" in sc.stop.keys():
            if sc.stop["exit_status"] == "success":
                samps.append((sc.start["uid"], sc.start["sample_id"]))
            if i > num_previous_scans:
                break
    for samp in bar:
        uid = next(uid for (uid, sample_id) in samps if sample_id is samp["sample_id"])
        scan = db[uid]
        data = scan.table()
        print("Sample: " + samp["sample_name"])
        print(
            "Scan date: " + datetime.datetime.fromtimestamp(scan.start["time"]).strftime("%A, %B %d, %Y %I:%M:%S")
        )
        print("Enter good point number from spiral scan or anything non-numeric to skip:")
        good_point = input()
        if good_point.isnumeric():
            sam_x = data[good_point]["RSoXS Sample Outboard-Inboard"]
            sam_y = data[good_point]["RSoXS Sample Up-Down"]
            for mot in samp["location"]:
                if mot["motor"] == "x":
                    mot["position"] = sam_x
                if mot["motor"] == "y":
                    mot["position"] = sam_y
        else:
            print("Non-numeric, not touching this sample")


# Bar imaging utilities:

# usage:

# load bar onto imager, load bar file, and do image_bar(bar,path='path_to_image')

# this will automatically go into image tagging, but to pick up where you left off, do

# locate_samples_from_image(bar,'path_to_image')

# Find alignment fiducials in chamber
#
# Helpful Functions goto_af1() goto_af2() and find_af1x(),find_af1y(),find_af2x(),find_af2y()
#
# and then remap the bar using
# correct_bar(bar,af1x,af1y,af2x,af2y)


def image_bar(bar, path=None, front=True):
    global loc_Q
    loc_Q = queue.Queue(1)
    ypos = np.arange(-100, 110, 25)
    images = []

    imageuid = yield from bp.list_scan([SampleViewer_cam], sam_viewer, ypos)
    print(imageuid)
    images = list(db[imageuid].data("Sample Imager Detector Area Camera_image"))
    image = stitch_sample(images, 25, -6)  # this will start the interactive pointing of samples
    if isinstance(path, str):
        im = Image.fromarray(image)
        im.save(path)
    update_bar(bar, loc_Q, front)


def locate_samples_from_image(bar, impath, front=True):
    # if the image was just taken itself, before a bar was compiled, then this can be run to just load that image
    # and then interactively place the elements of bar
    global loc_Q
    # user needs to define the 'bar' in their namespace
    loc_Q = queue.Queue(1)
    if front:
        image = stitch_sample(
            False, False, False, from_image=impath, flip_file=False
        )  # this starts the sample pointing
    else:
        image = stitch_sample(False, False, False, from_image=impath, flip_file=False)
    # stitch samples will be sending signals, update bar will catch those signals and assign the positions to the bar
    update_bar(bar, loc_Q, front)


def update_bar(inbar, loc_Q, front):
    """
    updated with whether we are pointing at the front or the back of the bar
    """
    from threading import Thread

    global bar
    bar = inbar
    try:
        loc_Q.get_nowait()
    except Exception:
        ...

    def worker():
        global bar
        global sample_image_axes
        samplenum = 0
        lastclicked = 0
        if front:
            # add / replace the front fiducial bar entries (bar[0], bar[-1])
            AF1 = default_sample("AF1_front")
            AF2 = default_sample("AF2_front")
            if sample_by_name(bar, "AF1_front") is not None:
                bar.remove(sample_by_name(bar, "AF1_front"))
            if sample_by_name(bar, "AF2_front") is not None:
                bar.remove(sample_by_name(bar, "AF2_front"))
            bar.insert(0, AF1)
            bar.append(AF2)
            # add in a diode position as well
            diode = default_sample("diode")
            if sample_by_name(bar, "diode") is not None:
                bar.insert(-1, diode)

        else:
            # if front fiducials don't exist,add dummy ones (so thge AF2 ones are in the correct position)
            if sample_by_name(bar, "AF1_front") is None:
                AF1 = default_sample("AF1_front")
                bar.insert(0, AF1)
            if sample_by_name(bar, "AF2_front") is None:
                AF2 = default_sample("AF2_front")
                bar.append(AF2)

            # add / replace the back fiducial bar entries (bar[1], bar[-2])

            if sample_by_name(bar, "AF1_back") is not None:
                bar.remove(sample_by_name(bar, "AF1_back"))
            if sample_by_name(bar, "AF2_back") is not None:
                bar.remove(sample_by_name(bar, "AF2_back"))
            AF1 = default_sample("AF1_back")
            AF2 = default_sample("AF2_back")
            AF1["front"] = False
            AF2["front"] = False
            bar.insert(1, AF1)  # inserts in the second position
            bar.insert(-1, AF2)  # inserts in the second to last position
        while True:
            #        for sample in bar:
            sample = bar[samplenum]
            if sample["front"] != front:  # skip if we are not on the right side of the sample bar
                # (only locate samples that we can see in this image!)
                samplenum += 1
                if samplenum >= len(bar):
                    print("done")
                    break
                else:
                    continue
            print(sample)
            print(
                f'Right-click on {sample["sample_name"]} location (recorded location is {sample["bar_loc"]["spot"]}).  '
                + "Press n on plot or enter to skip to next sample, p for previous sample, esc to end"
            )
            # ipython input x,y or click in plt which outputs x, y location
            while True:
                try:
                    # print('trying')
                    item = loc_Q.get(timeout=1)
                except Exception:
                    # print('no item')
                    ...
                else:
                    # print('got something')
                    break
            if item != ("enter" or "escape" or "n" or "p") and isinstance(item, list):
                sample["location"] = item
                sample["bar_loc"]["ximg"] = float(item[0]["position"])
                sample["bar_loc"]["yimg"] = float(item[1]["position"])
                if front:
                    sample["bar_loc"]["th0"] = float(0)
                else:
                    sample["bar_loc"]["th0"] = float(180)
                annotateImage(sample_image_axes, item, sample["sample_name"])
                # advance sample and loop
                lastclicked = samplenum
                samplenum += 1
            elif item == "escape":
                print("aborting")
                break
            elif item == "enter" or item == "n":
                print(f'leaving this {sample["sample_name"]} unchanged')
                lastclicked = samplenum
                samplenum += 1
            elif item == "p":
                print("Previous sample")
                samplenum = lastclicked
            if samplenum >= len(bar):
                print("done")
                break

    t = Thread(target=worker)
    t.start()


def annotateImage(axes, item, name):
    ycoord = item[0]["position"]
    xcoord = item[1]["position"]

    a = axes.annotate(
        name,
        xy=(xcoord, ycoord),
        xycoords="data",
        xytext=(xcoord - 3, ycoord + 10),
        textcoords="data",
        arrowprops=dict(color="red", arrowstyle="->"),
        horizontalalignment="center",
        verticalalignment="bottom",
        color="red",
    )

    a.draggable()
    plt.draw()


def stitch_sample(images, step_size, y_off, from_image=None, flip_file=False):
    global sample_image_axes

    if isinstance(from_image, str):
        im_frame = Image.open(from_image)
        result = np.array(im_frame)
        if flip_file:
            result = np.flipud(result)
    else:
        pixel_step = int(step_size * (1760) / 25)
        pixel_overlap = 2464 - pixel_step
        result = images[0][0]
        i = 0
        for imageb in images[1:]:
            image = imageb[0]
            i += 1
            if y_off > 0:
                result = np.concatenate((image[(y_off * i) :, :], result[:-(y_off), pixel_overlap:]), axis=1)
            elif y_off < 0:
                result = np.concatenate((image[: (y_off * i), :], result[-(y_off):, pixel_overlap:]), axis=1)
            else:
                result = np.concatenate((image[:, :], result[:, pixel_overlap:]), axis=1)
        # result = np.flipud(result)

    fig, ax = plt.subplots()
    ax.imshow(result, extent=[-210, 25, -14.5, 14.5])
    sample_image_axes = ax
    fig.canvas.mpl_connect("button_press_event", plot_click)
    fig.canvas.mpl_connect("key_press_event", plot_key_press)
    plt.show()
    return result


def print_click(event):
    # print(event.xdata, event.ydata)
    global bar, barloc
    item = []
    item.append({"motor": "x", "position": event.ydata})
    item.append({"motor": "y", "position": event.xdata})
    item.append({"motor": "z", "position": 0})
    item.append({"motor": "th", "position": 180})
    bar[barloc]["location"] = item
    print(f"Setting location {barloc} on bar to clicked position")


def plot_click(event):
    # print(event.xdata, event.ydata)
    global loc_Q
    item = []
    item.append({"motor": "x", "position": event.ydata, "order": 0})
    item.append({"motor": "y", "position": event.xdata, "order": 0})
    item.append({"motor": "z", "position": 0, "order": 0})
    item.append({"motor": "th", "position": 180, "order": 0})
    if not loc_Q.full() and event.button == 3:
        loc_Q.put(item, block=False)


def plot_key_press(event):
    global loc_Q
    if not loc_Q.full() and (
        event.key == "enter" or event.key == "escape" or event.key == "n" or event.key == "p"
    ):
        loc_Q.put(event.key, block=False)


def offset_bar(bar, xoff, yoff, zoff, thoff):
    for samp in bar:
        for mot in samp["location"]:
            if mot["motor"] == "x":
                mot["position"] += xoff
            if mot["motor"] == "y":
                mot["position"] += yoff
            if mot["motor"] == "z":
                mot["position"] += zoff
            if mot["motor"] == "th":
                mot["position"] += thoff


def correct_bar(bar, fiduciallist, include_back, training_wheels=True):
    """
    originally this function adjusted the x, y, positions of samples on a bar
    to align with the x-y locations found by fiducials
    now the fiducial needs 4 x measurements at the different angles, (-90,0.90,180)
    and the one measurement of y for each fiducial
    and the sample z offset can be found as well
    so apritrary angles can be gone to if requested (this should be recorded in the 'th' parameter in bar_loc

    fiducial list is the list output by find_fiducials()
    """
    af2y = fiduciallist[0]
    af2xm90 = fiduciallist[1]
    af2x0 = fiduciallist[2]
    af2x90 = fiduciallist[3]
    af2x180 = fiduciallist[4]
    af1y = fiduciallist[5]
    af1xm90 = fiduciallist[6]
    af1x0 = fiduciallist[7]
    af1x90 = fiduciallist[8]
    af1x180 = fiduciallist[9]
    af1_front = sample_by_name(bar, "AF1_front")
    af2_front = sample_by_name(bar, "AF2_front")
    af1_back = sample_by_name(bar, "AF1_back")
    af2_back = sample_by_name(bar, "AF2_back")
    if af1_back is None:
        back = False
    else:
        back = include_back
    af1x_img = af1_front["location"][0]["position"]
    af1y_img = af1_front["location"][1]["position"]
    af2x_img = af2_front["location"][0]["position"]
    af2y_img = af2_front["location"][1]["position"]
    # adding the possibility of a back fiducial position as well as front
    # these will be nonsense if there was no back image (image bar didn't add in these positions)
    # but they won't be used, unless a sample is marked as being on the back
    if back:
        af1xback_img = af1_back["location"][0]["position"]
        af1yback_img = af1_back["location"][1]["position"]
        af2xback_img = af2_back["location"][0]["position"]
        af2yback_img = af2_back["location"][1]["position"]

    af1x, af1zoff, af1xoff = af_rotation(
        af1xm90, af1x0, af1x90, af1x180
    )  # find the center of rotation from fiducials
    af2x, af2zoff, af2xoff = af_rotation(af2xm90, af2x0, af2x90, af2x180)
    # these values are the corresponding values at theta=0,
    # which is what we want if the image is of the front of the bar
    af1xback = rotatedx(af1x, 180, af1zoff, af1xoff)
    af2xback = rotatedx(af2x, 180, af2zoff, af2xoff)
    # if we are looking at the sample from the back,
    # then we need to rotate the fiducial x and y location for the sample corrections

    x_offset = af1x - af1x_img  # offset from X-rays to image in x
    y_offset = af1y - af1y_img  # offset from X-rays to image in y
    y_image_offset = af1y_img - af2y_img  # distance between fiducial y positions (should be ~ -190)
    if back:
        x_offset_back = af1xback - af1xback_img  # offset from X-rays to image in x on the back
        y_offset_back = af1y - af1yback_img  # offset from X-rays to image in x
        y_image_offset_back = (
            af1yback_img - af2yback_img
        )  # distance between fiducial y positions (should be ~ -190)

    if training_wheels:
        assert abs(abs(af2y - af1y) - abs(y_image_offset)) < 5, (
            "Hmm... "
            "it seems like the length of the bar has changed by more than"
            " 5 mm between the imager and the chamber.  \n \n Are you sure"
            " your alignment fiducials are correctly located?  \n\n If you're"
            " really sure, rerun with training_wheels=false."
        )

    dx = af2x - af2x_img - x_offset  # offset of Af2 X-rays to image in x relative to Af1 (mostly rotating)
    # dx is the total offset needed for a position in the image to be located with X-rays at the bottom of the bar
    # the
    dy = af2y - af2y_img - y_offset  # offset of Af2 X-rays to image in y relative to Af1 (mostly stretching)
    if back:
        dxb = (
            af2xback - af1xback + af1xback_img - af2xback_img
        )  # offset of Af2 X-rays to image in x relative to Af1 (mostly rotating)
        # offset from the top of the bar to the bottom of the bar with X-rays  minus
        # offset of the top of the bar to the bottom in the image
        # dxb is the extra bit needed to move the bottom of the bar to correct for this rotation
        dyb = (af2y - af1y) - (
            af2yback_img - af1yback_img
        )  # offset of Af2 X-rays to image in y relative to Af1 (this is scaling the image - should be 0)
        # dyb is the extra bit needed to scale the bottom of the bar to correct for this scaling
    # dx, dy, dyb, and dxb are all relative correction factors, which are from the top of the bar to the bottom,
    # we use run_y to translate this to a offset per mm
    run_y = af2y - af1y  # (distance between the fiducial markers) (above are the total delta over this run,
    # in between this will be scaled

    for samp in bar:
        xpos = samp["bar_loc"]["ximg"]  # x position from the image
        ypos = samp["bar_loc"]["yimg"]  # y position from the image
        xoff = af1xoff - (af1xoff - af2xoff) * (ypos - af1y) / run_y
        samp["bar_loc"]["xoff"] = float(xoff)  # this should pretty much be the same for both fiducials,
        # but just in case there is a tilt,
        # we account for that here, taking af1soff if the sample is towards the top and af2soff as it is lower

        if samp["front"]:
            newx = xpos + x_offset + (ypos - af1y) * dx / run_y
            # new position is the image position, plus the offset from the image to the x-rays, plus a linear correction
            # from the top of the bar to the bottom
            newy = ypos + y_offset + (ypos - af1y) * dy / run_y
            samp["bar_loc"]["x0"] = float(
                newx
            )  # these are the positions at 0 rotation, so for the front, we are already good
        elif back:
            newx = xpos + x_offset_back + (ypos - af1y) * dxb / run_y
            newy = ypos + y_offset_back + (ypos - af1y) * dyb / run_y
            samp["bar_loc"]["x0"] = float(2 * xoff - newx)  # these are the positions at 0 rotation,
            # so for the back, we have to correct
        else:
            continue  # sample is on the back, and we are not doing the back of the bar, so skip
        samp["bar_loc"]["y0"] = float(newy)
        # recording of fiducial information as well with every sample, so they will know how to rotate
        samp["bar_loc"]["af1y"] = float(af1y)
        samp["bar_loc"]["af2y"] = float(af2y)
        samp["bar_loc"]["af1xoff"] = float(af1xoff)
        samp["bar_loc"]["af2xoff"] = float(af2xoff)
        samp["bar_loc"]["af1zoff"] = float(af1zoff)
        samp["bar_loc"]["af2zoff"] = float(af2zoff)

        zoff = zoffset(
            af1zoff,
            af2zoff,
            newy,
            front=samp["front"],
            height=samp["height"],
            af1y=af1y,
            af2y=af2y,
        )
        samp["bar_loc"]["zoff"] = float(zoff)

        # now we can rotate the sample to the desired position (in the 'angle' metadata)
        # moving z is dangerous = best to keep it at 0 by default
        rotate_sample(samp)  # this will take the positions found above and the desired incident angle and
        # rotate the location of the sample accordingly


def zoffset(af1zoff, af2zoff, y, front=True, height=0.25, af1y=-186.3, af2y=4):
    """
    Using the z offset of the fiducial positions from the center of rotation,
    project the z offset of the surface of a given sample at some y position between
    the fiducials.
    """

    m = (af2zoff - af1zoff) / (af2y - af1y)  # slope of bar
    z0 = af1zoff + m * (y - af1y)

    # offset the line by the front/back offset + height
    if front:
        return z0 - 2.5 - height
    else:
        return z0 + height
    # return the offset intersect


def rotatedx(x0, theta, zoff, xoff=1.88, thoff=1.6):
    """
    given the x position at 0 rotation (from the image of the sample bar)
    and a rotation angle, the offset of rotation in z and x (as well as a potential theta offset)
    find the correct x position to move to at a different rotation angle
    """
    return (
        xoff + (x0 - xoff) * np.cos((theta - thoff) * np.pi / 180) - zoff * np.sin((theta - thoff) * np.pi / 180)
    )


def rotatedz(x0, theta, zoff, xoff=1.88, thoff=1.6):
    """
    given the x position at 0 rotation (from the image of the sample bar)
    and a rotation angle, the offset of rotation in z and x axes (as well as a potential theta offset)
    find the correct z position to move to to keep a particular sample at the same intersection point with X-rays
    """
    return (
        zoff + (x0 - xoff) * np.sin((theta - thoff) * np.pi / 180) - zoff * np.cos((theta - thoff) * np.pi / 180)
    )


def af_rotation(xfm90, xf0, xf90, xf180):
    """
    takes the fiducial centers measured in the x direction at -90, 0, 90, and 180 degrees
    and returns the offset in x and z from the center of rotation, as well as the
    unrotated x positon of the fiducial marker.

    the x offset is not expected to vary between loads, and has been measured to be 1.88,
    while the z offset is as the bar flexes in this direction, and will be used to
    map the surface locations of other samples between the fiducials

    """

    x0 = xf0
    xoff = (xf180 + x0) / 2
    zoff = (xfm90 - xf90) / 2
    return (x0, zoff, xoff)


def find_fiducials(f2=[7.5, 3.5, -2.5, 1.1]):
    thoffset = 1.6
    angles = [-90 + thoffset, 0 + thoffset, 90 + thoffset, 180 + thoffset]
    xrange = 3.5
    xnum = 36
    startxss = [f2, [4.2, 3.5, 1, 1.1]]
    yield from bps.mv(Shutter_enable, 0)
    yield from bps.mv(Shutter_control, 0)
    yield from load_configuration("SAXSNEXAFS")
    Beamstop_SAXS.kind = "hinted"
    # yield from bps.mv(DiodeRange, 7)
    bec.enable_plots()
    startys = [3, -188.0]  # af2 first because it is a safer location
    maxlocs = []
    for startxs, starty in zip(startxss, startys):
        yield from bps.mv(sam_Y, starty, sam_X, startxs[1], sam_Th, 0, sam_Z, 0)
        yield from bps.mv(Shutter_control, 1)
        yield from bp.rel_scan([Beamstop_SAXS], sam_Y, -1, 0.5, 16)
        yield from bps.mv(Shutter_control, 0)
        maxlocs.append(bec.peaks.max["SAXS Beamstop"][0])
        yield from bps.mv(sam_Y, bec.peaks.max["SAXS Beamstop"][0])
        for startx, angle in zip(startxs, angles):
            yield from bps.mv(sam_X, startx, sam_Th, angle)
            yield from bps.mv(Shutter_control, 1)
            yield from bp.scan(
                [Beamstop_SAXS],
                sam_X,
                startx - 0.5 * xrange,
                startx + 0.5 * xrange,
                xnum,
            )
            yield from bps.mv(Shutter_control, 0)
            yield from bps.sleep(3)
            maxlocs.append(bec.peaks.max["SAXS Beamstop"][0])
    print(maxlocs)  # [af2y,af2xm90,af2x0,af2x90,af2x180,af1y,af1xm90,af1x0,af1x90,af1x180]
    bec.disable_plots()


def rotate_now(theta, force=False):
    if theta is not None:
        samp = get_sample_dict()
        samp["angle"] = theta
        rotate_sample(samp, force)
        yield from load_sample(samp)


def rotate_sample(samp, force=False):
    """
    rotate a sample position to the requested theta position
    the requested sample position is set in the angle metadata (sample['angle'])
    """
    sanatize_angle(samp, force)  # makes sure the requested angle is translated into a real angle for acquisition
    theta_new = samp["bar_loc"]["th"]
    x0 = samp["bar_loc"]["x0"]
    y0 = samp["bar_loc"]["y0"]
    xoff = samp["bar_loc"]["xoff"]
    zoff = samp["bar_loc"]["zoff"]

    newx = rotatedx(x0, theta_new, zoff, xoff=xoff)
    for motor in samp["location"]:
        if motor["motor"] == "x":
            motor["position"] = newx
        if motor["motor"] == "th":
            motor["position"] = theta_new
        if motor["motor"] == "y":
            motor["position"] = y0

    # in future, updating y (if the rotation axis is not perfectly along y
    # and z (to keep the sample-detector distance constant) as needed would be good as well
    # newz = rotatedz(newx, th, zoff, af1xoff)


def sample_recenter_sample(samp):
    # the current samp['location'] is correct, the point of this is to make sure the x0 and y0 and incident angles
    # are updated accordingly, because the samp['location'] will generally be recalculated and overwritten next time
    # a sample rotation is requested
    # assume the center of rotation for the sample is already calculated correctly (otherwise correct bar is needed)
    # first record the location
    for loc in samp["location"]:
        if loc["motor"] == "x":
            newrotatedx = loc["position"]
        if loc["motor"] == "y":
            newy = loc["position"]
        if loc["motor"] == "th":
            newangle = loc["position"]
    # get the rotation parameters from the metadata
    xoff = samp["bar_loc"]["xoff"]
    zoff = samp["bar_loc"]["zoff"]
    # find the x0 location which would result in this new position
    newx0 = rotatedx(newrotatedx, -newangle, zoff, xoff=xoff)  # we rotate by the negative angle to get back to x0
    samp["bar_loc"]["x0"] = newx0
    samp["bar_loc"]["y0"] = newy  # y and y0 are the same, so we can just copy this
    samp["angle"] = newangle


def read_positions(bar):
    # for when the positions are altered by hand in the excel sheet, (i.e. after spiral scans)
    # this reads those positions and sets the default positions (x0 and y0) to match
    for samp in bar:
        sample_recenter_sample(samp)
