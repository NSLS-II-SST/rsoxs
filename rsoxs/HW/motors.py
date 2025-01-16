from ophyd.sim import motor1
from ophyd import EpicsSignal

from nbs_bl.printing import run_report
from sst_base.motors import PrettyMotorFMBO, PrettyMotor, PrettyMotorDeadbandFlyer, PrettyMotorFMBODeadbandFlyer, PrettyMotorFMBODeadband

class RetryFlyerMotor(PrettyMotorFMBODeadbandFlyer):
    def __init__(self,*args,retries=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.retries = retries
    
    def move(self, position,wait=True, **kwargs):
        """Move to a specified position, trying 5 times
        """
        self._started_moving = False
        not_in_position = True
        failed_count = 0
        while not_in_position:
            try:
                status = super().move(position,wait=True, **kwargs) # ignore wait parameter, we always wait with this motor
            except FailedStatus:
                failed_count +=1
                if failed_count < self.retries+1:
                    warnings.warn(f'Motor failed to get to position, trying again (try {failed_count})',stacklevel=2)
                    pass
                else:
                    raise FailedStatus(f"Failed to move to position after {self.retries} tries")
            else:
                not_in_position = False
        return status



class ShutterWait(EpicsSignal):
    def set(self, value, *, just_wait=False, **kwargs):
            """
            Set the value of the Signal, or just wait for the object to change to a value, either way returning a Status object

            Parameters
            ----------
            value : either a set value of a value to wait for
            just_wait : boolean whether to not set anything but just wait for the value to change to this value
            
            Returns
            -------
            Status

            """
            if(just_wait):
                wait_value = value
                def watcher(*,old_value,value,**kwargs):
                    if value == wait_value:
                        return True
                    else:
                        return False
                return SubscriptionStatus(self, watcher)
            else:
                return super().set(value, **kwargs)


run_report(__file__)


sam_viewer = PrettyMotorFMBO(
    "XF:07ID2-ES1{ImgY-Ax:1}Mtr", name="RSoXS Sample Imager", kind="hinted"
)
sam_X = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-ES1{Stg-Ax:X}Mtr", name="RSoXS Sample Outboard-Inboard", kind="hinted"#,retries=5
)
sam_Y = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-ES1{Stg-Ax:Y}Mtr", name="RSoXS Sample Up-Down", kind="hinted"#,retries=3,
)
sam_Z = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-ES1{Stg-Ax:Z}Mtr", name="RSoXS Sample Downstream-Upstream", kind="hinted"
)
sam_Th = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{Stg-Ax:Yaw}Mtr", name="RSoXS Sample Rotation", kind="hinted"
)
BeamStopW = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{BS-Ax:1}Mtr", name="Beam Stop WAXS", kind="hinted"
)
BeamStopS = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{BS-Ax:2}Mtr", name="Beam Stop SAXS", kind="hinted"
)
Det_W = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{Det-Ax:2}Mtr", name="Detector WAXS Translation", kind="hinted"
)
Det_S = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{Det-Ax:1}Mtr", name='Detector SAXS Translation',kind='hinted'
)
# Det_S = motor1
# Det_S.user_setpoint = Det_S.setpoint
Shutter_Y = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{FSh-Ax:1}Mtr", name="Shutter Vertical Translation", kind="hinted"
)
Izero_Y = PrettyMotorFMBODeadband(
    "XF:07ID2-ES1{Scr-Ax:1}Mtr",
    name="Izero Assembly Vertical Translation",
    kind="hinted",
)
Izero_ds = PrettyMotorFMBO(
    "XF:07ID2-BI{Diag:07-Ax:Y}Mtr",
    name="Downstream Izero DM7 Vertical Translation",
    kind="hinted",
)

TEMX = PrettyMotor(
    "XF:07ID1-ES:1{Smpl-Ax:X}Mtr", name="RSoXS TEM Upstream-Downstream", kind="hinted"
)
TEMY = PrettyMotor(
    "XF:07ID1-ES:1{Smpl-Ax:Y}Mtr", name="RSoXS TEM Up-Down", kind="hinted"
)
TEMZ = PrettyMotor(
    "XF:07ID1-ES:1{Smpl-Ax:Z}Mtr", name="RSoXS TEM Inboard-Outboard", kind="hinted"
)

dm7 = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-BI{Diag:07-Ax:Y}Mtr", name="Downstream diagnostic module translation", kind="normal"
)



