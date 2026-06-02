##
import numpy as np

from rsoxs.configuration_setup.configurations_instrument import load_configuration
from rsoxs.Functions.alignment import (
    load_samp, 
    rotate_now
    )
from rsoxs.HW.energy import set_polarization
from nbs_bl.plans.scans import nbs_list_scan
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from nbs_bl.hw import (
    en,
    mir3,
    slitc_cam,
)

import bluesky.plan_stubs as bps
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl




def m3_sweep(
        polarizations = [0, 90],
        energies = None,
        m3_xs = None,
        m3_pitches = None,
        configuration = "WAXSNEXAFS",
        sample_id = "OpenBeam",
):
    """
    Sweeps M3 pitch across different M3 x, energies, and polarizations.
    If the M3 pitch and x at which the maximum flux occurs stays the same across energies, then upstream M2/PGM are well-aligned.
    If not, then the M2/PGM roll may need to be adjusted via the manual wobble stick.

    TODO: Make a version that uses flymax.

    Args:
        polarizations: list of float values between -1 and 180
            List of polarizations (in degrees) to scan.
            Defaults to [0, 90]
        energies: list of float values between 70 and 2200
            List of energies (eV) to scan.
            Defaults to energies_250grating_default or energies_1200grating_default list to span energies covered by grating.
        m3_xs: list of float values
            List of inboard-outboard positions of M3 mirror.
        m3_pitches: list of float values
            List of M3 rotations about vertical axis.
        configuration: str
            Instrument configuration at which to run the scan.
        sample_id: str
            Sample to load before running the scan.



    Returns:
        Sweep of M3 settings across different beamline settings.


    Raises:


    Examples:
        For user beam time startup and before energy calibration, run a smaller subset such as RE(m3_sweep(polarizations=[0], energies=[270], m3_xs=[24.2]))
        
        For commissioning studies and after energy calibration, run the default parameters using RE(m3_sweep()).
        
        
    """

    ## Set input variables
    ## Using late binding method so that any inputs defined in the iPython terminal override defaults.
    if energies is None:
        energies_250grating_default = np.concatenate((
            np.array([90, 110, 130, 150, 200, 250]),
            np.arange(300, 1100, 100)
        ))
        energies_1200grating_default = np.concatenate((
            energies_250grating_default,
            np.arange(1100, 2100, 100)
        ))
        energies = energies_250grating_default
    if m3_xs is None:
        ## Sweeps from inside out because likely, the center x value is an okay one to start.
        
        ## Define bounds and center point
        low, high, step = 24.0, 24.5, 0.05
        center = 24.2
        ## Make array in forward order
        m3_xs = np.arange(
            start = low, 
            stop = high + step/2, 
            step = step
            )
        ## ARrange array to go outward from center
        m3_xs = m3_xs[np.argsort(np.abs(m3_xs - center))]
        
    if m3_pitches is None:
        m3_pitches = np.arange(7.6, 8, 0.002)

    ## Store previous settings
    m3_x_start = mir3.x.read()['SST 1 Mirror 3 fmb_x_setpoint']["value"] #m3_x_start = 24.2
    m3_pitch_start = mir3.pitch.read()['SST 1 Mirror 3 fmb_pitch_setpoint']["value"] #m3_pitch_start = 7.78
    ## TODO: probably can do .name or something instead of typing hard-coded text?

    
    yield from load_configuration(configuration)
    ## TODO: Open slits 2 and 3 at this stage?  And then restore configuration at the end?
    yield from load_samp(sample_id)

    ## TODO: 2026-05-23 - make a general sweeping function using itertools.products
    ## Allows loop order to be changed
    ## Take input dictionary of what parameters to sweep and what detectors to use and whatnot
    ## Use that general function for m3 sweeping and also energy calibration validation with HOPG scans with different cffs
    print("Starting M3 sweep.")
    for polarization in polarizations:
        print("Setting polarization: " + str(polarization))
        yield from set_polarization(polarization)
        for energy in energies:
            #if polarization == 90 and energy < 790: continue
            print("Setting energy: " + str(energy) + " eV")
            yield from bps.mv(en, energy)
            for m3_x in m3_xs:
                print("Setting M3 x = " + str(m3_x))
                yield from bps.mv(mir3.x, m3_x)

                ## Scan in forward and reverse directions.
                ## Location of maximum will change based on scan direction.
                ## TODO: Check if maximum value changes with direction; i.e., is it consistently lower/higher in one direction
                yield from nbs_list_scan(mir3.pitch, 
                                         m3_pitches, 
                                         extra_dets=[slitc_cam],
                                         )
                yield from nbs_list_scan(mir3.pitch, 
                                         m3_pitches[::-1], ## Reverse direction
                                         extra_dets=[slitc_cam],
                                         )
                ## Including slitc_cam to get image of the beam
                ## Exposure time should be 0.00002 s


    ## Restore old settings
    yield from set_polarization(0)
    yield from bps.mv(en, 270)
    yield from bps.mv(mir3.x, m3_x_start)
    yield from bps.mv(mir3.pitch, m3_pitch_start)