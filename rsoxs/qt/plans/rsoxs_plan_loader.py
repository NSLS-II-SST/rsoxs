from qtpy.QtWidgets import QMessageBox
from qtpy.QtCore import Signal
from bluesky_queueserver_api import BPlan
from nbs_gui.plans.planLoaders import PlanLoaderWidgetBase


class RSoXSPlanLoader(PlanLoaderWidgetBase):
    display_name = "RSoXS Plans"
    signal_update_rsoxs = Signal(object)
    signal_update_samples = Signal(object)

    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self.rsoxs_plans = {}
        self.signal_update_rsoxs.connect(self.update_rsoxs)
        self.user_status.register_signal("RSOXS_PLANS", self.signal_update_rsoxs)

        self.signal_update_samples.connect(self.update_samples)
        self.user_status.register_signal("GLOBAL_SAMPLES", self.signal_update_samples)

    def update_rsoxs(self, rsoxs_plans):
        self.rsoxs_plans = rsoxs_plans

    def update_samples(self, sample_dict):
        self.samples = sample_dict

    def get_plan(self, plan_name):
        plan_name = plan_name.lower()
        if plan_name in self.rsoxs_plans:
            return plan_name
        else:
            for plan_key, plan_info in self.rsoxs_plans.items():
                if plan_name in [
                    plan_info.get("name", "").lower(),
                    plan_info.get("edge", "").lower(),
                ]:
                    return plan_key
        raise KeyError(f"{plan_name} not found in list of RSoXS Plans")

    def create_plan_items(self):
        items = []
        for plan_data in self.plan_queue_data:
            sample_id = plan_data.get("Sample ID")
            plan_name = plan_data.get("Edge")

            try:
                plan = self.get_plan(plan_name)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Plan Generation Error",
                    f"Failed to create plan: {str(e)}",
                    QMessageBox.Ok,
                )
                return []

            if sample_id not in self.samples:
                QMessageBox.critical(
                    self,
                    "Plan Generation Error",
                    f"Sample: {sample_id} not in sample list",
                    QMessageBox.Ok,
                )
                return []

            plan_kwargs = {}
            slit_size = plan_data.get("Slit Size")
            plan_kwargs["eslit"] = float(slit_size) if slit_size not in [None, ""] else None
            plan_kwargs["group_name"] = plan_data.get("Group Name", None)
            plan_kwargs["comment"] = plan_data.get("Comment", None)
            plan_kwargs["repeat"] = int(plan_data.get("Repeat", 1))
            plan_kwargs["n_exposures"] = int(plan_data.get("Exposures", 1))

            item = BPlan(plan, sample=sample_id, **plan_kwargs)
            items.append(item)
        return items
