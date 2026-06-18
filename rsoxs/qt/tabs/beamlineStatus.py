from nbs_gui.tabs.monitorTab import MonitorTab
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from nbs_gui.views.status import StatusBox, SampleStatusBox
from nbs_gui.widgets.utils import HLine
from nbs_gui.views.views import (
    AutoControlBox,
    AutoMonitorBox,
    AutoControl,
    AutoControlCombo,
)
from nbs_gui.widgets.sampleSelect import SampleSelectWidget
from rsoxs.qt.widgets.configuration import ConfigurationSelectWidget


class BeamlineStatusTab(MonitorTab):
    name = "Beamline Status"
    reloadable = True

    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)

    def _create_motor_and_sample_controls(self):
        hbox = QHBoxLayout()
        motor_vbox = QVBoxLayout()
        # Combine available motor-like devices
        motor_devices = {}

        motors = getattr(self.beamline, "motors", {})
        if motors:
            print("Adding motor devices...")
            motor_devices.update(motors)

        manipulators = getattr(self.beamline, "manipulators", {})
        if manipulators:
            print("Adding manipulator devices...")
            motor_devices.update(manipulators)

        mirrors = getattr(self.beamline, "mirrors", {})
        if mirrors:
            print("Adding mirror devices...")
            motor_devices.update(mirrors)

        # Add motor control if any motors are available
        if motor_devices:
            print("Creating motor control widget...")
            motor_vbox.addWidget(AutoControlCombo(motor_devices, "Choose a Motor"))
            print("Motor control widget added")


        hbox.addLayout(motor_vbox)
        # Add sample selection if available
        has_sampleholder = (
            hasattr(self.beamline, "primary_sampleholder")
            and self.beamline.primary_sampleholder is not None
        )
        if has_sampleholder:
            print("Adding sample selection widgets...")
            hbox.addWidget(SampleSelectWidget(self.model))
            config_vbox = QVBoxLayout()
            config_vbox.addWidget(SampleStatusBox(self.user_status, "Selected Sample"))
            config_vbox.addWidget(ConfigurationSelectWidget(self.model))

            hbox.addLayout(config_vbox)
            print("Sample selection widgets added")

        return hbox