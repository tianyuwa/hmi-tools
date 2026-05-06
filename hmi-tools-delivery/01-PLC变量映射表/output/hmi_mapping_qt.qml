import QtQuick 2.15

// PLC Tag Bindings (auto-generated)
// Tags: 38 | Brand: siemens
// Generated: 2026-05-06 21:32

QtObject {
    property bool Motor_Start: 0  // 电机启动信号
    property bool Motor_Stop: 0  // 电机停止信号
    property bool Motor_Running: 0  // 电机运行状态
    property bool Motor_Fault: 0  // 电机故障报警
    property int Motor_Speed: 0  // 电机当前转速 RPM
    property int Motor_Torque: 0  // 电机扭矩百分比
    property real Motor_Temperature: 0  // 电机温度 °C
    property real Motor_Current: 0  // 电机电流 A
    property bool Pump_Start: 0  // 水泵启动
    property bool Pump_Running: 0  // 水泵运行状态
    property real Pump_Pressure: 0  // 水泵压力 Bar
    property real Pump_FlowRate: 0  // 水泵流量 L/min
    property real Pump_Level: 0  // 液位高度 mm
    property bool Valve_Open: 0  // 阀门打开
    property bool Valve_Close: 0  // 阀门关闭
    property int Valve_Position: 0  // 阀门开度百分比 0-100
    property int Valve_Mode: 0  // 阀门控制模式
    property real Temperature_Sensor1: 0  // 温度传感器1 °C
    property real Temperature_Sensor2: 0  // 温度传感器2 °C
    property real Temperature_Sensor3: 0  // 温度传感器3 °C
    property real Temperature_Avg: 0  // 平均温度
    property real Pressure_Sensor1: 0  // 压力传感器1 Bar
    property real Pressure_Sensor2: 0  // 压力传感器2 Bar
    property real Level_Sensor: 0  // 液位传感器 mm
    property int Conveyor_Speed: 0  // 传送带速度 m/min
    property bool Conveyor_Running: 0  // 传送带运行
    property bool Conveyor_Fault: 0  // 传送带故障
    property int Conveyor_Count: 0  // 产品计数
    property bool Alarm_Active: 0  // 报警指示
    property bool Alarm_Acknowledge: 0  // 报警确认
    property int Alarm_Code: 0  // 故障代码
    property int System_Mode: 0  // 系统运行模式 0=停止 1=手动 2=自动
    property int System_Status: 0  // 系统状态字
    property int System_Uptime: 0  // 系统运行时间
    property int Production_Target: 0  // 生产目标数量
    property int Production_Actual: 0  // 实际产量
    property int Production_Defect: 0  // 次品数量
    property real Production_Yield: 0  // 良品率百分比
}
