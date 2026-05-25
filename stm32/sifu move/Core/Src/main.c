#include "main.h"
#include "usart.h"
#include "gpio.h"
#include "i2c.h"
#include "config.h"
#include "uart_handler.h"
#include "motion.h"
#include "protocol.h"
#include "servo.h"
#include "timer.h"
#include "oled.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart1;

/* HSE 8MHz ×9 → 72MHz SYSCLK, APB1=/2(36MHz), APB2=/1(72MHz) */
void SystemClock_Config(void) {
    RCC_OscInitTypeDef o = {0}; RCC_ClkInitTypeDef c = {0};
    o.OscillatorType = RCC_OSCILLATORTYPE_HSE; o.HSEState = RCC_HSE_ON;
    o.PLL.PLLState = RCC_PLL_ON; o.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    o.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&o) != HAL_OK) Error_Handler();
    c.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
    c.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK; c.AHBCLKDivider = RCC_SYSCLK_DIV1;
    c.APB1CLKDivider = RCC_HCLK_DIV2; c.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&c, FLASH_LATENCY_2) != HAL_OK) Error_Handler();
}
void Error_Handler(void) { __disable_irq(); while(1); }

int main(void) {
    HAL_Init(); SystemClock_Config();

    /* ── USART1 初始化: PA9/PA10, 115200, 中断接收 ── */
    __HAL_RCC_USART1_CLK_ENABLE(); __HAL_RCC_GPIOA_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_9; g.Mode = GPIO_MODE_AF_PP; g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_10; g.Mode = GPIO_MODE_INPUT; g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200; huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1; huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX; huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart1);
    __HAL_UART_ENABLE_IT(&huart1, UART_IT_RXNE);
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0); HAL_NVIC_EnableIRQ(USART1_IRQn);

    HAL_UART_Transmit(&huart1, (uint8_t *)"READY\n", 6, 100);

    /* ── 外设和模块初始化 ── */
    MX_GPIO_Init();           /* GPIO引脚 */
    MX_I2C1_Init();           /* I2C1: OLED + 24C02 */
    Motion_Init(); Protocol_Init(); UART_Handler_Init();
    Servo_Init(); Timer_Init();
    HAL_NVIC_SetPriority(TIM2_IRQn, 0, 0); HAL_NVIC_EnableIRQ(TIM2_IRQn); /* TIM2最高优先级 */

    OLED_Init();
    OLED_DrawTitle("XY Table Controller");

    /* ── 主循环 ── */
    while (1) {
        /* 1. 串口命令解析 */
        if (UART_Handler_HasCommand()) Protocol_Parse(UART_Handler_GetCommand());
        /* 2. 协议响应发送 */
        if (Protocol_HasResponse()) {
            char *rsp = (char *)Protocol_GetResponse();
            HAL_UART_Transmit(&huart1, (uint8_t *)rsp, strlen(rsp), 100);
        }
        Motion_Update();
        /* 3. 归零流程(轮询ALM信号) */
        if (Servo_IsHoming()) {
            if (Servo_Home_Update()) {
                HAL_UART_Transmit(&huart1, (uint8_t *)"HOME DONE\n", 10, 100);
            }
        }
        /* 4. 运动完成 → 上报位置 */
        if (Motion_MoveComplete()) {
            char buf[64];
            int len = snprintf(buf, sizeof(buf), "POS X=%.2f Y=%.2f\n",
                               Motion_GetX_mm(), Motion_GetY_mm());
            HAL_UART_Transmit(&huart1, (uint8_t *)buf, len, 100);
        }
        /* 5. OLED刷新 + 心跳 */
        OLED_Update(Motion_GetX_mm(), Motion_GetY_mm(),
                    Motion_GetStateStr(), Motion_GetCurrentSpeed());
        HAL_Delay(200);
        HAL_UART_Transmit(&huart1, (uint8_t *)"OK\n", 3, 100);
    }
}
