#include "uart_handler.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

extern UART_HandleTypeDef huart1;

/* 环形接收缓冲: ISR写→head++; \n触发→拷入cmd_buffer→置cmd_ready */
static char rx_buffer[RX_BUFFER_SIZE];
static volatile uint16_t rx_head = 0;
static volatile uint16_t rx_tail = 0;
static char cmd_buffer[RX_BUFFER_SIZE];
static volatile uint8_t cmd_ready = 0;

void UART_Handler_Init(void)
{
    rx_head = 0;
    rx_tail = 0;
    cmd_ready = 0;
    memset(rx_buffer, 0, sizeof(rx_buffer));
    memset(cmd_buffer, 0, sizeof(cmd_buffer));
}

void UART_Handler_StartRx(void)
{
    /* RXNE interrupt already enabled in MX_USART1_UART_Init.
       Bytes are captured in USART1_IRQHandler via direct register read.
       No HAL receive IT needed. */
}

void UART_Handler_RxISR(uint8_t byte)
{
    uint16_t next = (rx_head + 1) % RX_BUFFER_SIZE;
    if (next != rx_tail) {
        rx_buffer[rx_head] = byte;
        rx_head = next;
        if (byte == '\n') {
            uint16_t i = 0;
            while (rx_tail != rx_head && i < RX_BUFFER_SIZE - 1) {
                char c = rx_buffer[rx_tail];
                rx_tail = (rx_tail + 1) % RX_BUFFER_SIZE;
                cmd_buffer[i++] = c;
                if (c == '\n') break;
            }
            cmd_buffer[i] = '\0';
            cmd_ready = 1;
        }
    }
}

uint8_t UART_Handler_HasCommand(void)
{
    return cmd_ready;
}

char* UART_Handler_GetCommand(void)
{
    cmd_ready = 0;
    return cmd_buffer;
}

void UART_Handler_Send(const char *str)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)str, strlen(str), 100);
}

void UART_Handler_Sendf(const char *fmt, ...)
{
    char buf[128];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    UART_Handler_Send(buf);
}
