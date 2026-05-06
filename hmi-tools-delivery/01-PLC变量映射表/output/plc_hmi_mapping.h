#ifndef PLC_HMI_MAPPING_H
#define PLC_HMI_MAPPING_H

// PLC Tag Definitions
// Tags: 38
// Generated: 2026-05-06 21:32

#include <stdint.h>

// bool
extern bool PLC_Alarm_Acknowledge;  // 报警确认
extern bool PLC_Alarm_Active;  // 报警指示
extern bool PLC_Conveyor_Fault;  // 传送带故障
extern bool PLC_Conveyor_Running;  // 传送带运行
extern bool PLC_Motor_Fault;  // 电机故障报警
extern bool PLC_Motor_Running;  // 电机运行状态
extern bool PLC_Motor_Start;  // 电机启动信号
extern bool PLC_Motor_Stop;  // 电机停止信号
extern bool PLC_Pump_Running;  // 水泵运行状态
extern bool PLC_Pump_Start;  // 水泵启动
extern bool PLC_Valve_Close;  // 阀门关闭
extern bool PLC_Valve_Open;  // 阀门打开

// int16_t
extern int16_t PLC_Conveyor_Speed;  // 传送带速度 m/min
extern int16_t PLC_Motor_Speed;  // 电机当前转速 RPM
extern int16_t PLC_Motor_Torque;  // 电机扭矩百分比
extern int16_t PLC_Valve_Position;  // 阀门开度百分比 0-100

// uint16_t
extern uint16_t PLC_System_Mode;  // 系统运行模式 0=停止 1=手动 2=自动
extern uint16_t PLC_Valve_Mode;  // 阀门控制模式

// int32_t
extern int32_t PLC_Conveyor_Count;  // 产品计数
extern int32_t PLC_Production_Actual;  // 实际产量
extern int32_t PLC_Production_Defect;  // 次品数量
extern int32_t PLC_Production_Target;  // 生产目标数量

// uint32_t
extern uint32_t PLC_Alarm_Code;  // 故障代码
extern uint32_t PLC_System_Status;  // 系统状态字
extern uint32_t PLC_System_Uptime;  // 系统运行时间

// float
extern float PLC_Level_Sensor;  // 液位传感器 mm
extern float PLC_Motor_Current;  // 电机电流 A
extern float PLC_Motor_Temperature;  // 电机温度 °C
extern float PLC_Pressure_Sensor1;  // 压力传感器1 Bar
extern float PLC_Pressure_Sensor2;  // 压力传感器2 Bar
extern float PLC_Production_Yield;  // 良品率百分比
extern float PLC_Pump_FlowRate;  // 水泵流量 L/min
extern float PLC_Pump_Level;  // 液位高度 mm
extern float PLC_Pump_Pressure;  // 水泵压力 Bar
extern float PLC_Temperature_Avg;  // 平均温度
extern float PLC_Temperature_Sensor1;  // 温度传感器1 °C
extern float PLC_Temperature_Sensor2;  // 温度传感器2 °C
extern float PLC_Temperature_Sensor3;  // 温度传感器3 °C

#endif // PLC_HMI_MAPPING_H
