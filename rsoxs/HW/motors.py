from ophyd.sim import motor1

from sst_funcs.printing import run_report
from sst_base.motors import PrettyMotorFMBO, PrettyMotor, PrettyMotorDeadbandFlyer, PrettyMotorFMBODeadbandFlyer, PrettyMotorFMBODeadband


run_report(__file__)


sam_viewer = PrettyMotorFMBO(
    "XF:07ID2-ES1{ImgY-Ax:1}Mtr", name="RSoXS Sample Imager", kind="hinted"
)
sam_X = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-ES1{Stg-Ax:X}Mtr", name="RSoXS Sample Outboard-Inboard", kind="hinted"
)
sam_Y = PrettyMotorFMBODeadbandFlyer(
    "XF:07ID2-ES1{Stg-Ax:Y}Mtr", name="RSoXS Sample Up-Down", kind="hinted"
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


