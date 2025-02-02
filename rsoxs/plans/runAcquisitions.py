##

from rsoxs.Functions.alignment import load_configuration, load_samp, rotate_now
from rsoxs.HW.energy import set_polarization
from rsoxs.plans.rsoxs import variable_energy_scan, rsoxs_step_scan
from rsoxs_scans.defaultParameters import *


def sanitizeAcquisition(
       acquisition 
):
    if isinstance(acquisition["energyListParameters"], str): acquisition["energyListParameters"] = energyListParameters[acquisition["energyListParameters"]]

    return acquisition


def runAcquisitions_Single(
        acquisition,
        dryrun = True
):
    
    acquisition = sanitizeAcquisition(acquisition)
    print("\n\n")
    print("Loading instrument configuration: " + str(acquisition["configurationInstrument"]))
    if dryrun == False: yield from load_configuration(acquisition["configurationInstrument"])

    ## TODO: set up diodes to high or low gain
    ## But there are issues at the moment with setup_diode_i400() and most people don't use this, so leave it for now

    print("Loading sample: " + str(acquisition["sampleID"]))
    if dryrun == False: yield from load_samp(acquisition["sampleID"]) ## TODO: what is the difference between load_sample (loads from dict) and load_samp(loads from id or number)?  Can they be consolidated?

    ## TODO: set temperature if needed, but this is lowest priority

    for indexAngle, angle in enumerate(acquisition["sampleAngles"]):
        print("Rotating to angle: " + str(angle))
        if dryrun == False: yield from rotate_now(angle) ## TODO: What is the difference between rotate_sample and rotate_now?

        for indexPolarization, polarization in enumerate(acquisition["polarizations"]):
            print("Setting polarization: " + str(polarization))
            if dryrun == False: yield from set_polarization(polarization)
            ## TODO: need to figure out how to incorporate sample frame polarization
            
            print("Running scan: " + str(acquisition["scanType"]))
            if dryrun == False: 
                if acquisition["scanType"] == "nexafs_step": yield from variable_energy_scan(*acquisition["energyListParameters"], dwell=acquisition["exposureTime"], group_name=acquisition["groupName"])
                if acquisition["scanType"] == "rsoxs_step": yield from rsoxs_step_scan(*acquisition["energyListParameters"], dwell=acquisition["exposureTime"], n_exposures=acquisition["exposuresPerEnergy"], group_name=acquisition["groupName"])
    



def runAcquisitions_Queue(
        queue, ## List of acquisition dictionaries
        dryrun = True,
        sortBy = {}
        ):
    ## Run a series of single acquisitions

    print("Starting queue")

    ## TODO: sort queue by priority, group, configuration, etc.

    for index, acquisition in enumerate(queue):
        yield from runAcquisitions_Single(acquisition=acquisition, dryrun=dryrun)

    print("Finished queue")

    ## TODO: get time estimates for individual acquisitions and the full queue

"""
## Example queue dictionary
myQueue = [

{
"sampleID": "OpenBeam_NIST",
"configurationInstrument": "WAXS",
"scanType": "rsoxs_step",
"energyListParameters": "carbon_NEXAFS",
"exposureTime": 0.1,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"polarizationFrame": "lab",
"polarizations": [0],
"groupName": "Test",
"priority": 1,
},

{
"sampleID": "HOPG_NIST",
"configurationInstrument": "WAXSNEXAFS",
"scanType": "nexafs_step",
"energyListParameters": "carbon_NEXAFS",
"exposureTime": 1,
"exposuresPerEnergy": None,
"sampleAngles": [20],
"polarizationFrame": "lab",
"polarizations": [90],
"groupName": "Test",
"priority": 1,
},

]








"""