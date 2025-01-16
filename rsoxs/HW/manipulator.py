from nbs_bl.devices import Manipulator4AxBase
from sst_base.motors import PrettyMotorFMBODeadbandFlyer
from ophyd import Component as Cpt
from nbs_bl.geometry.bars import Standard4SidedBar


def ManipulatorBuilderRSOXS(prefix, *, name, **kwargs):
    class Manipulator(Manipulator4AxBase):
        x = Cpt(PrettyMotorFMBODeadbandFlyer, "X}Mtr", name="x", kind="hinted")
        y = Cpt(PrettyMotorFMBODeadbandFlyer, "Y}Mtr", name="y", kind="hinted")
        z = Cpt(PrettyMotorFMBODeadbandFlyer, "Z}Mtr", name="z", kind="hinted")
        r = Cpt(PrettyMotorFMBODeadbandFlyer, "Yaw}Mtr", name="r", kind="hinted")
        
    holder = Standard4SidedBar(25, 215)
    origin = (0, 0, 464)
    return Manipulator(prefix, name=name, attachment_point=origin, holder=holder, **kwargs)