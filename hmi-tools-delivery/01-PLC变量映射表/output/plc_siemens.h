#ifndef PLC_SIEMENS_H
#define PLC_SIEMENS_H

// PLC Tag Definitions
// Tags: 17
// Generated: 2026-05-06 21:17

#include <stdint.h>

// bool
extern bool PLC_Motor_Fault;  // Fault Alarm
extern bool PLC_Motor_Running;  // Running Status
extern bool PLC_Motor_Start;  // Motor Start
extern bool PLC_Motor_Stop;  // Motor Stop
extern bool PLC_Pump_Running;  // Pump Running
extern bool PLC_Pump_Start;  // Pump Start
extern bool PLC_Valve_Open;  // Valve Open

// int16_t
extern int16_t PLC_Motor_Speed;  // RPM
extern int16_t PLC_Motor_Torque;  // Torque %
extern int16_t PLC_Valve_Position;  // 0-100%

// uint16_t
extern uint16_t PLC_System_Mode;  // 0=Stop 1=Run

// int32_t
extern int32_t PLC_Production_Count;  // Total Count

// uint32_t
extern uint32_t PLC_Alarm_Code;  // Fault Code

// float
extern float PLC_Motor_Temp;  // Temperature C
extern float PLC_Pump_Pressure;  // Pressure Bar
extern float PLC_Temp_Sensor1;  // Temp C
extern float PLC_Temp_Sensor2;  // Temp C

#endif // PLC_SIEMENS_H
