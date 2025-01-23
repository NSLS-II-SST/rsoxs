## TODO: update code and reorganize contents from alignment_local.py, alignment.py, and fly_alignment into the files in alignment folder
## TODO: code needs updates to comply with data security.  Main changes would be to have functions not point to db.  Instead, they can take in an up-to-date spreadsheet and any other necessary inputs and run that way.
## TODO: if possible, preserve bsui_local such that code that does not require beamline hardware can be run there.

import copy
import bluesky.plans as bp
from operator import itemgetter
from copy import deepcopy
import collections
import numpy as np

from functools import partial
import bluesky.plan_stubs as bps
from ophyd import Device
from ..startup import RE
from nbs_bl.hw import(
    Shutter_control,
    sam_X,
    sam_Y,
)
## An alternative way to load devices is:
#from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
#Beamstop_SAXS = bl["Beamstop_SAXS"] ## what follows bl is the key in devices.toml in profile_collection contained in the []
from rsoxs.HW.signals import default_sigs
from rsoxs.HW.detectors import set_exposure#, saxs_det
from rsoxs.HW.energy import en, set_polarization, grating_to_1200, grating_to_250, grating_to_rsoxs
from nbs_bl.printing import run_report, boxed_text, colored
from rsoxs.HW.slackbot import rsoxs_bot
from rsoxs.Functions import configurations
from rsoxs.Functions.per_steps import (
    take_exposure_corrected_reading,
    one_nd_sticky_exp_step
)

from rsoxs.Functions.alignment_local import *
run_report(__file__)

## The following imports need to be done outside Bluesky
#from rsoxs_scans.spreadsheets import load_samplesxlsx, save_samplesxlsx
#import PyHyperScattering as phs


## TODO: this was mostly just copied over from eliot's old code, so make it streamlined and might want to move sanitization to a different function
def spiral_survey(
    diameter=0.6,
    stepsize=0.2,
    energy=270,
    pol=0,
    angle=None,
    exposure=1,
    repeats=1,
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
    ## TODO: find a different way to do this.  I want to keep the functionality that we can ctrl + c the scan and move on, but I also want the possibility of doing multiple spirals without having  to remove from the spreadsheet.
    if len(str(md.get('bar_loc',{}).get('spiral_started','')))>0 and not force:
        print(f"spiral for {md['sample_name']} was already started, either force, or remove to run spiral again")
        yield from bps.null()
        return ''
    arguments = dict(locals())
    valid = True
    validation = ""
    newdets = []
    signals = default_sigs
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
    if len(newdets) != 1:
        valid = False
        validation += "a detector number not equal to 1 was given\n"

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
    
    set_exposure(exposure)
    old_n_exp = {}
    for det in newdets:
        old_n_exp[det.name] = det.number_exposures
        det.number_exposures = repeats
         
    x_center = sam_X.user_setpoint.get()
    y_center = sam_Y.user_setpoint.get()
    num = round(diameter / stepsize) + 1

    if isinstance(angle,(float,int)):
        print(f"moving angle to {angle}")
        yield from rotate_now(angle)
    md['bar_loc']['spiral_started'] = 1 #md['bar_loc']['spiral_started'] = RE.md['scan_id']+1

    yield from bp.spiral_square(
                newdets + signals,
                sam_X,
                sam_Y,
                x_center=x_center,
                y_center=y_center,
                x_range=diameter,
                y_range=diameter,
                x_num=num,
                y_num=num,
                md=md,
                per_step=partial(one_nd_sticky_exp_step,
                                    remember={},
                                    take_reading=partial(take_exposure_corrected_reading,
                                                        shutter = Shutter_control,
                                                        check_exposure=False))
                )
                
    #md['bar_loc']['spiral_started'] = db[-1]['start']['uid'] ## Don't want to access db







def pick_locations_from_spirals( ## Intended to be an updated, data-security-compliant version of resolve_spirals.  Probably will just have this function pick spots for one sample and then it can be rerun for multiple samples.  That way, not all spirals have to be resolved in one go.
        configuration, ## Up-to-date spreadsheet with current sample locations.  TODO: maybe load sheet separately and then pick spots and then save out a new sheet
        sampleID,
        catalog,
        scanID_Survey, ## Maybe the more generic thing to call it is a survey scan
        locationsSelected_Indices,
        
):
    
    ## TODO: Consider making this a more generic function that picks a sample location from some series scan.  For spiral scans, it picks x and y location, but for an angle series, it could pick from there as well
    ## Can do something like try/except where I try to find the coordinate from primary but otherwise, find it from the baseline
    ## Otherwise, this is simple enough to make a separate function for an angle series and not have unnecessary errors due to extra checking

    
    ## Load spiral scan from tiled and gather location coordinates
    scanSurvey = catalog[int(scanID_Survey)]
    ## TODO: If sample_id from tiled does not equal the sample ID here, then give warning
    locations_OutboardInboard = scanSurvey["primary"]["data"]["RSoXS Sample Outboard-Inboard"].read()
    locations_DownUp = scanSurvey["primary"]["data"]["RSoXS Sample Up-Down"].read()
    locations_UpstreamDownstream = scanSurvey["baseline"]["data"]["RSoXS Sample Downstream-Upstream"][0]
    locations_Theta = scanSurvey["baseline"]["data"]["RSoXS Sample Rotation"][0]
    
    
    ## Find the sample to update location
    ## TODO: probably better to deep copy configuration and search through the copy while updating the original configuration?
    for index_Configuration, sample in enumerate(configuration):
        if sample["sample_id"] == sampleID: 
            #locationInitial = sample["location"]
            for index_locationSelected_Indices, locationSelected_Indices in enumerate(locationsSelected_Indices):
                #locationNewFormatted = copy.deepcopy(locationInitial)
                locationNewFormatted = [{'motor':'x','position':locations_OutboardInboard[locationSelected_Indices]},
                                        {'motor':'y','position':locations_DownUp[locationSelected_Indices]},
                                        {'motor':'th','position':locations_Theta},
                                        {'motor':'z','position':locations_UpstreamDownstream}]
                if index_locationSelected_Indices==0: sample["location"] = locationNewFormatted
                else: 
                    sampleNew = copy.deepcopy(sample)
                    sampleNew["location"] = locationNewFormatted
                    sampleNew["sample_name"]+=f'_{index_locationSelected_Indices}'
                    sampleNew["sample_id"]+=f'_{index_locationSelected_Indices}'
                    configuration.append(sampleNew)
            break ## Exit after the sample is found and do not spend time looking through the other samples



## How to use pick_locations_from_spirals
"""
## Install rsoxs codebase and pyhyper

!pip install "git+https://github.com/xraygui/nbs-core.git"
!pip install "git+https://github.com/xraygui/nbs-bl.git"
!pip install "git+https://github.com/NSLS-II-SST/sst_base.git"
!pip install "git+https://github.com/NSLS-II-SST/rsoxs.git@Issue18_SimplifyScans"
!pip install "git+https://github.com/NSLS-II-SST/rsoxs_scans.git@rsoxsIssue18_SimplifyScans"
!pip install "git+https://github.com/usnistgov/PyHyperScattering.git@Issue170_UpdateDatabrokerImports#egg=PyHyperScattering[bluesky]"
"""

"""
## Imports

from rsoxs_scans.spreadsheets import load_samplesxlsx, save_samplesxlsx
from rsoxs.alignment2.spiral_scans import pick_locations_from_spirals

import PyHyperScattering as phs
print(f'Using PyHyper Version: {phs.__version__}')


Loader = phs.load.SST1RSoXSDB(corr_mode="none") #Loader = phs.load.SST1RSoXSDB(corr_mode='none', catalog_kwargs={"username":"pketkar"}) #Loader = phs.load.SST1RSoXSDB(corr_mode='none')
Catalog = Loader.c
Catalog
"""


"""
## Use the function

pathConfiguration = r"/content/drive/Shareddrives/NISTPostdoc/CharacterizationData/BeamTime/20241202_SST1_Murphy/DataAnalysis/out_2024-12-08_spirals_resolved_TEST2.xlsx"
configuration = load_samplesxlsx(pathConfiguration) ## (load_spreadsheet with update_configuration=False in my new code)

pick_locations_from_spirals(configuration=configuration,
                            sampleID="KR151", 
                            catalog=Catalog,
                            scanID_Survey=90681, 
                            locationsSelected_Indices=[0, 1]
                            )
save_samplesxlsx(bar=configuration, name="TestOut", path=r"/content/drive/Shareddrives/NISTPostdoc/CharacterizationData/BeamTime/20241202_SST1_Murphy/DataAnalysis/")
"""
