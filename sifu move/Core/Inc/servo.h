#ifndef __SERVO_H
#define __SERVO_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

typedef enum {
    HOME_IDLE = 0,
    HOME_X_FAST,
    HOME_X_BACKOFF,
    HOME_X_SETZERO,
    HOME_Y_FAST,
    HOME_Y_BACKOFF,
    HOME_Y_SETZERO,
    HOME_DONE
} HomeState_t;

void Servo_Init(void);
void Servo_Enable(void);
void Servo_Disable(void);
uint8_t Servo_AlarmCheck(void);
uint8_t Servo_GetAlarmCode(void);

void Servo_Home_Start(void);
uint8_t Servo_Home_Update(void);
void Servo_Home_Abort(void);
uint8_t Servo_IsHoming(void);
HomeState_t Servo_GetHomeState(void);

#ifdef __cplusplus
}
#endif

#endif /* __SERVO_H */
