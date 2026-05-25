#ifndef __MOTION_H
#define __MOTION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

typedef enum {
    MOTION_IDLE = 0,
    MOTION_RUNNING,
    MOTION_ESTOP
} MotionState_t;

void Motion_Init(void);
void Motion_LinearMove(float x_mm, float y_mm, float speed_mm_min);
void Motion_RapidMove(float x_mm, float y_mm);
void Motion_Jog(char axis, int8_t dir, float step_mm);
void Motion_EmergencyStop(void);
void Motion_ClearEstop(void);
void Motion_SetPosition(float x_mm, float y_mm);
void Motion_Update(void);

int32_t Motion_GetXSteps(void);
int32_t Motion_GetYSteps(void);
float Motion_GetX_mm(void);
float Motion_GetY_mm(void);
uint8_t Motion_MoveComplete(void);
MotionState_t Motion_GetState(void);
const char* Motion_GetStateStr(void);
float Motion_GetCurrentSpeed(void);
uint8_t Motion_IsRunning(void);

void Motion_TimerISR(void);

#ifdef __cplusplus
}
#endif

#endif /* __MOTION_H */
