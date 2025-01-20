##

import pandas as pd
from ..startup import rsoxs_config

Keys_SamplesDictionary = ["sample_id",
                          "proposal_id",
                          "notes"]
Keys_AcquisitionsDictionary = ["sample_id",
                               "plan_name",
                               "energy_parameters",
                               "notes"]

def load_spreadsheet(path, update_configuration = False):
    """
    Loads excel spreadsheet and loads sample metadata into memory.
    """
    
    Samples_df = pd.read_excel(path, sheet_name="Samples")
    Samples_dict = Samples_df.to_dict(orient="records")
    Configuration = []
    for Index, Sample in enumerate(Samples_dict):
        Sample_dict = {}
        for Index, Key in enumerate(Keys_SamplesDictionary): Sample_dict[Key] = Sample[Key]
        ## TODO: sanitize sample parameters.  Make a separate function for this.
        Sample_dict["acquisitions"] = []
        Configuration.append(Sample_dict)

    Acquisitions_df = pd.read_excel(path, sheet_name="Acquisitions")
    Acquisitions_dict = Acquisitions_df.to_dict(orient="records")
    for Index, Acquisition in enumerate(Acquisitions_dict):
        Acquisitions_dict = {}
        for Index, Key in enumerate(Keys_AcquisitionsDictionary): Acquisitions_dict[Key] = Acquisition[Key]
        ## TODO: sanitize acquisition parameters.  Make a separate function for this.
        for Index, Sample in enumerate(Configuration):
            if Sample["sample_id"] == Acquisitions_dict["sample_id"]: Configuration[Index]["acquisitions"].append(Acquisitions_dict)
    
    ## TODO: validate spreadsheet version?  Probably unnecessary if sanitized correctly?

    if update_configuration: rsoxs_config["bar"] = Configuration
