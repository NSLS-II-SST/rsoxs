from qtpy.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QGroupBox,
)
from qtpy.QtCore import Signal

from nbs_gui.widgets.qt_custom import ScrollingComboBox


from bluesky_queueserver_api import BPlan

class ConfigurationSelectWidget(QGroupBox):
    signal_update_options = Signal(object)

    def __init__(self, model, parent=None, **kwargs):
        super().__init__("Configuration Selection", parent=parent)
        self.run_engine = model.run_engine
        self.user_status = model.user_status
        self.signal_update_options.connect(self.update_configuration_combo)
        self.user_status.register_signal("RSoXS_Config", self.signal_update_options)

        vbox = QVBoxLayout()
        self.configuration_combo = ScrollingComboBox(max_visible_items=10)
        self.load_configuration_button = QPushButton("Load Configuration")
        self.load_configuration_button.clicked.connect(self.load_configuration)
        vbox.addWidget(self.configuration_combo)
        vbox.addWidget(self.load_configuration_button)
        self.setLayout(vbox)

    def update_configuration_combo(self, configurations):
        self.configuration_combo.clear()
        options = list(configurations.keys())
        print(f"Updating configuration combo with configurations: {options}")
        self.configuration_combo.addItems(options)

    def load_configuration(self):
        configuration = self.configuration_combo.currentText()
        plan = BPlan("load_configuration", configuration)

        try:
            self.run_engine._client.item_execute(plan)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Load Error",
                f"Failed to load configuration: {str(e)}",
                QMessageBox.Ok,
            )