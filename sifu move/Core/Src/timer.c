#include "timer.h"

TIM_HandleTypeDef htim2 = {0};   /* X轴脉冲定时器 */
TIM_HandleTypeDef htim3 = {0};   /* Y轴脉冲定时器 */

static uint8_t timer_running = 0;

/* TIM2/TIM3 初始化为 PWM Mode1, 72MHz/72=1MHz滴答, 预装载使能 */
void Timer_Init(void)
{
    TIM_OC_InitTypeDef sConfigOC = {0};

    __HAL_RCC_TIM2_CLK_ENABLE();
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = TIMER_PRESCALER;       /* 72分频 → 1MHz */
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = 1199;                     /* 初始频率 ~833Hz */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE; /* ARR缓冲 */
    HAL_TIM_PWM_Init(&htim2);

    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = 600;                        /* 50%占空比 */
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1);

    __HAL_RCC_TIM3_CLK_ENABLE();
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = TIMER_PRESCALER;
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = 1199;
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);

    sConfigOC.Pulse = 600;
    HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_1);
}

/* 启动PWM输出 + TIM2更新中断 (归零后脉冲引脚被切为GPIO,这里恢复AF) */
void Timer_Start(void)
{
    if (!timer_running) {
        GPIO_InitTypeDef GPIO_InitStruct = {0};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
        GPIO_InitStruct.Pin = X_PULSE_PIN;
        HAL_GPIO_Init(X_PULSE_PORT, &GPIO_InitStruct);
        GPIO_InitStruct.Pin = Y_PULSE_PIN;
        HAL_GPIO_Init(Y_PULSE_PORT, &GPIO_InitStruct);

        __HAL_TIM_ENABLE_IT(&htim2, TIM_IT_UPDATE);
        HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
        HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
        timer_running = 1;
    }
}

/* 停止脉冲: 关中断 → 停PWM → 止输出 */
void Timer_Stop(void)
{
    __HAL_TIM_DISABLE_IT(&htim2, TIM_IT_UPDATE);
    HAL_TIM_PWM_Stop(&htim2, TIM_CHANNEL_1);
    HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_1);
    timer_running = 0;
}

/* 设置脉冲频率: ARR = 1MHz/freq - 1, 范围10~99999 */
void Timer_SetARR(uint32_t arr)
{
    if (arr < 10) arr = 10;
    if (arr > 99999) arr = 99999;
    __HAL_TIM_SET_AUTORELOAD(&htim2, arr);
    __HAL_TIM_SET_AUTORELOAD(&htim3, arr);
}

/* 从轴CCR: >0=发脉冲, =0=不发 (Bresenham门控) */
void Timer_SetCCR_Sub(uint16_t ccr) { __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, ccr); }

/* 主轴CCR: ARR/2=50%占空比脉冲 */
void Timer_SetCCR_Dom(uint16_t ccr) { __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, ccr); }

uint32_t Timer_GetARR(void) { return __HAL_TIM_GET_AUTORELOAD(&htim2); }
