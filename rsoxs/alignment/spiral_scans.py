import copy

## The following imports need to be done outside Bluesky
#from rsoxs_scans.spreadsheets import load_samplesxlsx, save_samplesxlsx
#import PyHyperScattering as phs


def pick_locations_from_spirals( ## Intended to be an updated, data-security-compliant version of resolve_spirals.  Probably will just have this function pick spots for one sample and then it can be rerun for multiple samples.  That way, not all spirals have to be resolved in one go.
        configuration, ## Up-to-date spreadsheet with current sample locations.  TODO: maybe load sheet separately and then pick spots and then save out a new sheet
        sampleID,
        catalog,
        scanID_Survey, ## Maybe the more generic thing to call it is a survey scan
        locationsSelected_Indices,
        
):
    
    ## TODO: Consider making this a more generic function that picks a sample location from some series scan.  For spiral scans, it picks x and y location, but for an angle series, it could pick from there as well
    ## Can do something like try/except where I try to find the coordinate from primary but otherwise, find it from the baseline

    
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
