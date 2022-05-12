import json
from numpy import array
from ..HW.detectors import waxs_det, saxs_det

def giveme_inputs(*args, **kwargs):
    return args, kwargs


def string_to_inputs(string):
    return eval("giveme_inputs(" + string + ")")


def args_to_string(*args, **kwargs):
    outstr = ""
    for arg in args:
        if isinstance(arg, str):
            outstr += f'"{arg}",'
        else:
            outstr += f"{arg},"
    for key in kwargs.keys():
        if isinstance(kwargs[key], str):
            outstr += f'{key} = "{kwargs[key]}", '
        elif is_jsonable(kwargs[key]):
            outstr += f"{key} = {json.dumps(kwargs[key])}, "
        else:
            outstr += f"{key} = 'not seralizable', "
    return outstr.rstrip(", ")


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except Exception:
        return False
