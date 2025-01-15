from sst_base.manipulator import manipulatorFactory4Ax
from nbs_bl.geometry.bars import Standard4SidedBar

def ManipulatorBuilderRSOXS(prefix, *, name, **kwargs):
    holder = Standard4SidedBar(25, 215)
    origin = (0, 0, 464)
    Manipulator = manipulatorFactory4Ax("X}Mtr", "Y}Mtr", "Z}Mtr", "Yaw}Mtr")
    return Manipulator(prefix, name=name, attachment_point=origin, holder=holder, **kwargs)