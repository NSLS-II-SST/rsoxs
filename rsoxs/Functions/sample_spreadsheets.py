import pandas as pd
import numpy as np
import re
from ophyd import Device
from operator import itemgetter
from numpy import array
import re, warnings, httpx
from .common_functions import args_to_string, string_to_inputs
from ..HW.motors import sam_X, sam_Y, sam_Th, sam_Z
from ..Functions.acquisitions import avg_scan_time
from ..Functions import rsoxs_queue_plans
from ..HW.detectors import waxs_det, saxs_det


from .energyscans import (
    full_ca_scan_nd,
    full_carbon_calcium_scan_nd,
    full_carbon_scan_nd,
    full_carbon_scan_nonaromatic,
    full_fluorine_scan_nd,
    full_iron_scan_nd,
    full_nitrogen_scan_nd,
    full_oxygen_scan_nd,
    short_calcium_scan_nd,
    short_nitrogen_scan_nd,
    short_oxygen_scan_nd,
    short_sulfurl_scan_nd,
    short_zincl_scan_nd,
    short_carbon_scan_nd,
    short_carbon_scan_nonaromatic,
    collins_carbon_survey_fixedpol,
    short_fluorine_scan_nd,
    survey_scan_highenergy,
    very_short_carbon_scan_nd,
    very_short_oxygen_scan_nd,
    veryshort_fluorine_scan_nd,
    survey_scan_lowenergy,
    survey_scan_veryhighenergy,
    survey_scan_verylowenergy,
    cdsaxs_scan,
    custom_rsoxs_scan,
    custom_rotate_rsoxs_scan,
    focused_carbon_scan_nd,
)
from .NEXAFSscans import (
    fly_Oxygen_NEXAFS,
    fly_Iron_NEXAFS,
    fly_Nitrogen_NEXAFS,
    fly_Fluorine_NEXAFS,
    fly_Boron_NEXAFS,
    fixed_pol_rotate_sample_nexafs,
    fixed_sample_rotate_pol_list_nexafs,
    fixed_sample_rotate_pol_nexafs,
    fly_Calcium_NEXAFS,
    fly_Carbon_NEXAFS,
    fly_SiliconK_NEXAFS,
    fly_SiliconL_NEXAFS,
    fly_SulfurL_NEXAFS,
    full_Carbon_NEXAFS,
    normal_incidence_rotate_pol_nexafs,
)
from .alignment import (
    load_sample,
    load_configuration,
    spiralsearch,
)



def add_acq(
    sample_dict, plan_name="full_carbon_scan", arguments="", config="WAXS", priority=50
):
    sample_dict["acquisitions"].append(
        {
            "plan_name": plan_name,
            "args": string_to_inputs(arguments)[0],
            "kwargs": string_to_inputs(arguments)[1],
            "configuration": config,
            "priority": priority,
        }
    )
    return sample_dict


def get_proposal_info(proposal_id, beamline='SST1', path_base='/sst/', cycle='2022-2'):
    '''
    proposal_id is either a string of a number, a string including a "GU-", "PU-", "pass-", or  "C-" prefix and a number, or a number
    beamline is the beamline name from PASS,
    path_base is the part of the path that indicates it's really for this beamline
    cycle is the current cycle (or the cycle that is valid for this purpose)

    queury the api PASS database, and get the info corresponding to a proposal ID
    returns:
    the data_session ID which should be put into the run engine metadata of every scan
    the path to write analyzed data to
    all of the proposal information for the metadata if needed
    '''
    warn_text = "\n WARNING!!! no data taken with this proposal will be retrievable \n  it is HIGHLY suggested that you fix this"
    proposal_re = re.compile(r"^[GUCPpass]*-?(?P<proposal_number>\d+)$")
    if isinstance(proposal_id, str):
        proposal = proposal_re.match(proposal_id).group("proposal_number")
    else:
        proposal = proposal_id
    pass_client = httpx.Client(base_url="https://api-staging.nsls2.bnl.gov")
    responce = pass_client.get(f"/proposal/{proposal}")
    res = responce.json()
    if "safs" not in res:
        warnings.warn(f'proposal {proposal} does not appear to have any safs'+warn_text)
        return None, None, None, None
    comissioning = 1
    if "cycles" in res:
        comissioning = 0
        if cycle not in res['cycles']:
            warnings.warn(f'proposal {proposal} is not valid for the {cycle} cycle'+warn_text)
            return None, None, None, None
    elif "Commissioning" not in res['type']:
        warnings.warn(
            f'proposal {proposal} does not have a valid cycle, and does not appear to be a commissioning proposal'+warn_text)
        return -1
    if len(res['safs']) < 0:
        warnings.warn(f'proposal {proposal} does not have a valid SAF in the system'+warn_text)
        return None, None, None, None
    valid_SAF = ""
    for saf in res['safs']:
        if saf['status'] == 'APPROVED' and beamline in saf['instruments']:
            valid_SAF = saf['saf_id']
    if len(valid_SAF) == 0:
        warnings.warn(f'proposal {proposal} does not have a SAF for {beamline} active in the system'+warn_text)
        return None, None, None, None
    proposal_info = res
    dir_responce = pass_client.get(f"/proposal/{proposal}/directories")
    dir_res = dir_responce.json()
    if len(dir_res) < 1:
        warnings.warn(f'proposal{proposal} have any directories'+warn_text)
        return None, None, None, None
    valid_path = ""
    for dir in dir_res:
        if comissioning and (path_base in dir['path']):
            valid_path = dir['path']
        elif (path_base in dir['path']) and (cycle in dir['path']):
            valid_path = dir['path']
    if len(valid_path) == 0:
        warnings.warn(f'no valid paths (containing {path_base} and {cycle} were found for proposal {proposal}'+warn_text)
        return None, None, None, None
    return res['data_session'], valid_path, valid_SAF, proposal_info


def load_samplesxls(filename):
    df = pd.read_excel(
        filename,
        na_values="",
        engine="openpyxl",
        keep_default_na=True,
        converters={"sample_date": str},
        sheet_name="Samples",
        verbose=True,
    )
    df.replace(np.nan, "", regex=True, inplace=True)
    samplenew = df.to_dict(orient="records")
    if not isinstance(samplenew, list):
        samplenew = [samplenew]
    if "acquisitions" not in samplenew[0].keys():
        for samp in samplenew:
            samp["acquisitions"] = []
        acqsdf = pd.read_excel(
            filename,
            na_values="",
            engine="openpyxl",
            keep_default_na=True,
            sheet_name="Acquisitions",
            usecols="A:E",
            verbose=True,
        )
        acqs = acqsdf.to_dict(orient="records")
        if not isinstance(acqs, list):
            acqs = [acqs]
        for acq in acqs:
            if np.isnan(acq["priority"]):
                break
            samp = next(
                dict for dict in samplenew if dict["sample_id"] == acq["sample_id"]
            )
            add_acq(
                samp,
                acq["plan_name"],
                acq["arguments"],
                acq["configuration"],
                acq["priority"],
            )
    else:
        for i, sam in enumerate(samplenew):
            samplenew[i]["acquisitions"] = eval(sam["acquisitions"])
    for i, sam in enumerate(samplenew):
        samplenew[i]["location"] = eval(sam["location"])

        samplenew[i]["bar_loc"] = eval(sam["bar_loc"])
        if 'proposal_id' in sam:
            proposal = sam['proposal_id']
        elif 'data_session' in sam:
            proposal = sam['data_session']
        else:
            warnings.warn('no valid proposal was located - please add that and try again')
            proposal = 0
        sam['data_session'],sam['analysis_dir'],sam['SAF'],sam['proposal'] = get_proposal_info(proposal)
        if sam['SAF'] ==None:
            print(f'line {i}, sample {sam["sample_name"]} - data will not be accessible')
        if "acq_history" in sam.keys():
            samplenew[i]["acq_history"] = eval(sam["acq_history"])
        else:
            samplenew[i]["acq_history"] = []
        samplenew[i]["bar_loc"]["spot"] = sam["bar_spot"]
        for key in [key for key, value in sam.items() if "named" in key.lower()]:
            del samplenew[i][key]
    return samplenew


def save_samplesxls(bar, filename):
    switch = {
        sam_X.name: "x",
        sam_Y.name: "y",
        sam_Z.name: "z",
        sam_Th.name: "th",
        "x": "x",
        "y": "y",
        "z": "z",
        "th": "th",
    }
    sampledf = pd.DataFrame.from_dict(bar, orient="columns")
    sampledf.to_excel("temp.xlsx", index=False)

    df = pd.read_excel("temp.xlsx", na_values="")
    df.replace(np.nan, "", regex=True, inplace=True)
    testdict = df.to_dict(orient="records")
    for i, sam in enumerate(testdict):
        testdict[i]["location"] = eval(sam["location"])
        testdict[i]["acquisitions"] = eval(sam["acquisitions"])
        for acq in testdict[i]["acquisitions"]:
            args = acq["args"]
            kwargs = acq["kwargs"]
            acq["arguments"] = args_to_string(*args, **kwargs)
            del acq["args"]
            del acq["kwargs"]
        if "acq_history" not in testdict[i].keys():
            testdict[i]["acq_history"] = []
        elif testdict[i]["acq_history"] is "":
            testdict[i]["acq_history"] = []
        else:
            testdict[i]["acq_history"] = eval(sam["acq_history"])
        testdict[i]["bar_loc"] = eval(sam["bar_loc"])
        testdict[i]["bar_loc"]["spot"] = sam["bar_spot"]
    acqlist = []
    for i, sam in enumerate(testdict):
        for j, loc in enumerate(sam["location"]):
            if isinstance(loc["motor"], Device):
                testdict[i]["location"][j]["motor"] = switch[loc["motor"].name]
        for acq in sam["acquisitions"]:
            acq.update({"sample_id": sam["sample_id"]})
            acqlist.append(acq)

    sampledf = pd.DataFrame.from_dict(testdict, orient="columns")
    sampledf = sampledf.loc[:, df.columns != "acquisitions"]
    acqdf = pd.DataFrame.from_dict(acqlist, orient="columns")
    writer = pd.ExcelWriter(filename)
    sampledf.to_excel(writer, index=False, sheet_name="Samples")
    acqdf.to_excel(writer, index=False, sheet_name="Acquisitions")
    writer.close()


def load_xlsx_to_plan_list(
    filename, sort_by=["sample_num"], rev=[False], retract_when_done=False
):
    """
    run all sample dictionaries stored in the list bar
    @param bar: a list of sample dictionaries
    @param sort_by: list of strings determining the sorting of scans
                    strings include project, configuration, sample_id, plan, plan_args, spriority, apriority
                    within which all of one acquisition, etc
    @param dryrun: Print out the list of plans instead of actually doing anything - safe to do during setup
    @param rev: list the same length of sort_by, or booleans, wetierh to reverse that sort
    @param delete_as_complete: remove the acquisitions from the bar as we go, so we can automatically start back up
    @param retract_when_done: go to throughstation mode at the end of all runs.
    @param save_as_complete: if a valid path, will save the running bar to this position in case of failure
    @return:
    """
    bar = load_samplesxls(filename)
    list_out = []
    for samp_num, s in enumerate(bar):
        sample = s
        sample_id = s["sample_id"]
        sample_project = s["project_name"]
        for acq_num, a in enumerate(s["acquisitions"]):
            if "priority" not in a.keys():
                a["priority"] = 50
            list_out.append(
                [
                    sample_id,  # 0  X
                    sample_project,  # 1  X
                    a["configuration"],  # 2  X
                    a["plan_name"],  # 3
                    avg_scan_time(a["plan_name"], 50),  # 4 calculated plan time
                    sample,  # 5 full sample dict
                    a,  # 6 full acquisition dict
                    samp_num,  # 7 sample index
                    acq_num,  # 8 acq index
                    a["args"],  # 9  X
                    s["density"],  # 10
                    s["proposal_id"],  # 11 X
                    s["sample_priority"],  # 12 X
                    a["priority"],
                ]
            )  # 13 X
    switcher = {
        "sample_id": 0,
        "project": 1,
        "config": 2,
        "plan": 3,
        "plan_args": 9,
        "proposal": 11,
        "spriority": 12,
        "apriority": 13,
        "sample_num": 7,
    }
    # add anything to the above list, and make a key in the above dictionary,
    # using that element to sort by something else
    try:
        sort_by.reverse()
        rev.reverse()
    except AttributeError:
        if isinstance(sort_by, str):
            sort_by = [sort_by]
            rev = [rev]
        else:
            print(
                "sort_by needs to be a list of strings\n"
                "such as project, configuration, sample_id, plan, plan_args, spriority, apriority"
            )
            return
    try:
        for k, r in zip(sort_by, rev):
            list_out = sorted(list_out, key=itemgetter(switcher[k]), reverse=r)
    except KeyError:
        print(
            "sort_by needs to be a list of strings\n"
            "such as project, configuration, sample_id, plan, plan_args, spriority, apriority"
        )
        return
    plan_list = []
    for step in list_out:
        kwargs = step[6]["kwargs"]
        sample_md = step[5]
        # del sample_md['acquisitions']
        if hasattr(rsoxs_queue_plans, step[3]):
            kwargs.update(
                {
                    "configuration": step[2],
                    "sample_md": sample_md,
                    "acquisition_plan_name": step[3],
                }
            )
            plan = {"name": "run_queue_plan", "kwargs": kwargs, "item_type": "plan"}
            plan_list.append(plan)
        else:
            print(f"Invalid acquisition:{step[3]}, skipping")
    if retract_when_done:
        plan_list.append({"name": "all_out", "item_type": "plan"})
    return plan_list
