##

from rsoxs.Functions.alignment import load_configuration, load_samp, rotate_now
from rsoxs.HW.energy import set_polarization
from rsoxs.plans.rsoxs import energyScan, energyScan_withWAXSCamera
from rsoxs.HW.detectors import snapshot
from rsoxs_scans.defaultParameters import *


def sanitizeAcquisition(
       acquisition 
):
    ## TODO: some of this sanitizaiton should happen while importing the spreadsheet.  But the same sanitization should apply even if I were to feed in a dictionary directly into bsui.

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

    for indexAngle, sampleAngle in enumerate(acquisition["sampleAngles"]):
        print("Rotating to angle: " + str(sampleAngle))
        if dryrun == False: yield from rotate_now(sampleAngle) ## TODO: What is the difference between rotate_sample and rotate_now?

        for indexPolarization, polarization in enumerate(acquisition["polarizations"]):
            print("Setting polarization: " + str(polarization))
            if dryrun == False: yield from set_polarization(polarization)
            ## TODO: need to figure out how to incorporate sample frame polarization
            
            print("Running scan: " + str(acquisition["scanType"]) + " with " + str(acquisition["energyListParameters"]) + " energy list")
            if dryrun == False: 
                if acquisition["scanType"] == "nexafs_step": yield from energyScan(*acquisition["energyListParameters"], dwell=acquisition["exposureTime"], group_name=acquisition["groupName"])
                
                if acquisition["scanType"] == "rsoxs_step": 
                    ## TODO: per_steps probably needs to be adjusted to fix RSoXS energy scans.  Ad hoc solution for now is to take a snapwaxs at the same exposure time before each energy scan.
                    ## See 20250202 troubleshooting where the issue was reproduced
                    yield from snapshot(secs=acquisition["exposureTime"])

                    yield from energyScan_withWAXSCamera(*acquisition["energyListParameters"], dwell=acquisition["exposureTime"], n_exposures=acquisition["exposuresPerEnergy"], group_name=acquisition["groupName"])

                ## TODO: add count scans so that the queue can be tested without beam.  Also add a corresponding configuration where everything is retracted, so that I can test the full queue.  And we could load a spreadsheet adn duplicate a sample so that the sample manipulation motors don't move.
                ## TODO: add spiral scans

                ## TODO: Mark scan as done in spreadsheet
                ## TODO: Save a log of timestamps, maybe in the config and then save in the spreadsheet
    



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

    ## TODO: get time estimates for individual acquisitions and the full queue.  Import datetime and can print timestamps for when things actually completed.

"""
## Example queue dictionary
myQueue = [

{
"sampleID": "OpenBeam_NIST",
"configurationInstrument": "WAXS",
"scanType": "rsoxs_step",
"energyListParameters": (250, 255, 1),
"exposureTime": 0.01,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"polarizationFrame": "lab",
"polarizations": [0],
"groupName": "Test",
"priority": 1,
},

]





ReferenceQueue = [

{
"sampleID": "OpenBeam",
"configurationInstrument": "WAXSNEXAFS",
"scanType": "nexafs_step",
"energyListParameters": "carbon_NEXAFS",
"exposureTime": 1,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"polarizationFrame": "lab",
"polarizations": [0, 90],
"groupName": "IBM_NEXAFS",
"priority": 1,
},
{
"sampleID": "OpenBeam",
"configurationInstrument": "WAXSNEXAFS",
"scanType": "nexafs_step",
"energyListParameters": "oxygen_NEXAFS",
"exposureTime": 1,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"polarizationFrame": "lab",
"polarizations": [0, 90],
"groupName": "IBM_NEXAFS",
"priority": 1,
},
{
"sampleID": "OpenBeam",
"configurationInstrument": "WAXSNEXAFS",
"scanType": "nexafs_step",
"energyListParameters": "fluorine_NEXAFS",
"exposureTime": 1,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"polarizationFrame": "lab",
"polarizations": [0, 90],
"groupName": "IBM_NEXAFS",
"priority": 1,
},
{
"sampleID": "HOPG",
"configurationInstrument": "WAXSNEXAFS",
"scanType": "nexafs_step",
"energyListParameters": "carbon_NEXAFS",
"exposureTime": 1,
"exposuresPerEnergy": 1,
"sampleAngles": [20],
"polarizationFrame": "lab",
"polarizations": [90],
"groupName": "IBM_NEXAFS",
"priority": 1,
},

]


def overnightRuns():
    RE(runAcquisitions_Queue(queue=IBMQueue, dryrun=False))

    for repeat in np.arange(0, 1000, 1): RE(runAcquisitions_Queue(queue=ReferenceQueue, dryrun=False))

"""