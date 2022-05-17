import bluesky.plan_stubs as bps
import bluesky.plans as bp
from sst_hw.energy import (
    EnPos,EnSimEPUPos,
    base_grating_to_250,
    base_grating_to_1200,
    base_set_polarization,
    grating,
    mirror2
)
from ..HW.motors import sam_Th, sam_X, sam_Y
from sst_funcs.printing import run_report
from sst_hw.diode import Shutter_control
from .signals import Sample_TEY
from ..startup import bec


run_report(__file__)

#en = EnSimEPUPos("", rotation_motor=sam_Th, name="en")
en = EnPos("", rotation_motor=sam_Th, name="en")
en.energy.kind = "hinted"
en.monoen.kind = "normal"
mono_en = en.monoen
mono_en.tolerance.set(0.02)
epu_gap = en.epugap
epu_gap.tolerance.set(2)
epu_phase = en.epuphase
epu_phase.tolerance.set(10)
epu_mode = en.epumode
en.mir3Pitch.tolerance.set(0.01)
mono_en.readback.kind = "normal"
en.epugap.kind = "normal"
en.epuphase.kind = "normal"
en.polarization.kind = "normal"
en.sample_polarization.kind = "normal"
en.read_attrs = ["energy", "polarization", "sample_polarization"]
en.epugap.read_attrs = ["user_readback", "user_setpoint"]
en.monoen.read_attrs = [
    "readback",
    "grating",
    "grating.user_readback",
    "grating.user_setpoint",
    "grating.user_offset",
    "mirror2",
    "mirror2.user_readback",
    "mirror2.user_offset",
    "mirror2.user_setpoint",
    "cff",
]
en.monoen.grating.kind = "normal"
en.monoen.mirror2.kind = "normal"
en.monoen.gratingx.kind = "normal"
en.monoen.mirror2x.kind = "normal"
en.epugap.kind = "normal"
en.epugap.kind = "normal"

Mono_Scan_Start_ev = en.monoen.Scan_Start_ev
Mono_Scan_Stop_ev = en.monoen.Scan_Stop_ev
Mono_Scan_Speed_ev = en.monoen.Scan_Speed_ev
Mono_Scan_Start = en.monoen.Scan_Start
Mono_Scan_Stop = en.monoen.Scan_Stop

def set_polarization(pol):
    yield from base_set_polarization(pol, en)


def grating_to_1200(hopgx=None,hopgy=None,hopgtheta=None):
    moved = yield from base_grating_to_1200(mono_en, en)
    try:
        x = float(hopgx)
        y = float(hopgy)
        th = float(hopgtheta)
    except Exception:
        x = None
        y = None
        th = None
    if moved and isinstance(x,float) and isinstance(y,float) and isinstance(th,float):
        ensave = en.energy.setpoint.get()
        xsave = sam_X.user_setpoint.get()
        ysave = sam_Y.user_setpoint.get()
        thsave = sam_Th.user_setpoint.get()
        bec.enable_plots()
        Sample_TEY.kind='hinted'
        yield from bps.mv(sam_X,hopgx,sam_Y,hopgy,sam_Th,hopgtheta)
        yield from bps.mv(en.polarization, 0)
        yield from bps.mv(en, 291.65)
        yield from bps.sleep(1)
        yield from bps.mv(en, 291.65)
        yield from bps.sleep(1)
        yield from bps.mv(en, 291.65)
        yield from bps.mv(en.polarization, 0)
        yield from bps.mv(Shutter_control,1)
        yield from bp.rel_scan([Sample_TEY],grating,-0.05,.05,mirror2,-0.05,.05,201)
        yield from bps.mv(Shutter_control,0)
        yield from bps.mv(sam_X,xsave,sam_Y,ysave,sam_Th,thsave)
        yield from bps.sleep(5)
        newoffset = en.monoen.grating.get()[0] - bec.peaks.max['RSoXS Sample Current'][0]
        if -0.05 < newoffset < 0.05 :
            yield from bps.mvr(grating.user_offset,newoffset,mirror2.user_offset,newoffset)
        yield from bps.mv(en, ensave)
        bec.disable_plots()
        Sample_TEY.kind='normal'


def grating_to_250(hopgx=None,hopgy=None,hopgtheta=None):
    moved = yield from base_grating_to_250(mono_en, en)
    try:
        x = float(hopgx)
        y = float(hopgy)
        th = float(hopgtheta)
    except Exception:
        x = None
        y = None
        th = None
    if moved and isinstance(x,float) and isinstance(y,float) and isinstance(th,float):
        ensave = en.energy.setpoint.get()
        xsave = sam_X.user_setpoint.get()
        ysave = sam_Y.user_setpoint.get()
        thsave = sam_Th.user_setpoint.get()
        bec.enable_plots()
        Sample_TEY.kind='hinted'
        yield from bps.mv(sam_X,x,sam_Y,y,sam_Th,th)
        yield from bps.mv(en.polarization, 0)
        yield from bps.mv(en, 291.65)
        yield from bps.sleep(1)
        yield from bps.mv(en, 291.65)
        yield from bps.sleep(1)
        yield from bps.mv(en, 291.65)
        yield from bps.mv(Shutter_control,1)
        yield from bp.rel_scan([Sample_TEY],grating,-0.1,.1,mirror2,-0.1,.1,201)
        yield from bps.mv(Shutter_control,0)
        yield from bps.mv(sam_X,xsave,sam_Y,ysave,sam_Th,thsave)
        yield from bps.sleep(5)
        newoffset = en.monoen.grating.get()[0] - bec.peaks.max['RSoXS Sample Current'][0]
        if -0.05 < newoffset < 0.05 :
            yield from bps.mvr(grating.user_offset,newoffset,mirror2.user_offset,newoffset)
        yield from bps.mv(en, ensave)
        bec.disable_plots()
        Sample_TEY.kind='normal'
