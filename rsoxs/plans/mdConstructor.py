import copy
from rsoxs.startup import RE





def mdToUpdateConstructor(extraMD={}):
    md_ToUpdate = copy.deepcopy(extraMD)

    ## nbs-bl removes sample_name and sample_id here: https://github.com/xraygui/nbs-bl/blob/master/nbs_bl/plans/scan_decorators.py#L198C17-L201C79
    md_ToUpdate["sample_name"] = RE.md["sample_name"]
    md_ToUpdate["sample_id"] = RE.md["sample_id"]

    ## TODO: construct more descriptive plan names for energy scan based on which energies are used
    if "energyScan" in md_ToUpdate["scanType"]: md_ToUpdate["plan_name"] = md_ToUpdate["scanType"]
    else: md_ToUpdate["plan_name"] = md_ToUpdate["scanType"]


    return md_ToUpdate