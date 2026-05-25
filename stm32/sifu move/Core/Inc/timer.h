#ifndef __TIMER_H
#define __TIMER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

extern TIM_HandleTypeDef htim2;
extern TIM_HandleTypeDef htim3;

void Timer_Init(void);
void Timer_Start(void);
void Timer_Stop(void);
void Timer_SetARR(uint32_t arr);
uint32_t Timer_GetARR(void);
void Timer_SetCCR_Sub(uint16_t ccr);
void Timer_SetCCR_Dom(uint16_t ccr);

#ifdef __cplusplus
}
#endif

#endif /* __TIMER_H */
