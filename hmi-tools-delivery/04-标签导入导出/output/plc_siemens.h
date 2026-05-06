#ifndef PLC_SIEMENS_H
#define PLC_SIEMENS_H

// PLC Tag Definitions (auto-generated)
// Generated: 2026-05-06 21:17

#include <stdint.h>

// BOOL Tags
extern bool PLC_Alarm_Active;  // Alarm Indicator
extern bool PLC_Motor_Fault;  // Fault Alarm
extern bool PLC_Motor_Running;  // Running Status
extern bool PLC_Motor_Start;  // Motor Start
extern bool PLC_Motor_Stop;  // Motor Stop
extern bool PLC_Pump_Running;  // Pump Running
extern bool PLC_Pump_Start;  // Pump Start
extern bool PLC_Valve_Close;  // Valve Close
extern bool PLC_Valve_Open;  // Valve Open

// WORD Tags
extern uint16_t PLC_System_Mode;  // 0=Stop 1=Run 2=Auto

// DWORD Tags
extern uint32_t PLC_Alarm_Code;  // Fault Code

// INT Tags
extern int16_t PLC_Motor_Speed;  // RPM
extern int16_t PLC_Motor_Torque;  // Torque %
extern int16_t PLC_Valve_Position;  // Position 0-100%

// DINT Tags
extern int32_t PLC_Production_Count;  // Total Count

// REAL Tags
extern float PLC_Motor_Current;  // Current A
extern float PLC_Motor_Temp;  // Temperature C
extern float PLC_Production_Yield;  // Yield %
extern float PLC_Pump_Pressure;  // Pressure Bar
extern float PLC_Temp_Sensor1;  // Temp Sensor 1
extern float PLC_Temp_Sensor2;  // Temp Sensor 2

#endif // PLC_SIEMENS_H
