import sys
from pathlib import Path

paths = [
    path
    for path in Path(
        "/nsls2/data/sst/rsoxs/shared/config/bluesky/collection_packages"
    ).glob("*")
    if path.is_dir()
]
for path in paths:
    sys.path.append(str(path))

import os
import re
import nslsii
import time
import appdirs
import httpx

from bluesky.preprocessors import finalize_decorator
from bluesky.run_engine import Msg
import bluesky.plan_stubs as bps

# RSoXS specific code
# from rsoxs.Functions.alignment import *
# from rsoxs.Functions.alignment_local import *
# from rsoxs.Functions.common_procedures import *
# from rsoxs.Functions.configurations import *
# from rsoxs.Functions.schemas import *
# from rsoxs.Functions.PVdictionary import *
# from rsoxs.Functions.energyscancore import *
# from rsoxs.Functions.rsoxs_plans import *
# from rsoxs.Functions.fly_alignment import *
# from rsoxs.Functions.spreadsheets import *
# from rsoxs.HW.slackbot import rsoxs_bot
# from rsoxs_scans.spreadsheets import *
# from rsoxs_scans.acquisition import *

from sst_funcs.printing import run_report

run_report(__file__)

# Use caproto not pyepics.
# os.environ['OPHYD_CONTROL_LAYER'] = 'pyepics'


## stole below from BMM, but changed it around so it made sense to Eliot

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False


if not is_re_worker_active():
    ip = get_ipython()
    ns = get_ipython().user_ns
    nslsii.configure_base(
        ns, "rsoxs", bec=False, configure_logging=True, publish_documents_with_kafka=True
    )
    ip.log.setLevel("ERROR")
    RE = ip.user_ns["RE"]
    db = ip.user_ns["db"]
    sd = ip.user_ns["sd"]
    #bec = ip.user_ns["bec"]
else:
    ns = {}
    nslsii.configure_base(
        ns, "rsoxs", bec=False, configure_logging=True, publish_documents_with_kafka=True
    )
    RE = ns["RE"]
    db = ns["db"]
    sd = ns["sd"]
    #bec = ns["bec"]


# === START PERSISTENT DICT CODE ===
# old code, using the files on lustre to store the persistent dict
#from bluesky.utils import PersistentDict
#runengine_metadata_dir = Path("/nsls2/data/sst/legacy/RSoXS/config/runengine-metadata")
#RE.md = PersistentDict(runengine_metadata_dir)

# new code, using redis
from nslsii.md_dict import RunEngineRedisDict

class Sync_Dict(RunEngineRedisDict):

    def write(self):
        self._set_local_metadata_on_server()
        print('RSoXS configuration saved to redis')

    def read(self):
        self.update(self._get_local_metadata_from_server())
    
    def write_plan(self):
        yield from bps.null()
        self.write()
        yield from bps.null()
    
    def clear_bar(self):
        self['bar'] = []
        self.write()


RE.md = Sync_Dict(host="info.sst.nsls2.bnl.gov", port=60737) # port specific to rsoxs run engine
rsoxs_config = Sync_Dict(re_md_channel_name='RSoXS Config',host="info.sst.nsls2.bnl.gov", port=60737,db=1,global_keys=[])


data_session_re = re.compile(r"^pass-(?P<proposal_number>\d+)$")

def md_validator(md):
    """Validate RE.md before a plan runs.

    This function validates only "data_session".
    """

    if "data_session" in md:
        # if there is a "data_session" key
        # its value must be validated
        data_session_value = md["data_session"]
        if not isinstance(data_session_value, str):
            raise ValueError(
                f"RE.md['data_session']={data_session_value}', but it must be a string"
            )
        data_session_match = data_session_re.match(data_session_value)
        if data_session_match is None:
            raise ValueError(
                f"RE.md['data_session']='{data_session_value}' "
                f"is not matched by regular expression '{data_session_re.pattern}'"
            )
        else:
            proposal_number = data_session_match.group("proposal_number")
            nslsii_api_client = httpx.Client(
                #base_url="https://api-staging.nsls2.bnl.gov"
                base_url="https://api.nsls2.bnl.gov"
            )
            try:
                proposal_response = nslsii_api_client.get(
                    f"/v1/proposal/{proposal_number}"
                )
                proposal_response.raise_for_status()
                if "error_message" in proposal_response.json():
                    raise ValueError(
                        f"while verifying data_session '{data_session_value}' "
                        f"an error was returned by {proposal_response.url}: "
                        f"{proposal_response.json()}"
                    )
                else:
                    # data_session is valid!
                    pass

            except httpx.RequestError as rerr:
                # give the user a warning
                # but allow the run to start
                warnings.warn(
                    f"while verifying data_session '{data_session_value}' "
                    f"the request {rerr.request.url!r} failed with "
                    f"'{rerr}'"
                )
                return
            except httpx.HTTPStatusError as serr:
                warnings.warn(
                    f"while verifying data_session '{data_session_value}' "
                    f"the request {serr.request.url!r} failed with "
                    f"'{serr}'"
                )
                if serr.response.is_client_error:
                    # the user may be able to fix this?
                    # do not allow the run to start
                    raise serr
                elif serr.response.is_server_error:
                    # allow the run to start
                    pass
    else:
        # if there is no "data_session" key allow runs to start
        pass

# md_validator will be called before a plan runs
RE.md_validator = md_validator


# === END PERSISTENT DICT CODE ===


# Optional: set any metadata that rarely changes.
RE.md["beamline_id"] = "SST-1 RSoXS"

# Add a callback that prints scan IDs at the start of each scan.
def print_scan_ids(name, start_doc):
    print(
        "Transient Scan ID: {0} @ {1}".format(
            start_doc["scan_id"], time.strftime("%Y/%m/%d %H:%M:%S")
        )
    )
    print("Persistent Unique Scan ID: '{0}'".format(start_doc["uid"]))


RE.subscribe(print_scan_ids, "start")

control_layer = os.getenv("OPHYD_CONTROL_LAYER")

print(f'You are using the "{control_layer}" control layer')

# getting rid of the warnings
import logging

logging.getLogger("caproto").setLevel("ERROR")
#bec.disable_baseline()

#from bluesky.callbacks.zmq import Publisher

#publisher = Publisher("localhost:5577")
#RE.subscribe(publisher)

import logging
import bluesky.log

logger = logging.getLogger("bluesky_darkframes")
handler = logging.StreamHandler()
handler.setLevel("DEBUG")
logger.addHandler(handler)
logger.getEffectiveLevel()
logger.setLevel("DEBUG")  # change DEBUG to INFO later on

from databroker.v0 import Broker

db0 = Broker.named("rsoxs")

#bec.disable_table()
#bec.disable_plots()

RE.md['scan_id'] = int(RE.md['scan_id'])

