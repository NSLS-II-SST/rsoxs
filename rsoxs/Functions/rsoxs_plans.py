import bluesky.plan_stubs as bps
from sst_funcs.printing import run_report
from rsoxs_scans.acquisitions import dryrun_bar
from .alignment import load_sample, load_configuration, move_to_location,spiralsearch
from ..HW.lakeshore import tem_tempstage
from ..HW.signals import High_Gain_diode_i400, setup_diode_i400
from .energyscancore import NEXAFS_fly_scan_core, new_en_scan_core

run_report(__file__)

actions = {
    'load_configuration', # high level load names RSoXS configuration
    'rsoxs_scan_core',  # high level run a single RSoXS plan
    'temp', # change the temperature
    'spiral_scan_core',  # high spiral scan a sample
    'move', # move an ophyd object
    'load_sample', # high level load a sample
    'message', # message the user - no action
    'diode_low', # set diodes range setting to low
    'diode_high', # set diode range setting to high
    'nexafs_scan_core', # high level run a single NEXAFS scan
    'error'# raise an error - should never get here.
    }
motors = {
    'temp_ramp_rate':tem_tempstage.ramp_rate
}


def run_bar(
    sort_by=["sample_num"],
    rev=[False],
    print_dry_run = True):
    queue = dryrun_bar(sort_by=sort_by, rev=rev, print_dry_run=print_dry_run)
    print("Starting Queue")
    for queue_step in queue:
        yield from run_queue_step(queue_step)
    print("End of Queue")

def run_queue_step(step):
    print(f"\n----- starting acquisition step {step['acq_step']} in queue step {step['queue_step']}-----\n")
    print(step['description'])
    if step['action'] == 'diode_low':
        yield from setup_diode_i400()
    if step['action'] == 'diode_high':
        yield from High_Gain_diode_i400()
    if step['action'] == 'load_configuration':
        yield from load_configuration(step['kwargs']['configuration'])
    if step['action'] == 'load_sample':
        yield from load_sample(step['kwargs']['sample'])
    if step['action'] == 'temp':
        if step['kwargs']['wait']:
            yield from bps.mv(tem_tempstage, step['kwargs']['temp'])
        else:
            yield from bps.mv(tem_tempstage.setpoint, step['kwargs']['temp'])
    if step['action'] == 'temp':
        if step['kwargs']['wait']:
            yield from bps.mv(tem_tempstage, step['kwargs']['temp'])
        else:
            yield from bps.mv(tem_tempstage.setpoint, step['kwargs']['temp'])
    if step['action'] == 'move':
        yield from bps.mv(motors[step['kwargs']['motor']], step['kwargs']['position'])
        # use the motors look up table above to get the motor object by name
    if step['action'] == 'spiral_scan_core':
        yield from spiralsearch(**step['kwargs'])
    if step['action'] == 'nexafs_scan_core':
        yield from NEXAFS_fly_scan_core(**step['kwargs'])
    if step['action'] == 'rsoxs_scan_core':
        yield from new_en_scan_core(**step['kwargs'])
    print(f"\n----- finished acquisition step {step['acq_step']} in queue step {step['queue_step']}-----\n")
    
    

    
