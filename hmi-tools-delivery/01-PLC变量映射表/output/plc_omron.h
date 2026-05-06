#ifndef PLC_OMRON_H
#define PLC_OMRON_H

// PLC Tag Definitions
// Tags: 9
// Generated: 2026-05-06 21:17

#include <stdint.h>

// bool
extern bool PLC_Motor_Fault;  // Fault
extern bool PLC_Motor_Running;  // Running
extern bool PLC_Motor_Start;  // Motor Start
extern bool PLC_Motor_Stop;  // Motor Stop
extern bool PLC_Valve_Open;  // Valve Open

// int16_t
extern int16_t PLC_Motor_Speed;  // RPM

// uint16_t
extern uint16_t PLC_System_Mode;  // 0=Stop 1=Run

// float
extern float PLC_Motor_Temp;  // Temp C
extern float PLC_Pump_Pressure;  // Pressure

#endif // PLC_OMRON_H
