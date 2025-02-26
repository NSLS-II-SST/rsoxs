from nbs_gui.plans.variableStepPlan import VariableStepParam
from nbs_gui.plans.nbsPlan import NBSPlanWidget
from nbs_gui.plans.xasPlan import XASPlanWidget
from qtpy.QtCore import Signal
from bluesky_queueserver_api import BPlan


class RSoXSCustomWidget(NBSPlanWidget):
    signal_update_motors = Signal(object)
    display_name = "RSoXS Custom Scan"

    def __init__(
        self,
        model,
        parent=None,
        plans="rsoxs_step_scan",
    ):
        print("Initializing RSoXS Custom Scan")
        super().__init__(
            model,
            parent,
            plans,
            n_exposures={
                "type": "spinbox",
                "args": {"minimum": 1, "value_type": int, "default": 1},
                "label": "Number of Exposures per Step",
            },
            dwell={
                "type": "spinbox",
                "args": {"minimum": 0.1, "value_type": float, "default": 1},
                "label": "Dwell Time per Step (s)",
            },
            layout_style=2,
        )
        self.scan_widget.add_param(VariableStepParam(self))
        # print("Variable Scan Initialized")

    def check_plan_ready(self):
        params = self.get_params()
        checks = [self.scan_widget.check_ready()]
        self.plan_ready.emit(all(checks))

    def create_plan_items(self):
        params = self.get_params()
        samples = params.pop("samples", [{}])
        args = params.pop("args")
        items = []
        for sample in samples:
            item = BPlan(
                self.current_plan,
                *args,
                **params,
                **sample,
            )
            items.append(item)
        return items
