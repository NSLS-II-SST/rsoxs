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
from pathlib import Path
import appdirs

from sst.CommonFunctions.functions import run_report

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

try:
    from bluesky.utils import PersistentDict
except ImportError:
    import msgpack
    import msgpack_numpy
    import zict

    class PersistentDict(zict.Func):
        """
        A MutableMapping which syncs it contents to disk.
        The contents are stored as msgpack-serialized files, with one file per item
        in the mapping.
        Note that when an item is *mutated* it is not immediately synced:
        >>> d['sample'] = {"color": "red"}  # immediately synced
        >>> d['sample']['shape'] = 'bar'  # not immediately synced
        but that the full contents are synced to disk when the PersistentDict
        instance is garbage collected.
        """

        def __init__(self, directory):
            self._directory = directory
            self._file = zict.File(directory)
            self._cache = {}
            super().__init__(self._dump, self._load, self._file)
            self.reload()

            # Similar to flush() or _do_update(), but without reference to self
            # to avoid circular reference preventing collection.
            # NOTE: This still doesn't guarantee call on delete or gc.collect()!
            #       Explicitly call flush() if immediate write to disk required.
            def finalize(zfile, cache, dump):
                zfile.update((k, dump(v)) for k, v in cache.items())

            import weakref

            self._finalizer = weakref.finalize(
                self, finalize, self._file, self._cache, PersistentDict._dump
            )

        @property
        def directory(self):
            return self._directory

        def __setitem__(self, key, value):
            self._cache[key] = value
            super().__setitem__(key, value)

        def __getitem__(self, key):
            return self._cache[key]

        def __delitem__(self, key):
            del self._cache[key]
            super().__delitem__(key)

        def __repr__(self):
            return f"<{self.__class__.__name__} {dict(self)!r}>"

        @staticmethod
        def _dump(obj):
            "Encode as msgpack using numpy-aware encoder."
            # See https://github.com/msgpack/msgpack-python#string-and-binary-type
            # for more on use_bin_type.
            return msgpack.packb(obj, default=msgpack_numpy.encode, use_bin_type=True)

        @staticmethod
        def _load(file):
            return msgpack.unpackb(file, object_hook=msgpack_numpy.decode, raw=False)

        def flush(self):
            """Force a write of the current state to disk"""
            for k, v in self.items():
                super().__setitem__(k, v)

        def reload(self):
            """Force a reload from disk, overwriting current cache"""
            self._cache = dict(super().items())


# runengine_metadata_dir = appdirs.user_data_dir(appname="bluesky") / Path("runengine-metadata")
# Updated on 2021-04-28 by DSSI/@mrakitin to have a shared location for
# metadata for new RHEL8 machines (and old ones).
runengine_metadata_dir = Path("/nsls2/data/sst/legacy/RSoXS/config/runengine-metadata")

# PersistentDict will create the directory if it does not exist
print('before persistent dict loading')
RE.md = PersistentDict(runengine_metadata_dir)

print('after persistent dict loading')
# Temporary fix from Dan Allan Feb 2, 2021
import collections.abc, zict, msgpack, msgpack_numpy


class PersistentDict(collections.abc.MutableMapping):
    """
    A MutableMapping which syncs it contents to disk.
    The contents are stored as msgpack-serialized files, with one file per item
    in the mapping.
    Note that when an item is *mutated* it is not immediately synced:
    >>> d['sample'] = {"color": "red"}  # immediately synced
    >>> d['sample']['shape'] = 'bar'  # not immediately synced
    but that the full contents are synced to disk when the PersistentDict
    instance is garbage collected.
    """

    def __init__(self, directory):
        self._directory = directory
        self._file = zict.File(directory)
        self._func = zict.Func(self._dump, self._load, self._file)
        self._cache = {}
        self.reload()

        # Similar to flush() or _do_update(), but without reference to self
        # to avoid circular reference preventing collection.
        # NOTE: This still doesn't guarantee call on delete or gc.collect()!
        #       Explicitly call flush() if immediate write to disk required.
        def finalize(zfile, cache, dump):
            zfile.update((k, dump(v)) for k, v in cache.items())

        import weakref

        self._finalizer = weakref.finalize(
            self, finalize, self._file, self._cache, PersistentDict._dump
        )

    @property
    def directory(self):
        return self._directory

    def __setitem__(self, key, value):
        self._cache[key] = value
        self._func[key] = value

    def __getitem__(self, key):
        return self._cache[key]

    def __delitem__(self, key):
        del self._cache[key]
        del self._func[key]

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        return f"<{self.__class__.__name__} {dict(self)!r}>"

    def __iter__(self):
        yield from self._cache

    def popitem(self):
        key, _value = self._cache.popitem()
        del self._func[key]

    @staticmethod
    def _dump(obj):
        "Encode as msgpack using numpy-aware encoder."
        # See https://github.com/msgpack/msgpack-python#string-and-binary-type
        # for more on use_bin_type.
        return msgpack.packb(obj, default=msgpack_numpy.encode, use_bin_type=True)

    @staticmethod
    def _load(file):
        return msgpack.unpackb(file, object_hook=msgpack_numpy.decode, raw=False)

    def flush(self):
        """Force a write of the current state to disk"""
        for k, v in self.items():
            self._func[k] = v

    def reload(self):
        """Force a reload from disk, overwriting current cache"""
        self._cache = dict(self._func.items())


RE.md = PersistentDict(
    RE.md.directory
)  # Use fixed PersistentDict. aimed at same directory as built-in one

# end temporary fix


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
