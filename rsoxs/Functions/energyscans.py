import numpy as np
import bluesky.plan_stubs as bps
from .energyscancore import en_scan_core
from ..Functions.alignment import rotate_now
from sst_funcs.printing import run_report, read_input

run_report(__file__)


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
