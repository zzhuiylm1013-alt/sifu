#include "main.h"
#include "usart.h"
#include "gpio.h"
#include "config.h"
#include "uart_handler.h"
#include "timer.h"
#include "motion.h"
#include "servo.h"
#include "protocol.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart1;

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

    MX_GPIO_Init();
    Motion_Init(); Protocol_Init(); UART_Handler_Init();
    Servo_Init(); Timer_Init();
    HAL_NVIC_SetPriority(TIM2_IRQn, 0, 0); HAL_NVIC_EnableIRQ(TIM2_IRQn);

    while (1) {
        if (UART_Handler_HasCommand()) Protocol_Parse(UART_Handler_GetCommand());
        if (Protocol_HasResponse()) {
            char *rsp = (char *)Protocol_GetResponse();
            HAL_UART_Transmit(&huart1, (uint8_t *)rsp, strlen(rsp), 100);
        }
        Motion_Update();
        if (Motion_MoveComplete()) {
            char buf[32];
            int len = snprintf(buf, sizeof(buf), "POS X=%.2f Y=%.2f\n", Motion_GetX_mm(), Motion_GetY_mm());
            HAL_UART_Transmit(&huart1, (uint8_t *)buf, len, 100);
        }
        HAL_Delay(200);
        HAL_UART_Transmit(&huart1, (uint8_t *)"OK\n", 3, 100);
    }
}
