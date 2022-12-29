import numpy as np
import bluesky.plan_stubs as bps
from .energyscancore import en_scan_core,new_en_scan_core
from ..Functions.alignment import rotate_now,get_sample_dict,rotate_sample
from ..HW.lakeshore import tem_tempstage
from ..HW.signals import High_Gain_diode_i400,setup_diode_i400
from sst_funcs.printing import run_report, read_input
from copy import deepcopy

run_report(__file__)


def rsoxs_plan(edge, exposure = 1, frames='full', intervals=None, polarizations = [0],angles = None,grating='rsoxs',diode_range='high',temperatures=None,temp_ramp_speed=10,temp_wait=True,sim_mode=0, md=Nome,**kwargs):
    energies = get_energies(edge,frames,intervals,sim_mode)
    times, time = construct_exposure_times(energies,exposure,sim_mode)
    if isinstance(temperatures,list):
        yield from bps.mv(tem_tempstage.ramp_rate,temp_ramp_speed)
    if diode_range=='high':
        yield from setup_diode_i400()
    elif diode_range=='low':
        yield from High_Gain_diode_i400()
    if max(energies) > 1200 and grating == 'rsoxs':
        raise ValueError('energy is not appropriate for this grating')

    # construct the locations list
    samp = get_sample_dict()
    locations = []
    for angle in angles:
        samp['angle'] = angle
        rotate_sample(samp) # doesn't rotate the actual sample yet, just does the math to update the location of the sample
        locations = locations.append([deepcopy(samp['location'])]) # read that rotated location as a location for the acquisition
    ret_text = yield from new_en_scan_core( grating=grating,
                                            energies=energies,
                                            times=times,
                                            polarizations=polarizations,
                                            locations=locations,
                                            temperatures=temperatures,
                                            md=md,
                                            sim_mode=sim_mode)

    if sim_mode:
        total_time = time * len(polarizations) # time is the estimate for a single energy scan
        total_time += 30*len(polarizations) # 30 seconds for each polarization change
        if isinstance(angles,list):
            total_time *= len(angles)
            total_time += 30*len(angles) # 30 seconds for each angle change
        if isinstance(temperatures,list):
            total_time *= len(temperatures)
        return ret_text, total_time
    return ret_text

# TODO : write NEXAFS equivalent .... multiple scans for different angles?
# TODO : function that calls this and the NEXAFS equivalent


def get_energies(edge,frames = "full", intervals = None,sim_mode=False):
    """
    creates a usable list of energies, given an edge an estimated number of frames (energies) and intervals
    Args:
        edge: String or tuple of 2 or more numbers or number
            if string, this should be a key in the lookup tables refering to an absorption edge energy
            if tuple, this is the thresholds of the different ranges, i.e. start of pre edge, start of main edge, start of post edge, end etc.
                the length of the tuple should correspond to 1- the length of intervals (or a default can be chosen if between 2 and 6 thresholds are given)
            if number, just return a single element array of that number - this is a very silly way to make such an array
        frames: String or Number
            if string, this should be in the lookup table of standard lengths for scans
            if number, this is the aim for the number of exposures needed in the region
                the algorithm will almost always exceed this estimate slightly
                precise numbers of exposures will not be possible using this function at this time
        intervals: string or tuple of numbers
            if string, this should be in the lookup table of standard intervals
            if a tuple, this must have one less element than the edge tuple (either explicitely entered or from the lookup table)
                the values should not be thought of as energy steps, but the ratio of energy steps between the different regions defined by edge
        sim_mode: ignored currently, but could be expanded if this function ever does something that should only be simulated
                
    benefits of this algorithm are:
    1.) the number of frames is always known, at least approximately - this is the main cause of confusion with the existing system
    2.) flexibility is maintained - any energy scan can be defined here, and with effort, even very precise energy choices are possible with just three relatively plain text inputs
    3.) estimation of time should be considerably more accurate than looking up previous scans.  Here we can have a very simple algorithm to estimate the time of a scan
    4.) maintains very simple standard scans that will always be the same - if you don't change the inputs, and only choose an edge, or a standard frame the same energies will be taken each time
    downsides:
    1.) the exact energies taken might not be obvious.  all of the exact energies in the edge definition will always be taken, but the exact step between is not necessarily forseeable
    
    definite additions before put into practice
    1.) define all look up tables in persistant database dict.  allow new definitions.  defaults overwritten by these tables on BSUI load (through redis for now)
    2.) add sim mode, where no errors are thrown, but explainations / estimations are returned as a string - return number of exposures for time estimation
    3.) no plotting?  or maybe just as option when in sim mode
    
    possible additions:
    1.) exposure times - added this as seperate function below
    2.) direct time estimation output - added to function for exposure times below
    """
    
    edge_names = {"c":"Carbon",
              "carbonk": "Carbon",
              "ck": "Carbon",
              "n": "Nitrogen",
              "nitrogenk": "Nitrogen",
              "nk": "Nitrogen",
              "f": "Fluorine",
              "fluorinek": "Fluorine",
              "fk": "Fluorine",
              "o": "Oxygen",
              "oxygenk": "Oxygen",
              "ok": "Oxygen",
              "ca": "Calcium",
              "calciumk": "Calcium",
              "cak": "Calcium",
             }


     # these define the default edges of the intervals
    edges = {"carbon":(250,270,282,287,292,305,350),
             "oxygen":(510,525,540,560),
             "fluorine":(670,680,690,700,740),
             "aluminium":(1540,1560,1580,1600),
             "nitrogen":(380,397,407,440),
             "zincl": (1000,1015,1035,1085),
             "sulfurl":(150,160,170,200),
             "calcium":(320,340,345,349,349.5,352.5,353,355,360,380)
            }
     # these are the default interval ratios for each section
    intervals_table = {"carbon":(5,1,.1,.2,1,5),
                     "carbon nonaromatic":(5,1,.2,.1,1,5),
                     "default 4":(2,.2,2),
                     "default 5":(2,.2,.6,2),
                     "default 6":(2,.6,.2,.6,2),
                     "default 2":(2,),
                     "default 3":(2,.2),
                     "calcium": (5,1,0.5,0.1,0.25,0.1,0.5,1,5),
                    }

    frames_table = {"full": 112,
              "short":56,
              "very short":40,
             }
    edge_input = edge
    singleinput = False
    valid=True
    valid_text = ""
    if isinstance(edge,str):
        if edge.lower() in edge_names.keys():
            edge = edge_names[edge.lower()]
            edge_input = edge.lower()
        if edge.lower() in edges.keys():
            edge = edges[edge.lower()]
    if isinstance(edge_input,(float,int)):
        edge = (edge_input,edge_input)
        singleinput = True
    if not isinstance(edge,tuple):
        valid = False
        valid_text += f"invalid edge {edge} - no key of that name was found\n"
    
    if isinstance(frames,str):
        if frames.lower() in frames_table.keys():
            frames = frames_table[frames.lower()]
    if not isinstance(frames, (int,float)):
        valid = False
        valid_text += f"frame number {frame} was not found or is not a valid number\n"
    
    if intervals == None:
        if str(edge_input).lower() in intervals_table.keys():
            intervals = intervals_table[edge_input.lower()]
        elif f"default {len(edge)}" in intervals_table.keys():
            intervals = intervals_table[f"default {len(edge)}"]
        else:
            intervals = (1,)*(len(edge)-1)
    else:
        if not isinstance(intervals,(tuple,int,float)):
            intervals = intervals_table[intervals]
    if not isinstance(intervals,(tuple,int,float)):
        valid = False
        valid_text += f"invalid intervals {intervals}\n"
    if len(intervals) + 1 != len(edge):
        valid = False
        valid_text += f'got the wrong number of intervals {len(intervals)} expected {len(edge)-1}\n'
    
    if not valid:
        raise ValueError(valid_text)
    steps = 0
    multiple = 1
    numpnts = np.zeros_like(intervals)
    for i, interval in enumerate(intervals):
        numpnts[i] = np.round(np.abs(edge[i+1] - edge[i])/(interval*multiple))
    steps =sum(numpnts)
    multiple  *= steps / frames # if there are too many steps, multiple will reduce to approximately match the frames needed
    steps = 0
    energies = np.zeros(0)
    for i, interval in enumerate(intervals):
        numpnt = max(1,int(np.round(np.abs(edge[i+1] - edge[i])/max(0.01,interval*multiple)))) # get the number of points using this multiple
        at_end = i==len(intervals)-1 and not singleinput # if we are at the end, add the last point (built into linspace)
        energies = np.append(energies,np.around(np.linspace(edge[i],edge[i+1],numpnt+at_end,endpoint=at_end)*2,1)/2) # rounds to nearest 0.05 eV for clarity
    
    return energies


def construct_exposure_times(energies,exposure=1):
    """
    construct an array of exposure times to go with the array of energies input
    also estimate the total time for the scan, using a fixed 
    
    inputs:
        energies: an array or list of energies (floats or ints)
        exposure:
            (number) set all exposure times to this default value
            (list) assume this is a default value and a list of logical tests followed by their respective exposure times
                example [1,('less_than',270),10,('between',285,288),0.1]  the only logical operators allowed are "less_than", "between", "equals", and "greater_than"
    
    outputs:
        times : an array the same length of energies with exposure times
        time : the seconds estimated for the scan
    """
    if not isinstance(energies,np.ndarray):
        raise ValueError("Invalid list of energies")
    times = energies.copy()
    if isinstance(exposure,(float,int)):
        times[:] = float(exposure)
    elif isinstance(exposure,list):
        times[:] = float(exposure[0])
        for test,value in zip(exposure[1::2], exposure[2::2]):
            if test[0] == 'less_than':
                times[energies < test[1]] = value
                #print(f"testing if energies are less than {test[1]} and setting them to {value}")
            elif test[0] == 'greater_than':
                times[energies > test[1]] = value
                #print(f"testing if energies are greater than {test[1]} and setting them to {value}")
            elif test[0] == 'between':
                times[(test[1] < energies) * (energies < test[2])] = value
                #print(f"testing if energies are between {test[1]} and {test[2]} and setting them to {value}")
            elif test[0] == 'equals':
                times[test[1] == energies] = value
                #print(f"testing if energies are equal to {test[1]} and setting them to {value}")
            else:
                raise ValueError(f"Invalid test, only less_than, greater_than, and between are accepted, got {test}")
    time = sum(times) + 4*len(times)
    return times, time





def clean_up_md(arguments={}, md={}, **kwargs):
    del arguments["md"]  # no recursion here!
    del arguments["kwargs"]
    for key in kwargs:
        if type(kwargs[key]) == list:  # dets, signals
            for object in kwargs[key]:
                try:
                    newobject = object.name
                except Exception:
                    newobject = object
                arguments[key] = newobject
        elif key is "energy":
            arguments[key] = kwargs[key].name
        else:
            arguments[key] = kwargs[key]

    if md is None:
        md = {}
    md.setdefault("plan_history", [])
    md["plan_history"].append(
        {"plan_name": arguments["plan_name"], "arguments": arguments}
    )
    md.update(
        {"plan_name": arguments["enscan_type"], "master_plan": arguments["master_plan"]}
    )

def full_iron_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_iron_scan_nd",
    **kwargs
):
    """
    full_iron_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_iron_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(690.0, 700.0, 5.0)
    energies = np.append(energies, np.arange(700.0, 705.0, 1.0))
    energies = np.append(energies, np.arange(705.0, 712.5, 0.25))
    energies = np.append(energies, np.arange(712.5, 725.0, 0.5))
    energies = np.append(energies, np.arange(725.0, 740.0, 1.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_oxygen_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_oxygen_scan_nd",
    **kwargs
):
    """
    full_oxygen_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_oxygen_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(510, 525, 1.0)
    energies = np.append(energies, np.arange(525, 540, 0.2))
    energies = np.append(energies, np.arange(540, 560, 1.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_oxygen_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_oxygen_scan_nd",
    **kwargs
):
    """
    short_oxygen_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_oxygen_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(510, 525, 2.0)
    energies = np.append(energies, np.arange(525, 540, 0.5))
    energies = np.append(energies, np.arange(540, 560, 2.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    # times[energies<525] = 2
    # times[(energies < 540) & (energies >= 525)] = 5
    # times[energies >= 540] = 2
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_zincl_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_zincl_scan_nd",
    **kwargs
):
    """
    short_zincl_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_zincl_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(1000.0, 1015.0, 2.0)
    energies = np.append(energies, np.arange(1015.0, 1035.0, 1.0))
    energies = np.append(energies, np.arange(1035.0, 1085.0, 3.0))
    times = energies.copy()

    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def very_short_oxygen_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="very_short_oxygen_scan_nd",
    **kwargs
):
    """
    very_short_oxygen_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "very_short_oxygen_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(510, 525, 5.0)
    energies = np.append(energies, np.arange(525, 531, 0.5))
    energies = np.append(energies, np.arange(531, 535, 2.0))
    energies = np.append(energies, np.arange(535, 560, 10.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    # times[energies<525] = 2
    # times[(energies < 540) & (energies >= 525)] = 5
    # times[energies >= 540] = 2
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_fluorine_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_fluorine_scan_nd",
    **kwargs
):
    """
    short_fluorine_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_fluorine_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(670.0, 710.0, 1.0)
    # energies = np.append(energies,np.arange(525,540,0.5))
    # energies = np.append(energies,np.arange(540,560,2))
    times = energies.copy()

    # Define exposures times for different energy ranges
    # times[energies<525] = 2
    # times[(energies < 540) & (energies >= 525)] = 5
    # times[energies >= 540] = 2
    times[:] = 1.0
    times *= multiple
    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_aluminum_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_aluminum_scan_nd",
    **kwargs
):
    """
    short_aluminum_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_aluminum_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(1540.0, 1640.0, 2.0)
    # energies = np.append(energies,np.arange(525,540,0.5))
    # energies = np.append(energies,np.arange(540,560,2))
    times = energies.copy()

    # Define exposures times for different energy ranges
    # times[energies<525] = 2
    # times[(energies < 540) & (energies >= 525)] = 5
    # times[energies >= 540] = 2
    times[:] = 1.0
    times *= multiple
    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_nitrogen_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_nitrogen_scan_nd",
    **kwargs
):
    """
    full_nitrogen_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_nitrogen_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(385, 397, 1)
    energies = np.append(energies, np.arange(397, 407, 0.2))
    energies = np.append(energies, np.arange(407, 440, 1))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 400] = 1
    # times[(energies < 286) & (energies >= 282)] = 5
    times[energies >= 400] = 1
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_nitrogen_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_nitrogen_scan_nd",
    **kwargs
):
    """
    short_nitrogen_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_nitrogen_scan_nd"
    # grab locals
    arguments = dict(locals())
    # create a list of energies
    energies = np.arange(385, 397, 1.0)
    energies = np.append(energies, np.arange(397, 401, 0.2))
    energies = np.append(energies, np.arange(401, 410, 1.0))
    energies = np.append(energies, np.arange(410, 430, 2.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 400] = 1.0
    # times[(energies < 286) & (energies >= 282)] = 5
    times[energies >= 400] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def very_short_carbon_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="very_short_carbon_scan_nd",
    **kwargs
):
    """
    very_short_carbon_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "very_short_carbon_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 2.0)
    energies = np.append(energies, np.arange(282, 286, 0.5))
    energies = np.append(energies, np.arange(286, 292, 0.5))
    energies = np.append(energies, np.arange(292, 306, 2))
    energies = np.append(energies, np.arange(306, 320, 4))
    energies = np.append(energies, np.arange(320, 350, 10))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_carbon_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_carbon_scan_nd",
    **kwargs
):
    """
    short_carbon_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_carbon_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 2.0)
    energies = np.append(energies, np.arange(282, 286, 0.25))
    energies = np.append(energies, np.arange(286, 292, 0.5))
    energies = np.append(energies, np.arange(292, 306, 1))
    energies = np.append(energies, np.arange(306, 320, 4))
    energies = np.append(energies, np.arange(320, 350, 10))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_siliconk_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_siliconk_scan_nd",
    **kwargs
):
    """
    full_siliconk_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_siliconk_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(1830, 1870, 1.0)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid





def short_carbon_scan_nonaromatic(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_carbon_scan_nonaromatic",
    **kwargs
):
    """
    short_carbon_scan_nonaromatic
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_carbon_scan_nonaromatic"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 2.0)
    energies = np.append(energies, np.arange(282, 286, 0.5))
    energies = np.append(energies, np.arange(286, 290, 0.25))
    energies = np.append(energies, np.arange(290, 292, 0.5))
    energies = np.append(energies, np.arange(292, 306, 1))
    energies = np.append(energies, np.arange(306, 320, 4))
    energies = np.append(energies, np.arange(320, 350, 10))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid




def collins_carbon_survey_fixedpol(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    energies = [270.0,283.5,284.5,285.3],
    times = [5.0,1.0,1.0,1.0],
    polarizations=[-1,0,90],
    md={},
    pol=None,
    enscan_type="collins_carbon_survey_fixedpol",
    **kwargs
):
    """
    collins_carbon_survey_fixedpol
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    if pol is not None:
        print('Error: you cannot give this plan a polarization')
        raise ValueError('Error: you cannot give this plan a polarization')
    if len(times) != len(energies):
        print('Error: Energies and times must be the same length')
        raise ValueError('Error: Energies and times must be the same length')
    for time in times:
        if time > 20 or time <0 :
            print('invalid time')
            raise ValueError('invalid exposure time')
    plan_name = "collins_carbon_survey_fixedpol"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies

    times = [time * multiple for time in times]

    # use these energies and exposure times to scan energy and record detectors and signals
    returnvals = []
    for pol in polarizations:
        returnval = yield from en_scan_core(
            energies=energies,
            times=times,
            enscan_type=enscan_type,
            md=md,
            pol=pol,
            master_plan=master_plan,
            grating=grating,
            **kwargs
        )
        returnvals.append(returnval)
    return returnvals




def custom_rsoxs_scan(
    energies=[((270, 340, 1.0), 1.0)],
    master_plan=None,
    grating="rsoxs",
    md={},
    enscan_type="custom_rsoxs_scan",
    **kwargs
):
    """
    custom_rsoxs_scan
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "custom_rsoxs_scan"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    newenergies = []
    newtimes = []
    for ((start, stop, step), exp) in energies:
        tempenergies = np.arange(start, stop, step)
        newenergies = np.append(newenergies, tempenergies)
        temptimes = tempenergies.copy()
        temptimes[:] = exp
        newtimes = np.append(newtimes, temptimes)

    uid = yield from en_scan_core(
        energies=newenergies,
        times=newtimes,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid

def custom_rotate_rsoxs_scan(
    energies=[((270, 340, 1.0), 1.0)],
    angles = None,
    master_plan=None,
    grating="rsoxs",
    md=None,
    enscan_type="custom_rotate_rsoxs_scan",
    **kwargs
):
    """
    custom_rotate_rsoxs_scan
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "custom_rotate_rsoxs_scan"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    newenergies = []
    newtimes = []
    if md is None:
        md={}
    for ((start, stop, step), exp) in energies:
        tempenergies = np.arange(start, stop, step)
        newenergies = np.append(newenergies, tempenergies)
        temptimes = tempenergies.copy()
        temptimes[:] = exp
        newtimes = np.append(newtimes, temptimes)
    if isinstance(angles,list):
        returnvalues =  []
        for angle in angles:
            returnvalue = yield from en_scan_core(
                energies=newenergies,
                times=newtimes,
                enscan_type=enscan_type,
                md=md,
                master_plan=master_plan,
                grating=grating,
                angle=angle,
                **kwargs
            )
            returnvalues.append(returnvalue)
        return returnvalues
    else:
        uid = yield from en_scan_core(
            energies=newenergies,
            times=newtimes,
            enscan_type=enscan_type,
            md=md,
            master_plan=master_plan,
            grating=grating,
            **kwargs
        )
        return uid



def short_sulfurl_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_sulfurl_scan_nd",
    **kwargs
):
    """
    short_sulfurl_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_sulfurl_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # Oct 2019, this pitch value seems to be optimal for carbon

    # create a list of energies
    energies = np.arange(150, 160, 1.0)
    energies = np.append(energies, np.arange(160, 170, 0.25))
    energies = np.append(energies, np.arange(170, 200, 1.0))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 170] = 1.0
    times[energies >= 170] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def focused_carbon_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="focused_carbon_scan_nd",
    **kwargs
):
    """
    focused_carbon_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "focused_carbon_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 5.0)
    energies = np.append(energies, np.arange(282, 286, 0.2))
    energies = np.append(energies, np.arange(286, 292, 0.5))
    energies = np.append(energies, np.arange(292, 306, 1))
    energies = np.append(energies, np.arange(306, 320, 4))
    energies = np.append(energies, np.arange(320, 350, 10))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_carbon_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_carbon_scan_nd",
    **kwargs
):
    """
    full_carbon_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_carbon_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 0.5)
    energies = np.append(energies, np.arange(282, 286, 0.1))
    energies = np.append(energies, np.arange(286, 292, 0.2))
    energies = np.append(energies, np.arange(292, 305, 1))
    energies = np.append(energies, np.arange(305, 320, 1))
    energies = np.append(energies, np.arange(320, 350, 5))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_carbon_scan_nonaromatic(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_carbon_scan_nonaromatic",
    **kwargs
):
    """
    full_carbon_scan_nonaromatic
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_carbon_scan_nonaromatic"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 0.5)
    energies = np.append(energies, np.arange(282, 286, 0.2))
    energies = np.append(energies, np.arange(286, 292, 0.1))
    energies = np.append(energies, np.arange(292, 305, 1))
    energies = np.append(energies, np.arange(305, 320, 2))
    energies = np.append(energies, np.arange(320, 350, 5))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_titaniuml2_scan(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_titaniuml2_scan",
    **kwargs
):
    """
    full_carbon_scan_nonaromatic
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_titaniuml2_scan"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(445, 455, 2)
    energies = np.append(energies, np.arange(455, 468, 0.25))
    energies = np.append(energies, np.arange(468, 480, 2))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_fluorine_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_fluorine_scan_nd",
    **kwargs
):
    """
    full_fluorine_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_fluorine_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(680, 720.25, 0.25)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def veryshort_fluorine_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="veryshort_fluorine_scan_nd",
    **kwargs
):
    """
    veryshort_fluorine_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "veryshort_fluorine_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(680, 700, 1.0)
    energies = np.append(energies, np.arange(700, 720.5, 5))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_ca_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_ca_scan_nd",
    **kwargs
):
    """
    full_ca_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_ca_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(320, 340, 5.0)
    energies = np.append(energies, np.arange(340, 345, 1))
    energies = np.append(energies, np.arange(345, 349, 0.5))
    energies = np.append(energies, np.arange(349, 349.5, 0.1))
    energies = np.append(energies, np.arange(349.5, 352.5, 0.25))
    energies = np.append(energies, np.arange(352.5, 353, 0.1))
    energies = np.append(energies, np.arange(353, 355, .5))
    energies = np.append(energies, np.arange(355, 360, 1))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 400] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def short_calcium_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="short_calcium_scan_nd",
    **kwargs
):
    """
    short_calcium_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "short_calcium_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(320, 340, 5.0)
    energies = np.append(energies, np.arange(340, 345, 1))
    energies = np.append(energies, np.arange(345, 355, 0.5))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 400] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def full_carbon_calcium_scan_nd(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="full_carbon_calcium_scan_nd",
    **kwargs
):
    """
    full_carbon_calcium_scan_nd
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "full_carbon_calcium_scan_nd"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(270, 282, 0.5)
    energies = np.append(energies, np.arange(282, 286, 0.1))
    energies = np.append(energies, np.arange(286, 292, 0.2))
    energies = np.append(energies, np.arange(292, 305, 1))
    energies = np.append(energies, np.arange(305, 320, 5))
    energies = np.append(energies, np.arange(320, 340, 5))
    energies = np.append(energies, np.arange(340, 345, 1))
    energies = np.append(energies, np.arange(345, 360, 0.5))
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[energies < 282] = 1.0
    times[(energies < 286) & (energies >= 282)] = 1.0
    times[energies >= 286] = 1.0
    times[energies >= 320] = 3.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        **kwargs
    )
    return uid


def survey_scan_verylowenergy(
    multiple=1.0,
    grating="250",
    master_plan=None,
    md={},
    enscan_type="survey_scan_verylowenergy",
    **kwargs
):
    """
    survey_scan_verylowenergy
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "survey_scan_verylowenergy"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(70.0, 260.0, 1.0)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        lockscan=False,
        **kwargs
    )
    return uid


def survey_scan_lowenergy(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="survey_scan_lowenergy",
    **kwargs
):
    """
    survey_scan_lowenergy
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "survey_scan_lowenergy"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(240.0, 500, 2.0)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        lockscan=False,
        **kwargs
    )
    return uid


def survey_scan_highenergy(
    multiple=1.0,\
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="survey_scan_highenergy",
    **kwargs
):
    """
    survey_scan_highenergy
    @param master_plan: higher level plan for timing purposes
    @param md: any metadata to push through to acquisition
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "survey_scan_highenergy"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(400.0, 1200, 5.0)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        lockscan=False,
        **kwargs
    )
    return uid


def survey_scan_veryhighenergy(
    multiple=1.0,
    grating="rsoxs",
    master_plan=None,
    md={},
    enscan_type="survey_scan_veryhighenergy",
    **kwargs
):
    """
    survey_scan_veryhighenergy
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "survey_scan_veryhighenergy"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    # create a list of energies
    energies = np.arange(1200.0, 2030, 10.0)
    times = energies.copy()

    # Define exposures times for different energy ranges
    times[:] = 1.0
    times *= multiple

    # use these energies and exposure times to scan energy and record detectors and signals
    uid = yield from en_scan_core(
        energies=energies,
        times=times,
        enscan_type=enscan_type,
        md=md,
        master_plan=master_plan,
        grating=grating,
        lockscan=False,
        **kwargs
    )
    return uid


def cdsaxs_scan(
    energies=[(250, 2), (270, 2), (280, 2), (285, 2), (300, 2)],
    angles=(-60, 61, 2),
    master_plan="cdsaxs_scan",
    grating="rsoxs",
    md={},
    enscan_type="cdsaxs_scan",
    **kwargs
):
    """
    custom_rsoxs_scan
    @param master_plan: a category of higher level plan which you might want to sort by
    @param enscan_type: the granular level plan you might want to sort by - generally for timing or data lookup
    @param md: metadata to push through to lower level plans and eventually a bluesky document
    @param multiple: default exposure times is multipled by this
    @param energies: list of touples of energy, exposure time
    @param angles: list of angles.  at each angle, the energy list will be collected
    @param grating: '1200' high energy or '250' low energy
    @param kwargs: all extra parameters for general scans - see the inputs for en_scan_core
    @return: Do a step scan and take images
    """
    plan_name = "cdsaxs_scan"
    # grab locals
    arguments = dict(locals())
    clean_up_md(arguments, md, **kwargs)
    newenergies = []
    newtimes = []
    for (energy, exp) in energies:
        newenergies.append(energy)
        newtimes.append(exp)
    returnvals = []
    for angle in np.arange(*angles):

        returnval = yield from en_scan_core(
            angle=angle,
            energies=newenergies,
            times=newtimes,
            enscan_type=enscan_type,
            md=md,
            master_plan=master_plan,
            grating=grating,
            **kwargs
        )
        returnvals.append(returnval)
    return returnvals
