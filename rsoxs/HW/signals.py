from ophyd import EpicsSignalRO, EpicsSignal
from ophyd.status import StatusTimeoutError
from sst_funcs.printing import run_report
from sst_base.detectors.scalar import I400SingleCh
from bluesky import plan_stubs as bps
from bluesky import FailedStatus
from datetime import datetime as datet


run_report(__file__)

# These might need/make more sense to be split up into separate files later on.
# But while we have so few, I'm just putting them in this single file.

bpm13_sum = EpicsSignalRO(
    "XF:07ID-BI{BPM:13}Stats5:Total_RBV", name="Downstream Izero Phosphor Intensity"
)

ring_current = EpicsSignalRO(
    "SR:OPS-BI{DCCT:1}I:Real-I", name="NSLS-II Ring Current", kind="normal"
)
sst_control = EpicsSignalRO(
    "XF:07ID1-CT{Bl-Ctrl}Endstn-Sel", name="SST endstation in Control", kind="normal",string=True
)
Beamstop_WAXS = EpicsSignalRO(
    "XF:07ID-ES1{DMR:I400-1}:IC1_MON", name="WAXS Beamstop", kind="normal"
)
Beamstop_SAXS = EpicsSignalRO(
    "XF:07ID-ES1{DMR:I400-1}:IC2_MON", name="SAXS Beamstop", kind="normal"
)
Izero_Diode = EpicsSignalRO(
    "XF:07ID-ES1{DMR:I400-1}:IC3_MON", name="Izero Photodiode", kind="normal"
)

Slit1_Current_Bottom = EpicsSignalRO(
    "XF:07ID-ES1{Slt1:I400-1}:IC1_MON", name="RSoXS Slit 1 Bottom Current", kind="normal"
)
Slit1_Current_Top = EpicsSignalRO(
    "XF:07ID-ES1{Slt1:I400-1}:IC2_MON", name="RSoXS Slit 1 Top Current", kind="normal"
)
Slit1_Current_Inboard = EpicsSignalRO(
    "XF:07ID-ES1{Slt1:I400-1}:IC3_MON", name="RSoXS Slit 1 In Board Current", kind="normal"
)
Slit1_Current_Outboard = EpicsSignalRO(
    "XF:07ID-ES1{Slt1:I400-1}:IC4_MON", name="RSoXS Slit 1 Out Board Current", kind="normal"
)

Slit1_i400_cap = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:CAP_SP", name="RSoXS Slit 1 i400 capasitor", kind="normal"
,string=True)
diode_i400_cap = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:CAP_SP", name="RSoXS diode i400 capasitor", kind="normal"
,string=True)
Slit1_i400_enable = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:ENABLE_IC_UPDATES", name="RSoXS Slit 1 i400 enable", kind="normal"
,string=True)
diode_i400_enable = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:ENABLE_IC_UPDATES", name="RSoXS diode i400 enable", kind="normal"
,string=True)
Slit1_i400_npnts = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:TRIGPOINTS_SP", name="RSoXS Slit 1 i400 trigger points", kind="normal"
,string=True)
Slit1_i400_read_time = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:PERIOD_SP", name="RSoXS Slit 1 i400  read time", kind="normal"
,string=True)
diode_i400_npnts = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:TRIGPOINTS_SP", name="RSoXS diode i400 trigger points", kind="normal"
,string=True)
Slit1_i400_mode = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:IC_UPDATE_MODE", name="RSoXS Slit 1 i400 mode", kind="normal"
,string=True)
diode_i400_mode = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:IC_UPDATE_MODE", name="RSoXS diode i400 mode", kind="normal"
,string=True)
Slit1_i400_accum = EpicsSignal(
    "XF:07ID-ES1{Slt1:I400-1}:ACCUM_SP", name="RSoXS Slit 1 i400 accumulation mode", kind="normal"
,string=True)
diode_i400_accum = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:ACCUM_SP", name="RSoXS diode i400  accumulation mode", kind="normal"
,string=True)
diode_i400_read_time = EpicsSignal(
    "XF:07ID-ES1{DMR:I400-1}:PERIOD_SP", name="RSoXS diode i400  read time", kind="normal"
,string=True)


diode_i400_PDU = EpicsSignal(
    "XF:07ID-CT{RG:C1-PDU:1}Sw:8-Sel", name="RSoXS diode power control", kind="normal"
,string=True)



def setup_slit1_i400():
    yield from bps.mv(Slit1_i400_enable, 'Disabled')
    try:
        yield from bps.mv(Slit1_i400_cap, '1000pF',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(Slit1_i400_npnts, 940,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(Slit1_i400_read_time, 0.001,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(Slit1_i400_mode, 'Trigger Count',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(Slit1_i400_accum, 'Interpolate',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(Slit1_i400_enable, 'Enabled',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass



def setup_diode_i400():
    yield from bps.mv(diode_i400_enable, 'Disabled')
    try:
        yield from bps.mv(diode_i400_cap, '1000pF',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_npnts, 200,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_mode, 'Trigger Count',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_read_time, 0.001,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_accum, 'Interpolate',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_enable, 'Enabled',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass


def High_Gain_diode_i400():
    yield from bps.mv(diode_i400_enable, 'Disabled')
    try:
        yield from bps.mv(diode_i400_cap, '10pF',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_npnts, 20,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_mode, 'Trigger Count',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_read_time, 0.01,timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_accum, 'Interpolate',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass
    try:
        yield from bps.mv(diode_i400_enable, 'Enabled',timeout=1)
    except FailedStatus:
        pass
    except StatusTimeoutError:
        pass


def power_cycle_diode_i400():
    yield from bps.mv(diode_i400_PDU,"Off")
    yield from bps.sleep(2)
    yield from bps.mv(diode_i400_PDU,"On")


def reset_diodes():
    yield from power_cycle_diode_i400()
    yield from bps.sleep(5)
    yield from setup_diode_i400()


def check_diodes():
    if datet.timestamp(datet.now())-Beamstop_SAXS.read()['SAXS Beamstop']['timestamp'] > 1:
        yield from reset_diodes()


mir1_pressure = EpicsSignalRO(
    "XF:07IDA-VA:0{Mir:M1-CCG:1}P:Raw-I", name="Mirror 1 Vacuum Pressure", kind="normal"
)


# IzeroMesh    = EpicsSignalRO('XF:07ID-ES1{Slt1:I400-1}:IC4_MON',name = 'Izero Mesh I400', kind='normal')
# Sample_EY = EpicsSignalRO('XF:07ID-ES1{Slt1:I400-1}:IC1_MON',name = 'RSoXS Drain', kind='normal')
# SlitBottom_I = EpicsSignalRO('XF:07ID-ES1{Slt1:I400-1}:IC2_MON',name = 'Slit 1 Bottom Current', kind='normal')
# SlitTop_I    = EpicsSignalRO('XF:07ID-ES1{Slt1:I400-1}:IC3_MON',name = 'Slit Top', kind='normal')


# Beamstop_SAXS  = EpicsSignalRO('XF:07ID1-BI{EM:1}EM180:Current3:MeanValue_RBV',
#                           name = 'SAXS Beamstop', kind='hinted')
Izero_Mesh = EpicsSignalRO(
    "XF:07ID1-BI{EM:1}EM180:Current2:MeanValue_RBV",
    name="RSoXS Au Mesh Current",
    kind="normal",
)
Sample_TEY = EpicsSignalRO(
    "XF:07ID1-BI{EM:1}EM180:Current1:MeanValue_RBV",
    name="RSoXS Sample Current",
    kind="normal",
)


Izero_update_time = EpicsSignal(
     "XF:07ID1-BI{EM:1}EM180:AveragingTime",
     name="RSoXS quadem Averaging Time",
     kind="normal",)

DiodeRange = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:RANGE_BP")

# DM7_Diode = EpicsSignalRO('XF:07ID-BI{DM7:I400-1}:IC4_MON',name = 'DM7 Photodiode', kind='normal')
DM4_PD = EpicsSignalRO(
    "XF:07ID-BI{DM5:F4}Cur:I3-I", name="DM4 Photodiode", kind="normal"
)

# scalars (integrating detectors)

Beamstop_WAXS_int = I400SingleCh(
    "XF:07ID-ES1{DMR:I400-1}:IC1_MON", name="WAXS Beamstop", kind="normal"
)
Beamstop_SAXS_int = I400SingleCh(
    "XF:07ID-ES1{DMR:I400-1}:IC2_MON", name="SAXS Beamstop", kind="normal"
)
Izero_Mesh_int = I400SingleCh(
    "XF:07ID1-BI{EM:1}EM180:Current2:MeanValue_RBV",
    name="RSoXS Au Mesh Current",
    kind="normal",
)
Sample_TEY_int = I400SingleCh(
    "XF:07ID1-BI{EM:1}EM180:Current1:MeanValue_RBV",
    name="RSoXS Sample Current",
    kind="normal",
)