#ifndef PLC_MITSUBISHI_H
#define PLC_MITSUBISHI_H

// PLC Tag Definitions (auto-generated)
// Generated: 2026-05-06 21:17

#include <stdint.h>

// BOOL Tags
extern bool PLC_Alarm_Active;  // Alarm
extern bool PLC_Motor_Fault;  // Motor Fault
extern bool PLC_Motor_Running;  // Motor Running
extern bool PLC_Motor_Start;  // Motor Start
extern bool PLC_Motor_Stop;  // Motor Stop
extern bool PLC_Pump_Running;  // Pump Running
extern bool PLC_Pump_Start;  // Pump Start
extern bool PLC_Valve_Open;  // Valve Open

// INT Tags
extern int16_t PLC_Conveyor_Speed;  // m/min
extern int16_t PLC_Motor_Speed;  // Motor RPM
extern int16_t PLC_Motor_Torque;  // Torque %
extern int16_t PLC_System_Mode;  // 0=Stop 1=Manual 2=Auto
extern int16_t PLC_Valve_Pos;  // Valve %

// REAL Tags
extern float PLC_Motor_Temp;  // Temp C
extern float PLC_Pump_Pressure;  // Pressure MPa
extern float PLC_Temp_Sensor1;  // Temp C

#endif // PLC_MITSUBISHI_H
