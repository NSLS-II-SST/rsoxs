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
import nslsii
import time
import appdirs

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
        ns, "rsoxs", configure_logging=True, publish_documents_with_kafka=True
    )
    ip.log.setLevel("ERROR")
    RE = ip.user_ns["RE"]
    db = ip.user_ns["db"]
    sd = ip.user_ns["sd"]
    bec = ip.user_ns["bec"]
else:
    ns = {}
    nslsii.configure_base(
        ns, "rsoxs", configure_logging=True, publish_documents_with_kafka=True
    )
    RE = ns["RE"]
    db = ns["db"]
    sd = ns["sd"]
    bec = ns["bec"]


# === START PERSISTENT DICT CODE ===
# old code, using the files on lustre to store the persistent dict
#from bluesky.utils import PersistentDict
#runengine_metadata_dir = Path("/nsls2/data/sst/legacy/RSoXS/config/runengine-metadata")
#RE.md = PersistentDict(runengine_metadata_dir)

# new code, using redis
from nslsii.md_dict import RunEngineRedisDict
RE.md = RunEngineRedisDict(host="info.sst.nsls2.bnl.gov", port=60737) # port specific to rsoxs run engine

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

# print(f'You are using the "{control_layer}" control layer')

# getting rid of the warnings
import logging

logging.getLogger("caproto").setLevel("ERROR")
bec.disable_baseline()

from bluesky.callbacks.zmq import Publisher

publisher = Publisher("localhost:5577")
RE.subscribe(publisher)

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

bec.disable_table()
bec.disable_plots()

RE.md['scan_id'] = int(RE.md['scan_id'])