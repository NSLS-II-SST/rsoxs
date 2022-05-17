from sst_funcs.printing import run_report


run_report(__file__)


"""
changing this to all be in directory "schemas" with separate json file for each definition

also removing json references, and just putting ids - this will allow cross referencing to other database

"""
acquisition_schema = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS Acquisition",
    "type": "object",
    "properties": {
        "plan_name": {"type": "string"},
        "filename": {
            "type": "string"
        },  # what to add to the filename for this scan, if anything
        "scan_core": {"type": "string"},  # the core scan plan name
        "detectors": {
            "type": "array",
            "items": [{"type": "string"}],
        },  # will be given to core with "dets=[]" format
        "motors": {
            "type": "array",  # list of motors to scan
            "items": [{"type": "string"}],
        },  # will be given to core scan with 'motors=[]'
        "beamline_settings": {
            "type": "array",
            "items": [{"type": "string"}],
        },  # list of devices and positions
        # (i.e. diode range, m3_pitch, EPU polarization)
        # these will be set before acquisition
        "positions": {
            "type": "array",  # if step scan, a list of the steps for each motor
            "items": [[{"type": "number"}]],
        },  # given to core as positions = [[],[]]
        # can be combined or grid depending on core
        "display": {"type": "string", "enum": ["private", "public"]},
        # default visualization to use during this scan,
        # can be another plan name, or list of axes depending on core
        "time_estimate": {
            "type": "string"
        },  # function to call and give parameters to give time estimate
        # in seconds
        "favorite": {"type": "boolean"},  # displayed first on the dropdown list?
        "creator_ID": {"type": "number"},  # who's scan is this?
    },
    "required": ["plan_name", "motors", "positions", "display", "favorite"],
}

configuration_schmea = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS configuration",
    "type": "object",
    "properties": {
        "plan_name": {"type": "string"},
        "motors": {"type": "array", "items": [{"type": "string"}]},
        "positions": {"type": "array", "items": [{"type": "number"}]},
        "display": {"type": "string", "enum": ["private", "public"]},
        "favorite": {"type": "boolean"},
        "creator_ID": {"type": "number"},
    },
    "required": ["plan_name", "motors", "positions", "display", "favorite"],
}

location_schema = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS location",
    "type": "object",
    "properties": {
        "location_list": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "motor_name": {"type": "string"},
                        "position": {"type": "number"},
                    },
                    "required": ["motor_name", "position"],
                }
            ],
            "minItems": 1,
        },
        "display": {"type": "string", "enum": ["private", "public"]},
        "favorite": {"type": "boolean"},
        "creator_ID": {"type": "number"},
    },
    "required": ["location_list", "display", "favorite"],
}

sample_schema = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS Sample",
    "type": "object",
    "properties": {
        "sample_name": {"type": "string"},
        "sample_id": {"type": "string"},
        "sample_priority": {"type": "number"},
        "sample_desc": {"type": "string"},
        "date_created": {"type": "string", "format": "date"},
        "user_id": {"type": "number"},
        "proposal_id": {"type": "string"},
        "saf_id": {"type": "string"},
        "project_name": {"type": "string"},
        "institution_id": {"type": "number"},
        "front": {"type": "boolean"},
        "grazing": {"type": "boolean"},
        "bar_loc": {
            "type": "object",
            "properties": {
                "spot": {
                    "type": "string"
                },  # e.g. 1A. 16C (first row first sample, 16th row third sample)
                "front": {"type": "boolean"},  # default rotation
                "beam_from_back": {"type": "boolean"},  # default measurement rotation
                "th": {
                    "type": "number"
                },  # measurement theta (will determine measurement x and y)
                "x0": {
                    "type": "number"
                },  # best unrotated location of sample in x dimension
                "ximg": {
                    "type": "number"
                },  # for bookkeeping, the original location of x from the image
                "y0": {
                    "type": "number"
                },  # best corrected y location of sample (from image/refinements)
                "yimg": {
                    "type": "number"
                },  # for bookkeeping, the original location of y from the image
                "th0": {
                    "type": "number"
                },  # determined from image/refinement (front ~ 0, back ~ 180)
                "xoff": {"type": "number"},  # determined from fiducials / y position
                "zoff": {"type": "number"},  # determined from fiducials / y position
                "z0": {
                    "type": "number"
                },  # default 0, can be used if necessary for some samples.
                "af1y": {"type": "number"},  # used to calculate the zoffset
                "af2y": {"type": "number"},
                "af1zoff": {"type": "number"},
                "af2zoff": {"type": "number"},
                "af1xoff": {"type": "number"},
                "af2xoff": {"type": "number"},
            },
            "required": [
                "x0",
                "y0",
                "th0",
                "front",
                "beam_from_back",
                "th",
                "xoff",
                "yoff",
            ],
        },
        "composition": {"type": "string"},
        "density": {"type": "number"},
        "thickness": {"type": "number"},
        "notes": {"type": "string"},
        "state": {
            "type": "string",
            "enum": ["loaded", "fresh", "broken", "lost", "unloaded"],
        },
        "current_bar_id": {"type": "number"},
        "current_slot_name": {"type": "string"},
        "past_bar_ids": {"type": "array"},
        "location": {"$ref": "#/definitions/location"},
        "collections": {
            "type": "array",
            "uniqueItems": True,
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "configuration": {"$ref": "RSoXS configuration"},
                        "acquisition": {"$ref": "RSoXS acquisition"},
                        "location": {"$ref": "RSoXS location"},
                    },
                    "required": ["configuration", "acquisition"],
                }
            ],
        },
    },
    "required": [
        "sample_name",
        "sample_id",
        "sample_priority",
        "date_created",
        "user_id",
        "proposal_id",
        "saf_id",
        "project_name",
        "institution_id",
        "notes",
        "state",
        "location",
        "current_bar_id",
        "current_slot_name",
        "collections",
    ],
}


user_schema = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS User",
    "type": "object",
    "properties": {
        "user_id": {"type": "number"},
        "username": {"type": "string"},
        "last_checkin": {"type": "string", "format": "date"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "institution_id": {"type": "number"},
        "proposal_id": {"type": "number"},
        "date_checkin_list": {
            "type": "array",
            "items": [{"type": "string", "format": "date"}],
        },
        "past_institutions": {"type": "array", "items": [{"type": "number"}]},
        "past_proposals": {"type": "array", "items": [{"type": "number"}]},
        "notes": {"type": "string"},
    },
    "required": [
        "user_id",
        "username",
        "email",
        "first_name",
        "last_name",
        "last_checkin",
        "institution_id",
        "proposal_id",
        "date_checkin_list",
        "past_institutions",
    ],
}

Institution_schema = {
    "$schema": "http://json-schema.org/schema#",
    "$id": "RSoXS Institution",
    "type": "object",
    "properties": {
        "institution_id": {"type": "number"},
        "full_name": {"type": "string"},
        "short_name": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["institution_id", "full_name", "short_name"],
}
