from ophyd import EpicsSignalRO, EpicsSignal
from ophyd.status import StatusTimeoutError
from sst_funcs.printing import run_report
from sst_base.detectors.scalar import I400SingleCh, ophScalar
from bluesky import plan_stubs as bps
from bluesky import FailedStatus
from datetime import datetime as datet


run_report(__file__)


#signals - not used anymore
bpm13_sum = EpicsSignalRO("XF:07ID-BI{BPM:13}Stats5:Total_RBV", name="Downstream Izero Phosphor Intensity")
ring_current = EpicsSignalRO("SR:OPS-BI{DCCT:1}I:Real-I", name="NSLS-II Ring Current", kind="normal")
sst_control = EpicsSignalRO("XF:07ID1-CT{Bl-Ctrl}Endstn-Sel", name="SST endstation in Control", kind="normal",string=True)

#detectors (Jamie's definition)
Beamstop_WAXS = EpicsSignalRO("XF:07ID-ES1{DMR:I400-1}:IC1_MON", name="WAXS Beamstop", kind="normal")
Beamstop_SAXS = EpicsSignalRO("XF:07ID-ES1{DMR:I400-1}:IC2_MON", name="SAXS Beamstop", kind="normal")
Izero_Diode = EpicsSignalRO("XF:07ID-ES1{DMR:I400-1}:IC3_MON", name="Izero Photodiode", kind="normal")
Slit1_Current_Bottom = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC1_MON", name="RSoXS Slit 1 Bottom Current", kind="normal")
Slit1_Current_Top = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC2_MON", name="RSoXS Slit 1 Top Current", kind="normal")
Slit1_Current_Inboard = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC3_MON", name="RSoXS Slit 1 In Board Current", kind="normal")
Slit1_Current_Outboard = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC4_MON", name="RSoXS Slit 1 Out Board Current", kind="normal")
Slit1_i400_cap = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:CAP_SP", name="RSoXS Slit 1 i400 capasitor", kind="normal",string=True)
diode_i400_cap = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:CAP_SP", name="RSoXS diode i400 capasitor", kind="normal",string=True)
Slit1_i400_enable = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:ENABLE_IC_UPDATES", name="RSoXS Slit 1 i400 enable", kind="normal",string=True)
diode_i400_enable = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:ENABLE_IC_UPDATES", name="RSoXS diode i400 enable", kind="normal",string=True)
Slit1_i400_npnts = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:TRIGPOINTS_SP", name="RSoXS Slit 1 i400 trigger points", kind="normal",string=True)
Slit1_i400_read_time = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:PERIOD_SP", name="RSoXS Slit 1 i400  read time", kind="normal",string=True)
diode_i400_npnts = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:TRIGPOINTS_SP", name="RSoXS diode i400 trigger points", kind="normal",string=True)
Slit1_i400_mode = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:IC_UPDATE_MODE", name="RSoXS Slit 1 i400 mode", kind="normal",string=True)
diode_i400_mode = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:IC_UPDATE_MODE", name="RSoXS diode i400 mode", kind="normal",string=True)
Slit1_i400_accum = EpicsSignal("XF:07ID-ES1{Slt1:I400-1}:ACCUM_SP", name="RSoXS Slit 1 i400 accumulation mode", kind="normal",string=True)
diode_i400_accum = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:ACCUM_SP", name="RSoXS diode i400  accumulation mode", kind="normal",string=True)
diode_i400_read_time = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:PERIOD_SP", name="RSoXS diode i400  read time", kind="normal",string=True)
diode_i400_PDU = EpicsSignal("XF:07ID-CT{RG:C1-PDU:1}Sw:8-Sel", name="RSoXS diode power control", kind="normal",string=True)

mir1_pressure = EpicsSignalRO("XF:07IDA-VA:0{Mir:M1-CCG:1}P:Raw-I", name="Mirror 1 Vacuum Pressure", kind="normal")
Izero_Mesh = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC1_MON", name="RSoXS Au Mesh Current", kind="normal")
Sample_TEY = EpicsSignalRO("XF:07ID-ES1{Slt1:I400-1}:IC2_MON", name="RSoXS Sample Current", kind="normal")

mc19_fault = EpicsSignalRO('SST1_Upstream:MC19AmpFaultSum-Sts',name="MC19 Amp Fault")
mc20_fault = EpicsSignalRO('SST1_Upstream:MC20AmpFaultSum-Sts',name="MC20 Amp Fault")
mc21_fault = EpicsSignalRO('SST1_Upstream:MC21AmpFaultSum-Sts',name="MC21 Amp Fault")

DownstreamLargeDiode = EpicsSignalRO("XF:07ID-ES1{DMR:I400-1}:IC4_MON", name="DownstreamLargeDiode", kind="normal")
Izero_update_time = EpicsSignal("XF:07ID1-BI{EM:1}EM180:AveragingTime",name="RSoXS quadem Averaging Time",kind="normal",)

DiodeRange = EpicsSignal("XF:07ID-ES1{DMR:I400-1}:RANGE_BP")
Temperature_MonoPGM = EpicsSignalRO("XF:07IDA-OP{Mono:PGM}T:Grg-I", name="Temperature_MonoPGM", kind="normal")
Temperature_M3 = EpicsSignalRO("XF:07IDA-OP{Mir:2}T:Mir-I", name="Temperature_M3", kind="normal")
Temperature_M1 = EpicsSignalRO("XF:07IDA-OP{Mir:1}T:Msk-I", name="Temperature_M1", kind="normal")
Temperature_L1 = EpicsSignalRO("XF:07IDA-OP{Mir:L1}T:Msk-I", name="Temperature_L1", kind="normal")

Offset_EPU60_Horizontal = EpicsSignalRO("SR:C31-{AI}Aie7-2:Offset-x-Cal", name="Offset_EPU60_Horizontal", kind="normal")
Offset_EPU60_Vertical = EpicsSignalRO("SR:C31-{AI}Aie7-2:Offset-y-Cal", name="Offset_EPU60_Vertical", kind="normal")
Angle_EPU60_Horizontal = EpicsSignalRO("SR:C31-{AI}Aie7-2:Angle-x-Cal", name="Angle_EPU60_Horizontal", kind="normal")
Angle_EPU60_Vertical = EpicsSignalRO("SR:C31-{AI}Aie7-2:Angle-y-Cal", name="Angle_EPU60_Vertical", kind="normal")
Gap_EPU60 = EpicsSignalRO("SR:C07-ID:G1A{SST1:1-Ax:Gap}-Mtr.RBV", name="Gap_EPU60", kind="normal")
Phase_EPU60 = EpicsSignalRO("SR:C07-ID:G1A{SST1:1-Ax:Phase}-Mtr.RBV", name="Phase_EPU60", kind="normal")

Offset_C07U42_Horizontal = EpicsSignalRO("SR:C31-{AI}Aie7:Offset-x-Cal", name="Offset_C07U42_Horizontal", kind="normal")
Offset_C07U42_Vertical = EpicsSignalRO("SR:C31-{AI}Aie7:Offset-y-Cal", name="Offset_C07U42_Vertical", kind="normal")
Angle_C07U42_Horizontal = EpicsSignalRO("SR:C31-{AI}Aie7:Angle-x-Cal", name="Angle_C07U42_Horizontal", kind="normal")
Angle_C07U42_Vertical = EpicsSignalRO("SR:C31-{AI}Aie7:Angle-y-Cal", name="Angle_C07U42_Vertical", kind="normal")
Gap_C07U42 = EpicsSignalRO("SR:C07-ID:G1A{SST2:1-Ax:Gap}-Mtr.RBV", name="Gap_C07U42", kind="normal")

# scalars (integrating detectors)

Beamstop_WAXS_int =             ophScalar("XF:07ID-ES1{DMR:I400-1}:IC1_MON",        name="WAXS Beamstop",                   kind="normal")
Beamstop_SAXS_int =             ophScalar("XF:07ID-ES1{DMR:I400-1}:IC2_MON",        name="SAXS Beamstop",                   kind="normal")
Izero_Mesh_int =                ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC1_MON",       name="RSoXS Au Mesh Current",           kind="normal")
Sample_TEY_int =                ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC2_MON",       name="RSoXS Sample Current",            kind="normal")
DownstreamLargeDiode_int =      ophScalar("XF:07ID-ES1{DMR:I400-1}:IC4_MON",        name="DownstreamLargeDiode",            kind="normal")
Slit1_Current_Bottom_int =      ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC1_MON",       name="RSoXS Slit 1 Bottom Current",     kind="normal")
Slit1_Current_Top_int =         ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC2_MON",       name="RSoXS Slit 1 Top Current",        kind="normal")
Slit1_Current_Inboard_int =     ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC3_MON",       name="RSoXS Slit 1 In Board Current",   kind="normal")
Slit1_Current_Outboard_int =    ophScalar("XF:07ID-ES1{Slt1:I400-1}:IC4_MON",       name="RSoXS Slit 1 Out Board Current",  kind="normal")
ring_current_int =              ophScalar("SR:OPS-BI{DCCT:1}I:Real-I",              name="NSLS-II Ring Current",            kind="normal")
Gap_EPU60_int =                 ophScalar("SR:C07-ID:G1A{SST1:1-Ax:Gap}-Mtr.RBV",   name="Gap_EPU60",                       kind="normal")
Phase_EPU60_int =               ophScalar("SR:C07-ID:G1A{SST1:1-Ax:Phase}-Mtr.RBV", name="Phase_EPU60",                     kind="normal")
mono_en_int =                   ophScalar("XF:07ID1-OP{Mono:PGM1-Ax::ENERGY_MON",   name="Energy",                          kind="normal")


default_sigs = [Beamstop_WAXS_int,
                Beamstop_SAXS_int,
                Izero_Mesh_int,
                Sample_TEY_int,
                DownstreamLargeDiode_int,
                Slit1_Current_Bottom_int,
                Slit1_Current_Top_int,
                Slit1_Current_Inboard_int,
                Slit1_Current_Outboard_int,
                ring_current_int,
                Gap_EPU60_int,
                Phase_EPU60_int,
                mono_en_int,
]


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



#
"""
RE(bp.count([Beamstop_WAXS, Izero_Mesh, Temperature_MonoPGM, Temperature_M3,
                                                    ...: Temperature_M1, Temperature_L1, Offset_EPU60_Horizontal, Offset_EPU60_Vertica
                                                    ...: l, Angle_EPU60_Horizontal, Angle_EPU60_Vertical, Gap_EPU60, Phase_EPU60, Offs
                                                    ...: et_C07U42_Horizontal, Offset_C07U42_Vertical, Angle_C07U42_Horizontal, Angle_
                                                    ...: C07U42_Vertical, Gap_C07U42, Slit1_Current_Top, Slit1_Current_Bottom, Slit1_C
                                                    ...: urrent_Inboard, Slit1_Current_Outboard], num=5000000000))


"""

"""
RE(bp.count([FS7_cam, Offset_EPU60_Horizontal, Offset_EPU60_Vertical, Angle_EPU60_Horizontal, Angle_EPU60_Vertical], num=5000000000, delay=6-))
"""
