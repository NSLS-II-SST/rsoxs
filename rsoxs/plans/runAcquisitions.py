##
import numpy as np
import copy

from rsoxs.Functions.alignment import load_configuration, load_samp, rotate_now
from rsoxs.HW.energy import set_polarization
from rsoxs.plans.rsoxs import timeScan, spiralScan, energyScan, energyScan_with2DDetector
from rsoxs.HW.detectors import snapshot
from ..startup import rsoxs_config
from rsoxs_scans.configurationLoadSaveSanitize.py import gatherAcquisitionsFromConfiguration, sanitizeAcquisition
from rsoxs_scans.defaultEnergyParameters import *



def runAcquisitions_Queue(
        configuration = rsoxs_config["bar"], ## List of acquisition dictionaries
        dryrun = True,
        sortBy = {}
        ):
    ## Run a series of single acquisitions

    acquisitions = gatherAcquisitionsFromConfiguration(configuration)
    ## TODO: Not sure if I need to sanitize again here, but might be safer
    queue = acquisitions ## TODO: not ready yet, but make a function in rsoxs_local for sorting by priority, group, configuration, etc.
    
    print("Starting queue")

    for indexAcquisition, acquisition in enumerate(queue):
        yield from runAcquisitions_Single(acquisition=acquisition, dryrun=dryrun)
        queue[indexAcquisition]["acquireStatus"] = "Finished"
        ## TODO: Save updated status in rsoxs_config so that when I save sheet, these statuses get saved

    print("\n\nFinished queue")

    ## TODO: get time estimates for individual acquisitions and the full queue.  Import datetime and can print timestamps for when things actually completed.

"""
def sanitizeAcquisition(
       acquisition 
):
    ## TODO: some of this sanitizaiton should happen while importing the spreadsheet.  But the same sanitization should apply even if I were to feed in a dictionary directly into bsui.

    if isinstance(acquisition["energyListParameters"], str): acquisition["energyListParameters"] = energyListParameters[acquisition["energyListParameters"]]

    return acquisition
"""

def runAcquisitions_Single(
        acquisition,
        dryrun = True
):
    
    acquisition = sanitizeAcquisition(acquisition) ## This would be run before if a spreadsheet were loaded, but now it will ensure the acquisition is sanitized in case the acquisition is run in the terminal

    parameter = "configurationInstrument"
    if not np.isnan(acquisition[parameter]):
        print("\n\n Loading instrument configuration: " + str(acquisition[parameter]))
        if dryrun == False: yield from load_configuration(acquisition[parameter])

    ## TODO: set up diodes to high or low gain
    ## But there are issues at the moment with setup_diode_i400() and most people don't use this, so leave it for now

    parameter = "sample_id"
    if not np.isnan(acquisition[parameter]):
        print("Loading sample: " + str(acquisition[parameter]))
        if dryrun == False: yield from load_samp(acquisition[parameter]) ## TODO: what is the difference between load_sample (loads from dict) and load_samp(loads from id or number)?  Can they be consolidated?

    ## TODO: set temperature if needed, but this is lowest priority

    for indexAngle, sampleAngle in enumerate(acquisition["sampleAngles"]):
        print("Rotating to angle: " + str(sampleAngle))
        if dryrun == False: yield from rotate_now(sampleAngle) ## TODO: What is the difference between rotate_sample and rotate_now?
        
        ## Handle scans without energy variation
        if acquisition["scanType"] == ("time" or "spiral"):
            ## If a timeScan or spiral is being run when I don't have beam (during shutdown or when another station is using beam), I don't want to make any changes to the energy or polarization
            ## This assumes I only have one polarization or energy listed for a timeScan.  If I had more, makes sense to run NEXAFS scan instead.
            if not np.isnan(acquisition["polarizations"]):
                polarization = acquisition["polarizations"][0]
                print("Setting polarization: " + str(polarization))
                if dryrun == False: yield from set_polarization(polarization)
            ## TODO: do the same for energy
            print("Running scan: " + str(acquisition["scanType"]))
            acquisition["acquireStatus"] = "Started"
            if dryrun == False:
                if acquisition["scanType"] == "time":
                    yield from timeScan(
                        n_exposures=acquisition["exposuresPerEnergy"], 
                        dwell=acquisition["exposureTime"]
                        )
                if acquisition["scanType"] == "spiral": 
                    yield from spiralScan(
                        stepsize=acquisition["spiralDimensions"][0], 
                        widthX=acquisition["spiralDimensions"][1], 
                        widthY=acquisition["spiralDimensions"][2],
                        n_exposures=acquisition["exposuresPerEnergy"], 
                        dwell=acquisition["exposureTime"]
                        )
        
        if acquisition["scanType"] == ("nexafs" or "rsoxs"):
            for indexPolarization, polarization in enumerate(acquisition["polarizations"]):
                print("Setting polarization: " + str(polarization))
                if dryrun == False: yield from set_polarization(polarization)
                ## TODO: need to figure out how to incorporate sample frame polarization
                
                print("Running scan: " + str(acquisition["scanType"]) + " with " + str(acquisition["energyListParameters"]) + " energy list")
                acquisition["acquireStatus"] = "Started"
                if dryrun == False: 
                    ## TODO: there might be a way to gather the majority of these parameters into a list and feed them in that way?
                    if acquisition["scanType"] == "nexafs": 
                        yield from energyScan(
                            *acquisition["energyListParameters"], 
                            dwell=acquisition["exposureTime"], 
                            group_name=acquisition["groupName"]
                            )
                    
                    if acquisition["scanType"] == "rsoxs": 
                        ## TODO: per_steps probably needs to be adjusted to fix RSoXS energy scans.  Ad hoc solution for now is to take a snapwaxs at the same exposure time before each energy scan.
                        ## See 20250202 troubleshooting where the issue was reproduced
                        yield from snapshot(secs=acquisition["exposureTime"])

                        yield from energyScan_with2DDetector(
                            *acquisition["energyListParameters"], 
                            dwell=acquisition["exposureTime"], 
                            n_exposures=acquisition["exposuresPerEnergy"], 
                            group_name=acquisition["groupName"]
                            )

                    
                    ## TODO: Mark scan as done in spreadsheet
                    ## TODO: Save a log of timestamps, maybe in the config and then save in the spreadsheet




def markCurrentAcquisitionAsDone():
    ## TODO: grab current acquisition from RE.md or rsoxs_config.  Then mark as done in rsoxs_config so that queue will move onto the next sample.
    ## Especially useful for spirals.  Instead of having it inside the spiral function.  Or maybe just code it for spirals specifically...
    return ""
"""
## Example queue dictionary
myQueue = [

{
"sampleID": "OpenBeam_NIST",
"configurationInstrument": "WAXS",
"scanType": "rsoxs_step",
"energyListParameters": (250, 255, 1),
"polarizationFrame": "lab",
"polarizations": [0],
"exposureTimewidthX=acquisition["spiralDimensions"][1],": 0.01,
"exposuresPerEnergy": 1,
"sampleAngles": [0],
"spiralDimensions": [0.3, 1.8, 1.8], ## [step_size, diameter_x, diameter_y], useful if our windows are rectangles, not squares
"groupName": "Test",
"priority": 1,
},
## TODO: maybe add a kwarg column?  So the spreadsheet isn't too long?

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