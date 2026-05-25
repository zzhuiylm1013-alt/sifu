#include "main.h"
#include "usart.h"
#include "config.h"
#include "timer.h"
#include "uart_handler.h"
#include "motion.h"
#include "sys_tick.h"

extern TIM_HandleTypeDef htim2;

void NMI_Handler(void) {}
void HardFault_Handler(void) { __disable_irq(); while(1); }
void MemManage_Handler(void) { __disable_irq(); while(1); }
void BusFault_Handler(void) { __disable_irq(); while(1); }
void UsageFault_Handler(void) { __disable_irq(); while(1); }
void SVC_Handler(void) {}
void DebugMon_Handler(void) {}
void PendSV_Handler(void) {}

void SysTick_Handler(void)
{
  HAL_IncTick();
  SysTick_ISR();
}

/* USART1接收中断: 读DR → 入环形缓冲 → UART_Handler_RxISR处理 */
void USART1_IRQHandler(void)
{
    if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE)) {
        uint8_t byte = (uint8_t)(huart1.Instance->DR & 0xFF);
        UART_Handler_RxISR(byte);
    }
}

/* TIM2更新中断: 每脉冲触发一次,调用运动ISR(Bresenham+梯形调速) */
void TIM2_IRQHandler(void)
{
    if (__HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE)) {
        __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
        Motion_TimerISR();
    }
}
