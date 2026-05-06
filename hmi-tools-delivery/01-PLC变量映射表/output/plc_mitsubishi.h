#ifndef PLC_MITSUBISHI_H
#define PLC_MITSUBISHI_H

// PLC Tag Definitions
// Tags: 12
// Generated: 2026-05-06 21:17

#include <stdint.h>

// bool
extern bool PLC_Alarm_Active;  // Alarm Output
extern bool PLC_Motor_Fault;  // Motor Fault
extern bool PLC_Motor_Running;  // Motor Running
extern bool PLC_Motor_Start;  // Motor Start
extern bool PLC_Motor_Stop;  // Motor Stop
extern bool PLC_Pump_Running;  // Pump Running
extern bool PLC_Pump_Start;  // Pump Start

// uint16_t
extern uint16_t PLC_Motor_Speed;  // RPM
extern uint16_t PLC_Motor_Torque;  // Torque %
extern uint16_t PLC_System_Mode;  // 0=Stop 1=Auto

// float
extern float PLC_Motor_Temp;  // Temp C
extern float PLC_Pump_Pressure;  // Pressure MPa

#endif // PLC_MITSUBISHI_H
