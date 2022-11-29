from ophyd import EpicsSignal, EpicsSignalWithRBV, PVPositioner, Component as Cpt



# XF:07ID2-ES1{TCtrl:1}LS336:TC1:IN2  read back of temperature (channel 2)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:IN2:Name_RBV name of the channel
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OUT2:SP_RBV setpoint read back (celcius)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OUT2:SP setpoint
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:HTR2:Range heater range (0 off, 1 low, 2 medium, 3 high)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:HTR2:Range_RBV heater range readback
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OUT2:Mode (off:0, closed loop :1, zone : 2, open loop:3)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OUT2:Mode_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:P2 proportional gain
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:P2_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:I2 integrative gain
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:I2_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:D2 derivative gain
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:D2_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:RampR2 ramp speed C/min
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:RampR2_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OnRamp2 use the ramp (0 - off, 1 - on)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:OnRamp2_RBV
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:HTR2 current heater output (in percentage)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:IN2:Units
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:RampSts2 ramping loop 2 status (0 off 1 on)
# XF:07ID2-ES1{TCtrl:1}LS336:TC1:D2


class lakeshore_TEM(PVPositioner):
    setpoint = Cpt(EpicsSignalWithRBV,'OUT2:SP_RBV',write_pv='OUT2:SP',string=True,kind="normal")
    readback = Cpt(EpicsSignal,'IN2',string=True,kind="hinted")
    done = Cpt(EpicsSignal,'RampSts2',kind="normal")
    done_value = 0


    heater_level = Cpt(EpicsSignalWithRBV,'HTR2_RBV',write_pv='HTR2',kind="normal")
    heater_mode = Cpt(EpicsSignalWithRBV,'OUT2:Mode_RBV',write_pv='OUT2:Mode',kind="normal")
    ramp_speed = Cpt(EpicsSignalWithRBV,'RampR2_RBV',write_pv='RampR2',kind="normal")
    use_ramp = Cpt(EpicsSignalWithRBV,'OnRamp2_RBV',write_pv='OnRamp2',kind="normal")

    P = Cpt(EpicsSignalWithRBV,'P2_RBV',write_pv='P2',kind="config")
    I = Cpt(EpicsSignalWithRBV,'I2_RBV',write_pv='I2',kind="config")
    D = Cpt(EpicsSignalWithRBV,'D2_RBV',write_pv='D2',kind="config")



temp_TEM = lakeshore_TEM("XF:07ID2-ES1{TCtrl:1}LS336:TC1:", name="TEM temperature controller", kind="normal")

