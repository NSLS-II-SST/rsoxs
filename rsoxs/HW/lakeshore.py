from ophyd import (
        EpicsSignal,
        EpicsSignalRO,
        EpicsSignalWithRBV,
        PVPositioner,
        Device,
        DeviceStatus,
        Component as Cpt
        )
from ophyd.status import MoveStatus
from ophyd.mixins import EpicsSignalPositioner
from collections import deque
from sst_funcs.printing import run_report

run_report(__file__)


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
    setpoint = Cpt(EpicsSignal,'OUT2:SP',kind="normal")
    readback = Cpt(EpicsSignal,'IN2',kind="hinted")
    done = Cpt(EpicsSignal,'RampSts2',kind="normal")
    done_value = 0


    heater_level = Cpt(EpicsSignal,'HTR2:Range_RBV',write_pv='HTR2:Range',string=True,kind="normal")
    heater_mode = Cpt(EpicsSignal,'OUT2:Mode_RBV',write_pv='OUT2:Mode',string=True,kind="normal")
    ramp_speed = Cpt(EpicsSignal,'RampR2_RBV',write_pv='RampR2',kind="normal")
    use_ramp = Cpt(EpicsSignal,'OnRamp2_RBV',write_pv='OnRamp2',kind="normal")



class Lakeshore336Picky(Device):
    setpoint = Cpt(EpicsSignal, read_pv='OUT2:SP_RBV', write_pv='OUT2:SP',
                   add_prefix=('read_pv', 'write_pv'))
    # TODO expose ramp rate
    ramp_done = Cpt(EpicsSignalRO, 'RampSts2')
    ramp_enabled = Cpt(EpicsSignal,'OnRamp2_RBV',write_pv='OnRamp2',kind="normal")
    ramp_rate = Cpt(EpicsSignal,'RampR2_RBV',write_pv='RampR2',kind="normal")

    temperature_actual = Cpt(EpicsSignal, 'IN2',kind='normal')
    readback = Cpt(EpicsSignalPositioner, 'IN2',kind='hinted')

    P = Cpt(EpicsSignal,'P2_RBV',write_pv='P2',kind="config")
    I = Cpt(EpicsSignal,'I2_RBV',write_pv='I2',kind="config")
    D = Cpt(EpicsSignal,'D2_RBV',write_pv='D2',kind="config")

    def __init__(self, *args, timeout=60*60*30, target='setpoint', **kwargs):
        # do the base stuff
        super().__init__(*args, **kwargs)
        # status object for communication
        self._done_sts = None

        # state for deciding if we are done or not
        self._cache = deque()
        self._start_time = 0
        self._setpoint = None
        self._count = -1

        # longest we can wait before giving up
        self._timeout = timeout
        self._lagtime = 120

        # the channel to watch to see if we are done
        self._target_channel = target

        # parameters for done testing
        self.mean_thresh = .01
        self.ptp_thresh = .1

    def _value_cb(self, value, timestamp, **kwargs):
        self._cache.append((value, timestamp))

        if (timestamp - self._cache[0][1]) < self._lagtime / 2:
            return

        while (timestamp - self._cache[0][1]) > self._lagtime:
            self._cache.popleft()

        buff = np.array([v[0] for v in self._cache])
        if self._done_test(self._setpoint, buff):
            self._done_sts._finished()
            self._reset()

    def _setpoint_cb(self, value, **kwargs):
        if value == self._setpoint:
            self._done_sts._finished()
            self.setpoint.clear_sub(self._setpoint_cb, 'value')

    def _reset(self):
        if self._target_channel == 'setpoint':
            target = self.setpoint
            target.clear_sub(self._setpoint_cb, 'value')
        else:
            target = getattr(self, self._target_channel)
            target.clear_sub(self._value_cb, 'value')
        self._done_sts = None
        self._setpoint = None
        self._cache.clear()

    def _done_test(self, target, buff):
        mn = np.mean(np.abs(buff - target))

        if mn > self.mean_thresh:
            return False

        if np.ptp(buff) > self.ptp_thresh:
            return False

        return True


    def set(self, new_position, *, timeout=None):
        # to be subscribed to 'value' cb on readback
        sts = self._done_sts = MoveStatus(self.readback,new_position, timeout=timeout)
        if self.setpoint.get() == new_position:
            self._done_sts._finished()
            self._done_sts = None
            return sts

        self._setpoint = new_position

        self.setpoint.set(self._setpoint)

        # todo, set up subscription forwarding
        if self._target_channel == 'setpoint':
            self.setpoint.subscribe(self._setpoint_cb, 'value')
        else:
            target = getattr(self, self._target_channel)
            target.subscribe(self._value_cb, 'value')

        return self._done_sts





tem_tempstage = Lakeshore336Picky("XF:07ID2-ES1{TCtrl:1}LS336:TC1:", name="TEM temperature controller", kind="normal")
