#include "sys_tick.h"

static volatile uint32_t sys_tick_ms = 0;

void SysTick_Setup(void)
{
    SysTick_Config(SYSTEM_CLK / 1000);
}

uint32_t SysTick_GetMs(void)
{
    return sys_tick_ms;
}

uint8_t SysTick_CheckElapsed(uint32_t *last, uint32_t interval)
{
    uint32_t now = sys_tick_ms;
    if ((now - *last) >= interval) {
        *last = now;
        return 1;
    }
    return 0;
}

void SysTick_ISR(void)
{
    sys_tick_ms++;
}
