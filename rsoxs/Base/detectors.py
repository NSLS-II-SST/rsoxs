import time
from bluesky.run_engine import Msg
from ophyd import Component as C
from ophyd import EpicsSignalRO, Device, EpicsSignal
from ophyd.areadetector import (
    GreatEyesDetector,
    GreatEyesDetectorCam,
    ImagePlugin,
    TIFFPlugin,
    ROIPlugin,
    TransformPlugin,
)
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from nslsii.ad33 import SingleTriggerV33, StatsPluginV33
from sst_funcs.printing import boxed_text, colored
from sst_hw.diode import (
    Shutter_open_time,
    Shutter_control,
    Shutter_enable,
    Shutter_delay,
)
from sst_funcs.printing import run_report


run_report(__file__)


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GreatEyesDetCamWithVersions(GreatEyesDetectorCam):
    adcore_version = C(EpicsSignalRO, "ADCoreVersion_RBV")
    driver_version = C(EpicsSignalRO, "DriverVersion_RBV")
    wait_for_plugins = C(EpicsSignal, "WaitForPlugins", string=True, kind="config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs["wait_for_plugins"] = "Yes"

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()


class GreateyesTransform(TransformPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    type = C(EpicsSignal, "Type")


class RSOXSGreatEyesDetector(SingleTriggerV33, GreatEyesDetector):
    image = C(ImagePlugin, "image1:")
    cam = C(GreatEyesDetCamWithVersions, "cam1:")
    transform_type = 0
    tiff = C(
        TIFFPluginWithFileStore,
        "TIFF1:",
        write_path_template="/nsls2/data/sst/assets/%Y/%m/%d/",
        read_path_template="/nsls2/data/sst/assets/%Y/%m/%d/",
        read_attrs=[],
        root="/nsls2/data/sst/assets/",
    )

    stats1 = C(StatsPluginV33, "Stats1:")
    # stats2 = C(StatsPluginv33, 'Stats2:')
    # stats3 = C(StatsPlugin, 'Stats3:')
    # stats4 = C(StatsPlugin, 'Stats4:')
    # stats5 = C(StatsPlugin, 'Stats5:')
    trans1 = C(GreateyesTransform, "Trans1:")
    roi1 = C(ROIPlugin, "ROI1:")
    # roi2 = C(ROIPlugin, 'ROI2:')
    # roi3 = C(ROIPlugin, 'ROI3:')
    # roi4 = C(ROIPlugin, 'ROI4:')
    # proc1 = C(ProcessPlugin, 'Proc1:')
    binvalue = 4
    useshutter = True

    def sim_mode_on(self):
        self.useshutter = False
        self.cam.sync.set(0)
        self.cam.shutter_mode.set(0)

    def sim_mode_off(self):
        self.useshutter = True
        self.cam.sync.set(1)
        self.cam.shutter_mode.set(2)

    def stage(self, *args, **kwargs):
        self.cam.temperature_actual.read()
        self.cam.temperature.read()
        # self.cam.sync.set(1)
        # self.cam.temperature.set(-80)
        # self.cam.enable_cooling.set(1)
        # print('staging the detector')
        if self.useshutter:
            Shutter_enable.set(1)
            Shutter_delay.set(0)
        if abs(self.cam.temperature_actual.get() - self.cam.temperature.get()) > 2.0:

            boxed_text(
                "Temperature Warning!!!!",
                self.cooling_state()
                + "\nPlease wait until temperature has stabilized before collecting important data.",
                "yellow",
                85,
            )
        self.trans1.enable.set(1)
        self.trans1.type.set(self.transform_type)
        self.image.nd_array_port.set("TRANS1")
        self.tiff.nd_array_port.set("TRANS1")

        return [self].append(super().stage(*args, **kwargs))

    def trigger(self, *args, **kwargs):
        # if(self.cam.sync.get() != 1):
        #    print(f'Warning: It looks like the {self.name} restarted, putting in default values again')
        #    self.cam.temperature.set(-80)
        if self.cam.enable_cooling.get() != 1:
            print(
                f"Warning: It looks like the {self.name} restarted, putting in default values again"
            )
            self.cam.temperature.set(-80)
            self.cam.enable_cooling.set(1)
            self.cam.bin_x.set(self.binvalue)
            self.cam.bin_y.set(self.binvalue)
        return super().trigger(*args, **kwargs)

    def skinnystage(self, *args, **kwargs):
        yield Msg("stage", super())

    def shutter(self):
        switch = {0: "disabled", 1: "enabled", 3: "unknown", 4: "unknown", 2: "enabled"}
        #return "Shutter is {}".format(switch[self.cam.sync.get()])
        return "Shutter is {}".format(switch[self.cam.shutter_mode.get()])
        # return ('Shutter is {}'.format(switch[self.cam.shutter_mode.get()]))

    def shutter_on(self):
        # self.cam.sync.set(1)
        if self.useshutter:
            #self.cam.sync.set(1)
            self.cam.shutter_mode.det(2)
        else:
            print("not turning on shutter because detector is in simulation mode")

    def shutter_off(self):
        # self.cam.sync.set(0)
        self.cam.shutter_mode.det(0)

    def unstage(self, *args, **kwargs):
        if self.useshutter:
            Shutter_enable.set(0)
        else:
            print("not turning on shutter because detector is in simulation mode")
        return [self].append(super().unstage(*args, **kwargs))

    def skinnyunstage(self, *args, **kwargs):
        yield Msg("unstage", super())

    def set_exptime(self, secs):
        self.cam.acquire_time.set(secs)
        if self.useshutter:
            Shutter_open_time.set(secs * 1000)

    def set_exptime_detonly(self, secs):
        self.cam.acquire_time.set(secs)

    def exptime(self):
        return "{} has an exposure time of {} seconds".format(
            colored(self.name, "lightblue"),
            colored(str(self.cam.acquire_time.get()), "lightgreen"),
        )

    def set_temp(self, degc):
        self.cam.temperature.set(degc)
        self.cam.enable_cooling.set(1)

    def cooling_off(self):
        self.cam.enable_cooling.set(0)

    #    def setROI(self,):
    #        self.cam.

    def cooling_state(self):
        if self.cam.enable_cooling.get():
            self.cam.temperature_actual.read()
            if self.cam.temperature_actual.get() - self.cam.temperature.get() > 1.0:
                return "{} is {}°C, not at setpoint ({}°C, enabled)".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "red"),
                    colored(self.cam.temperature.get(), "blue"),
                )
            else:
                return "{} is {}°C, at setpoint ({}°C, enabled)".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "green"),
                    colored(self.cam.temperature.get(), "blue"),
                )
        else:
            if self.cam.temperature_actual.get() - self.cam.temperature.get() > 1.0:
                return "{} is {}°C, not at setpoint ({}°C, disabled)".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "red"),
                    colored(self.cam.temperature.get(), "darkgray"),
                )
            else:
                return "{} is {}°C, at setpoint ({}°C, disabled)".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "green"),
                    colored(self.cam.temperature.get(), "darkgray"),
                )

    def set_binning(self, binx, biny):
        self.binvalue = binx
        self.cam.bin_x.set(binx)
        self.cam.bin_y.set(biny)

    def binning(self):
        return "Binning of {} is set to ({},{}) pixels".format(
            colored(self.name, "lightblue"),
            colored(self.cam.bin_x.get(), "lightpurple"),
            colored(self.cam.bin_y.get(), "lightpurple"),
        )

    def exposure(self):
        return self.exptime()

    def set_exposure(self, seconds):
        self.set_exptime(seconds)


class SyncedDetectors(Device):
    saxs = C(
        RSOXSGreatEyesDetector,
        "XF:07ID1-ES:1{GE:1}",
        read_attrs=["tiff", "stats1.total"],
        name="Small Angle CCD Detector",
    )
    waxs = C(
        RSOXSGreatEyesDetector,
        "XF:07ID1-ES:1{GE:2}",
        read_attrs=["tiff", "stats1.total"],
        name="Wide Angle CCD Detector",
    )

    def __init__(self, *args, **kwargs):
        self.lightwason = None
        super().__init__(*args, **kwargs)

    def trigger(self):
        waxs_status = self.waxs.trigger()
        saxs_status = self.saxs.trigger()
        return saxs_status & waxs_status

    def collect_asset_docs(self, *args, **kwargs):
        yield from self.saxs.collect_asset_docs(*args, **kwargs)
        yield from self.waxs.collect_asset_docs(*args, **kwargs)

    def set_exposure(self, seconds):
        self.waxs.set_exptime_detonly(seconds)
        self.saxs.set_exptime_detonly(seconds)
        Shutter_open_time.set(seconds * 1000)
        self.waxs.trans1.type.put(1)
        self.saxs.trans1.type.put(3)

    def exposure(self):
        return self.waxs.exptime() + "\n" + self.saxs.exptime()

    def set_binning(self, pixels):
        self.saxs.set_binning(pixels, pixels)
        self.waxs.set_binning(pixels, pixels)

    def binning(self):
        return self.saxs.binning() + "\n" + self.waxs.binning()

    def cooling_on(self):
        self.saxs.set_temp(-80)
        self.waxs.set_temp(-80)

    def shutter_status(self):
        return self.saxs.shutter()

    def shutter_on(self):
        self.saxs.shutter_on()
        self.waxs.shutter_on()

    def shutter_off(self):
        self.saxs.shutter_off()
        self.waxs.shutter_off()

    def cooling_state(self):
        return self.saxs.cooling_state() + self.waxs.cooling_state()

    def cooling_off(self):
        self.saxs.cooling_off()
        self.waxs.cooling_off()
        time.sleep(2)
        self.cooling_state()

    def open_shutter(self):
        Shutter_control.set(1)

    def close_shutter(self):
        Shutter_control.set(0)

    def shutter(self):
        Shutter_control.get()


from ophyd.sim import SynSignalWithRegistry, SynSignal
from ophyd import Device, Component, Signal, DeviceStatus
import numpy as np
import threading


def make_random_array():
    # return numpy array
    return np.zeros([100, 100])


class SimGreatEyesCam(Device):
    shutter_mode = Component(Signal, value=3)
    acquire_time = Component(SynSignal, func=lambda: 3 + np.random.rand())
    bin_x = Component(Signal, value=3)
    bin_y = Component(Signal, value=3)
    temperature = Component(Signal, value=-80)
    temperature_actual = Component(Signal, value=-80)
    enable_cooling = Component(Signal, value=1)

    def collect_asset_docs(self):
        yield from []


#  test out the nxsas suitcase
#  (/home/xf07id1/conda_envs/nxsas-analysis-2019-3.0) xf07id1@xf07id1-ws19:~$ ipython --profile=collection
# In [1]: import suitcase.nxsas
# In [2]: h = db[-1]
# In [3]: suitcase.nxsas.export(h.documents(), directory=".")


class PatchedSynSignalWithRegistry(SynSignalWithRegistry, Device):
    def trigger(self):
        "Promptly return  a status object that will be marked 'done' after self.exposure_time seconds."
        super().trigger()  # returns NullStatus, which is "done" immediately -- let's do better
        status = DeviceStatus(self)
        # In the background, wait for `self.exposure_time` seconds and then mark the status as "done".
        threading.Timer(self.exposure_time, status._finished).start()
        return status


class SimGreatEyes(Device):
    useshutter = True

    image = Component(
        PatchedSynSignalWithRegistry,
        func=make_random_array,
        save_path="/tmp/sim_detector_storage/",
        exposure_time=2,
    )
    cam = Component(SimGreatEyesCam)

    def sim_mode_on(self):
        self.useshutter = False

    def sim_mode_off(self):
        self.useshutter = True

    def stage(self):
        print("staging")
        return super().stage()

    def unstage(self):
        print("unstaging")
        return super().unstage()

    def trigger(self):
        print("trigger")
        return self.image.trigger()

    def collect_asset_docs(self):
        print("collecting documents")
        yield from self.image.collect_asset_docs()

    def shutter(self):
        switch = {0: "disabled", 1: "enabled", 3: "unknown", 4: "unknown", 2: "enabled"}
        # return ('Shutter is {}'.format(switch[self.cam.sync.get()]))
        return "Shutter is {}".format(switch[self.cam.shutter_mode.get()])

    def shutter_on(self):
        # self.cam.sync.set(1)
        self.cam.shutter_mode.set(2)

    def shutter_off(self):
        # self.cam.sync.set(0)
        self.cam.shutter_mode.set(0)

    def set_exptime(self, secs):
        self.image.exposure_time = secs

    def set_exptime_detonly(self, secs):
        self.image.exposure_time = secs

    def exptime(self):
        return "{} has an exposure time of {} seconds".format(
            colored(self.name, "lightblue"),
            colored(str(self.image.exposure_time), "lightgreen"),
        )

    def set_temp(self, degc):
        self.cam.temperature.set(degc)
        self.cam.enable_cooling.set(1)

    def cooling_off(self):
        self.cam.enable_cooling.set(0)

    #    def setROI(self,):
    #        self.cam.

    def cooling_state(self):
        if self.cam.enable_cooling.get():
            self.cam.temperature_actual.read()
            if self.cam.temperature_actual.get() - self.cam.temperature.get() > 1.0:
                return "\n{} ({} °C) is not at setpoint ({} °C) but cooling is on".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "red"),
                    colored(self.cam.temperature.get(), "blue"),
                )
            else:
                return "\n{} ({} °C) is at setpoint ({} °C) and cooling is on".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "green"),
                    colored(self.cam.temperature.get(), "blue"),
                )
        else:
            if self.cam.temperature_actual.get() - self.cam.temperature.get() > 1.0:
                return "\nTemperature of {} ({} °C) is not at setpoint ({} °C) and cooling is off".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "red"),
                    colored(self.cam.temperature.get(), "lightgray"),
                )
            else:
                return "\nTemperature of {} ({} °C) is at setpoint ({} °C), but cooling is off".format(
                    colored(self.name, "lightblue"),
                    colored(self.cam.temperature_actual.get(), "green"),
                    colored(self.cam.temperature.get(), "lightgray"),
                )

    def set_binning(self, binx, biny):
        self.cam.bin_x.set(binx)
        self.cam.bin_y.set(biny)

    def binning(self):
        return "Binning of {} is set to ({},{}) pixels".format(
            colored(self.name, "lightblue"),
            colored(self.cam.bin_x.get(), "lightpurple"),
            colored(self.cam.bin_y.get(), "lightpurple"),
        )

    def exposure(self):
        return self.exptime()

    def set_exposure(self, seconds):
        self.set_exptime(seconds)
