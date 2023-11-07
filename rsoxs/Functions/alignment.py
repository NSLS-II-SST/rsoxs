import bluesky.plans as bp
from matplotlib import pyplot as plt
import queue
from PIL import Image
from operator import itemgetter
from copy import deepcopy
import collections
import numpy as np
import datetime
import warnings
import bluesky.plan_stubs as bps
from bluesky.utils import FailedStatus
from ophyd import Device
from bluesky.preprocessors import finalize_decorator
from ..startup import RE, db, bec, db0, rsoxs_config
from ..HW.motors import sam_viewer
from ..HW.cameras import SampleViewer_cam
from sst_hw.diode import Shutter_enable, Shutter_control
from ..HW.signals import Beamstop_SAXS, Beamstop_WAXS, DiodeRange, Beamstop_SAXS_int,Beamstop_WAXS_int, Izero_Mesh_int,Sample_TEY_int

from ..HW.detectors import waxs_det,  set_exposure#, saxs_det
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

from .alignment_local import *
from .flystream_wrapper import flystream_during_wrapper
run_report(__file__)


def sample():
    title = "Sample metadata - stored in every scan:"
    text = ""
    if len(str(RE.md["proposal_id"])) > 0:
        text += "   proposal ID:           " + colored("{}".format(RE.md["proposal_id"]).center(48, " "), "cyan")
    if len(str(RE.md["SAF"])) > 0:
        text += "\n   SAF id:                " + colored("{}".format(RE.md["SAF"]).center(48, " "), "cyan")
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



def get_location(motor_list):
    locs = []
    for motor in motor_list:
        locs.append({"motor": motor, "position": motor.user_readback.get(), "order": 0})
    return locs


def sample_set_location(num):
    sample_dict = rsoxs_config['bar'][num]
    sample_dict["location"] = get_sample_location()  # set the location metadata
    # sample_recenter_sample(
    #     sample_dict
    # )  # change the x0, y0, theta to result in this new position (including angle)
    # return sample_dict


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
        TEMZ: TEMZ,
        'TEMZ': TEMZ,
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
    
def load_samp(num_or_id, sim_mode=False):
    """
    move to a sample location and load the metadata with the sample information from persistant sample list by index or sample_id

    :param sam_dict: sample dictionary containing all metadata and sample location
    :return:
    """
    sam_dict = samp_dict_from_id_or_num(num_or_id)
    yield from load_sample(sam_dict, sim_mode)


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



def alignment_rel_scan(det, motor, start_rel, end_rel, steps):
    savemd = RE.md.deepcopy()




# Spiral searches


def samxscan():
    yield from psh10.open()
    yield from bp.rel_scan([Beamstop_SAXS], sam_X, -2, 2, 41)
    yield from psh10.close()



@finalize_decorator(rsoxs_config.write_plan)
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
    force=False,
    **kwargs,
):
    """conduct a spiral grid pattern of exposures

    Parameters
    ----------
    diameter : float, optional
        _description_, by default 0.6
    stepsize : float, optional
        _description_, by default 0.2
    energy : int, optional
        _description_, by default 270 -148.3
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
    md : _type_, optional
        the sample dictionary, by default None
    force : bool, optional
        force a spiral even if one was already started, by default False
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
    if md is None:
        md = RE.md
    if len(str(md.get('bar_loc',{}).get('spiral_started','')))>0 and not force:
        print(f"spiral for {md['sample_name']} was already started, either force, or remove to run spiral again")
        yield from bps.null()
        return ''
    arguments = dict(locals())
    valid = True
    validation = ""
    newdets = []
    for argument in arguments:
        if isinstance(argument,np.ndarray):
            argument = list(argument)
    del arguments["md"]  # no recursion here!
    md.setdefault("acq_history", [])
    md["acq_history"].append(
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

    if isinstance(angle,(float,int)):
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

    if isinstance(angle,(float,int)):
        print(f"moving angle to {angle}")
        yield from rotate_now(angle)
    md['bar_loc']['spiral_started'] = RE.md['scan_id']+1

    yield from flystream_during_wrapper(bp.spiral_square(
                                                        newdets,
                                                        sam_X,
                                                        sam_Y,
                                                        x_center=x_center,
                                                        y_center=y_center,
                                                        x_range=diameter,
                                                        y_range=diameter,
                                                        x_num=num,
                                                        y_num=num,
                                                        md=md,
                ),[Beamstop_WAXS_int, Beamstop_SAXS_int, Izero_Mesh_int, Sample_TEY_int])
    md['bar_loc']['spiral_started'] = db[-1]['start']['uid']




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


def find_fiducials(f2=[7.5, 3.5, -2.5, 1.1]):
    thoffset = 0
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
    startys = [3, -187.0]  # af2 first because it is a safer location
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
    accept = input(f"Do you want to apply this correction (y,n)?")
    if accept in ['y','Y','yes']:
        back = False
        rsoxs_config.read()
        for samp in rsoxs_config['bar']:
            if samp['front'] ==False:
                back = True
        correct_bar(maxlocs,include_back=back)
    bec.disable_plots()


def rotate_now(theta, force=False):
    if theta is not None:
        samp = get_sample_dict()
        samp["angle"] = theta
        rotate_sample(samp, force)
        rsoxs_config.write()
        yield from load_sample(samp)


def jog_samp_zoff(id_or_num,jog_val,write_default=True,move=True):
    # jogs the zoffset of a sample by some mm and optionally moves to the new position
    samp = samp_dict_from_id_or_num(id_or_num)
    if jog_val < -5 or jog_val > 5:
        raise ValueError('invalid jog value with magnitude > 5 was entered, start with something small')
    if 'bar_loc' in samp:
        if 'zoff' in samp['bar_loc']:
            samp['bar_loc']['zoff'] += jog_val
            if write_default:
                rotate_sample(samp) # this will write the new rotated positions into the position (without moving anything)
            rsoxs_config.write() # this saves the zoff and the new rotated position to the persistent sample list
            if(move):
                RE(load_samp(id_or_num))
        else:
            raise ValueError(f'the sample {samp["sample_name"]} does not appear to have a zoff yet, have you corrected positions?')
    else:
        raise ValueError(f'the sample {samp["sample_name"]} does not appear to have a bar_loc field yet, have you imaged the sample positions?')

