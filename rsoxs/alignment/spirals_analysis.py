# imports
import copy
import numpy as np


def pickLocationsFromSpirals( ## Intended to be an updated, data-security-compliant version of resolve_spirals.  Probably will just have this function pick spots for one sample and then it can be rerun for multiple samples.  That way, not all spirals have to be resolved in one go.
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
    ## TODO: update try/except and update to solid_sample_x
    try: locations_OutboardInboard = scanSurvey["primary"]["data"]["RSoXS Sample Outboard-Inboard"].read()
    except KeyError: locations_OutboardInboard = scanSurvey["primary"]["data"]["manipulator_x"].read()
    
    try: locations_DownUp = scanSurvey["primary"]["data"]["RSoXS Sample Up-Down"].read()
    except KeyError: locations_DownUp = scanSurvey["primary"]["data"]["manipulator_y"].read()
    
    try: locations_UpstreamDownstream = scanSurvey["baseline"]["data"]["RSoXS Sample Downstream-Upstream"][0]
    except KeyError: locations_UpstreamDownstream = scanSurvey["baseline"]["data"]["manipulator_z"][0]

    try: locations_Theta = scanSurvey["baseline"]["data"]["RSoXS Sample Rotation"][0]
    except KeyError: locations_Theta = scanSurvey["baseline"]["data"]["manipulator_r"][0]
    
    
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
    return configuration


## How to use pick_locations_from_spirals
"""
## Install rsoxs codebase and pyhyper

!pip install "git+https://github.com/NSLS-II-SST/rsoxs_scans.git@rsoxsIssue18_SimplifyScans"
!pip install "git+https://github.com/usnistgov/PyHyperScattering.git#egg=PyHyperScattering[bluesky]"
"""

"""
## Imports

from rsoxs_scans.configuration_load_save_sanitize import load_configuration_spreadsheet_local, save_configuration_spreadsheet_local
from rsoxs_scans.spiralsAnalysis import pickLocationsFromSpirals

import PyHyperScattering as phs
print(f'Using PyHyper Version: {phs.__version__}')


Loader = phs.load.SST1RSoXSDB(corr_mode="none") #Loader = phs.load.SST1RSoXSDB(corr_mode='none', catalog_kwargs={"username":"pketkar"}) #Loader = phs.load.SST1RSoXSDB(corr_mode='none')
Catalog = Loader.c
Catalog
"""


"""
## Use the function

pathConfiguration = r"/content/drive/Shareddrives/NISTPostdoc/CharacterizationData/BeamTime/20250123_SST1_Commissioning_Jordan-Sweet/DataAnalysis/in_2025-02-01_UpdatedBar.xlsx"
configuration = load_configuration_spreadsheet_local(pathConfiguration) 

configuration = pickLocationsFromSpirals(configuration=configuration,
                            sampleID="OpenBeam_NIST",
                            catalog=Catalog,
                            scanID_Survey=91532,
                            locationsSelected_Indices=[0, 8, 15]
                            )

save_configuration_spreadsheet_local(configuration=configuration, file_label="SpiralSpotsPicked", file_path=r"/content/drive/Shareddrives/NISTPostdoc/CharacterizationData/BeamTime/20250123_SST1_Commissioning_Jordan-Sweet/DataAnalysis/")

"""