from sst.CommonFunctions.functions import run_report


run_report(__file__)


pressure_dict = {"Main Chamber Pressure": "XF:07IDB-VA:2{RSoXS:Main-CCG:1}P:Raw-I"}
pressure_dict["Load Lock Pressure"] = "XF:07IDB-VA:2{RSoXS:LL-CCG:1}P:Raw-I"
pressure_dict["Izero Pressure"] = "XF:07IDB-VA:2{RSoXS:DM-CCG:1}P:Raw-I"

valve_dict = {"Front-End Shutter": "XF:07ID-PPS{Sh:FE}Pos-Sts"}
valve_dict["Hutch Photon Shutter"] = "XF:07IDA-PPS{PSh:4}Pos-Sts"
valve_dict["Upstream Photon Shutter"] = "XF:07IDA-PPS{PSh:10}Pos-Sts"
valve_dict["Downstream Photon Shutter"] = "XF:07IDA-PPS{PSh:7}Pos-Sts"
valve_dict["Pre Mono Gate Valve"] = "XF:07IDA-VA:2{FS:6-GV:1}Pos-Sts"
valve_dict["Mono Gate Valve"] = "XF:07IDA-VA:2{FS:6-GV:2}Pos-Sts"
valve_dict["Pre Shutter Gate Valve"] = "XF:07IDB-VA:2{Mono:PGM-GV:1}Pos-Sts"
valve_dict["Post Shutter Gate Valve"] = "XF:07IDB-VA:2{Mir:M3C-GV:1}Pos-Sts"
valve_dict["Upstream Gate Valve"] = "XF:07IDB-VA:3{Slt:C-GV:1}Pos-Sts"
valve_dict["Izero-Main Gate Valve"] = "XF:07IDB-VA:2{RSoXS:Main-GV:1}Pos-Sts"
valve_dict["Downstream Gate Valve"] = "XF:07IDB-VA:2{BT:1-GV:1}Pos-Sts"
valve_dict["TEM Load Lock Gate Valve"] = "XF:07IDB-VA:2{RSoXS:Main-GV:2}Pos-Sts"
valve_dict["Load Lock Gate Valve"] = "XF:07IDB-VA:2{RSoXS:LL-GV:1}Pos-Sts"
valve_dict["Turbo Gate Valve"] = "XF:07IDB-VA:2{RSoXS:TP-GV:1}Pos-Sts"

motor_dict = {"RSoXS Sample Outboard-Inboard": "XF:07ID2-ES1{Stg-Ax:X}Mtr.RBV"}
motor_dict["RSoXS Sample Up-Down"] = "XF:07ID2-ES1{Stg-Ax:Y}Mtr.RBV"
motor_dict["RSoXS Sample Downstream-Upstream"] = "XF:07ID2-ES1{Stg-Ax:Z}Mtr.RBV"
motor_dict["RSoXS Sample Rotation"] = "XF:07ID2-ES1{Stg-Ax:Yaw}Mtr.RBV"
motor_dict["Beam Stop WAXS"] = "XF:07ID2-ES1{BS-Ax:1}Mtr.RBV"
motor_dict["Beam Stop SAXS"] = "XF:07ID2-ES1{BS-Ax:2}Mtr.RBV"
motor_dict["Detector WAXS Translation"] = "XF:07ID2-ES1{Det-Ax:1}Mtr.RBV"
motor_dict["Detector SAXS Translation"] = "XF:07ID2-ES1{Det-Ax:2}Mtr.RBV"
motor_dict["Shutter Vertical Translation"] = "XF:07ID2-ES1{FSh-Ax:1}Mtr.RBV"
motor_dict["Izero Assembly Vertical Translation"] = "XF:07ID2-ES1{Scr-Ax:1}Mtr.RBV"
motor_dict[
    "Downstream Izero DM7 Vertical Translation"
] = "XF:07ID2-BI{Diag:07-Ax:Y}Mtr.RBV"
motor_dict["Exit Slit of Mono Vertical Gap"] = "XF:07ID2-BI{Slt:11-Ax:YGap}Mtr.RBV"

energy_dict = {"Monochromator Energy": "XF:07ID1-OP{Mono:PGM1-Ax::ENERGY_MON"}
energy_dict["EPU Gap"] = "SR:C07-ID:G1A{SST1:1-Ax:Gap}-Mtr.RBV"

slit_dict = {
    "Slit 1 Top": "XF:07ID2-ES1{Slt1-Ax:T}Mtr.RBV",
    "Slit 1 Bottom": "XF:07ID2-ES1{Slt1-Ax:B}Mtr.RBV",
    "Slit 1 Inboard": "XF:07ID2-ES1{Slt1-Ax:I}Mtr.RBV",
    "Slit 1 Outboard": "XF:07ID2-ES1{Slt1-Ax:O}Mtr.RBV",
    "Slit 2 Top": "XF:07ID2-ES1{Slt2-Ax:T}Mtr.RBV",
    "Slit 2 Bottom": "XF:07ID2-ES1{Slt2-Ax:B}Mtr.RBV",
    "Slit 2 Inboard": "XF:07ID2-ES1{Slt2-Ax:I}Mtr.RBV",
    "Slit 2 Outboard": "XF:07ID2-ES1{Slt2-Ax:O}Mtr.RBV",
    "Slit 3 Top": "XF:07ID2-ES1{Slt3-Ax:T}Mtr.RBV",
    "Slit 3 Bottom": "XF:07ID2-ES1{Slt3-Ax:B}Mtr.RBV",
    "Slit 3 Inboard": "XF:07ID2-ES1{Slt3-Ax:I}Mtr.RBV",
    "Slit 3 Outboard": "XF:07ID2-ES1{Slt3-Ax:O}Mtr.RBV",
}
