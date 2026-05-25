#ifndef __SYS_TICK_H
#define __SYS_TICK_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

void SysTick_Setup(void);
void SysTick_ISR(void);
uint32_t SysTick_GetMs(void);
uint8_t SysTick_CheckElapsed(uint32_t *last, uint32_t interval);

#ifdef __cplusplus
}
#endif

#endif /* __SYS_TICK_H */
