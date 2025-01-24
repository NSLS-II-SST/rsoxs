from ophyd import (
    Device,
    EpicsSignal,
    EpicsSignalRO,
)
from ophyd import Component as Cpt, DynamicDeviceComponent as DDC
from nbs_bl.printing import run_report


run_report(__file__)


class Syringe_Pump(Device):
    "Syringe pump controller"

    vol_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:Vol-SP" % i, {}) for i in range(1, 3)})
    vol_rb = DDC({"p%d" % i: (EpicsSignalRO, "{Pmp:%s}Val:Vol-RB" % i, {}) for i in range(1, 3)})

    rate_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:Rate-SP" % i, {}) for i in range(1, 3)})
    rate_rb = DDC({"p%d" % i: (EpicsSignalRO, "{Pmp:%s}Val:Rate-RB" % i, {}) for i in range(1, 3)})

    dia_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:Dia-SP" % i, {}) for i in range(1, 3)})
    dia_rb = DDC({"p%d" % i: (EpicsSignalRO, "{Pmp:%s}Val:Dia-RB" % i, {}) for i in range(1, 3)})

    dir_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:Dir-Sel" % i, {}) for i in range(1, 3)})
    dir_rb = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:Dir-Sts" % i, {}) for i in range(1, 3)})

    vol_unit_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Unit:Vol-Sel" % i, {}) for i in range(1, 3)})
    rate_unit_sp = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Unit:Rate-Sel" % i, {}) for i in range(1, 3)})
    vol_unit_rb = DDC({"p%d" % i: (EpicsSignalRO, "{Pmp:%s}Unit:Vol-Sel" % i, {}) for i in range(1, 3)})
    rate_unit_rb = DDC({"p%d" % i: (EpicsSignalRO, "{Pmp:%s}Unit:Rate-Sel" % i, {}) for i in range(1, 3)})

    Run = DDC({"p%s" % i: (EpicsSignal, "{Pmp:%s}Cmd:Run-Cmd" % i, {}) for i in [1, 2, "All"]})
    Stop = DDC({"p%s" % i: (EpicsSignal, "{Pmp:%s}Cmd:Stop-Cmd" % i, {}) for i in [1, 2, "All"]})
    Purge = DDC({"p%s" % i: (EpicsSignal, "{Pmp:%s}Cmd:Purge-Cmd" % i, {}) for i in [1, 2, "All"]})

    disI_vol_rb = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:InfDisp-I" % i, {}) for i in [1, 2]})
    disI_unit_rb = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:InfDisp-I.EGU" % i, {}) for i in [1, 2]})

    disW_vol_rb = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:WdlDisp-I" % i, {}) for i in [1, 2]})
    disW_unit_rb = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Val:WdlDisp-I.EGU" % i, {}) for i in [1, 2]})

    Clr = DDC({"p%d" % i: (EpicsSignal, "{Pmp:%s}Cmd:Clr-Cmd" % i, {}) for i in [1, 2]})

    p = "All"
    run_all = Cpt(EpicsSignal, "{Pmp:%s}Cmd:Run-Cmd" % p)
    purge_all = Cpt(EpicsSignal, "{Pmp:%s}Cmd:Purge-Cmd" % p)
    stop_all = Cpt(EpicsSignal, "{Pmp:%s}Cmd:Stop-Cmd" % p)

    def get_vol(self, pump=1):
        if pump == 1:
            return self.vol_rb.p1.get()
        else:
            return self.vol_rb.p2.get()

    def get_vol_unit(self, pump=1):
        if pump == 1:
            return self.vol_unit_rb.p1.get()
        else:
            return self.vol_unit_rb.p2.get()

    def set_vol_unit(self, pump=1):
        if pump == 1:
            return self.vol_unit_sp.p1.get()
        else:
            return self.vol_unit_sp.p2.get()

    def get_rate_unit(self, pump=1):
        if pump == 1:
            return self.rate_unit_rb.p1.get()
        else:
            return self.rate_unit_rb.p2.get()

    def set_rate_unit(self, pump=1):
        if pump == 1:
            return self.rate_unit_sp.p1.get()
        else:
            return self.rate_unit_sp.p2.get()

    def set_vol(self, val, pump=1):
        if pump == 1:
            return self.vol_sp.p1.set(val)
        else:
            return self.vol_sp.p2.set(val)

    def get_rate(self, pump=1):
        if pump == 1:
            return self.rate_rb.p1.get()
        else:
            return self.rate_rb.p2.valget()

    def set_rate(self, val, pump=1):
        if pump == 1:
            return self.rate_sp.p1.set(val)
        else:
            return self.rate_sp.p2.set(val)

    def get_dia(self, pump=1):
        if pump == 1:
            return self.dia_rb.p1.get()
        else:
            return self.dia_rb.p2.get()

    def set_dia(self, val, pump=1):
        if pump == 1:
            return self.dia_sp.p1.set(val)
        else:
            return self.dia_sp.p2.set(val)

    def get_dir(self, pump=1):
        if pump == 1:
            return self.dir_rb.p1.get()
        else:
            return self.dir_rb.p2.get()

    def set_dir(self, val, pump=1):
        if pump == 1:
            return self.dir_sp.p1.set(val)
        else:
            return self.dir_sp.p2.set(val)

    def run(self, pump=1):
        if pump == 1:
            return self.Run.p1.set(1)
        elif pump == 2:
            return self.Run.p2.set(1)
        else:
            return self.Run.pAll.set(1)

    def stop(self, pump=1):
        if pump == 1:
            return self.Stop.p1.set(1)
        elif pump == 2:
            return self.Stop.p2.set(1)
        else:
            return self.Stop.pAll.set(1)

    def get_disvol(
        self,
        pump=1,
        Dir=None,
    ):
        """dir: 0 for infusion, 1 for withdraw"""
        if Dir is None:
            Dir = self.get_dir(pump)
        if Dir == 0:
            if pump == 1:
                return self.disI_vol_rb.p1.get()
            else:
                return self.disI_vol_rb.p2.get()
        else:
            if pump == 1:
                return self.disW_vol_rb.p1.get()
            else:
                return self.disW_vol_rb.p2.get()

    def clr(
        self,
        pump=1,
        Dir=None,
    ):
        """dir: 0 for infusion, 1 for withdraw"""
        if Dir is None:
            Dir = self.get_dir(pump)
        if pump == 1:
            return self.Clr.p1.set(Dir)
        else:
            return self.Clr.p2.set(Dir)

    @property
    def hints(self):
        fields = []
        for name in self.component_names:
            motor = getattr(self, name)
            fields.extend(motor.hints["fields"])
        return {"fields": fields}
