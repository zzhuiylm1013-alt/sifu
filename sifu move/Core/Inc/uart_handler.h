#ifndef __UART_HANDLER_H
#define __UART_HANDLER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

void UART_Handler_Init(void);
void UART_Handler_StartRx(void);
void UART_Handler_RxISR(uint8_t byte);
uint8_t UART_Handler_HasCommand(void);
char* UART_Handler_GetCommand(void);
void UART_Handler_Send(const char *str);
void UART_Handler_Sendf(const char *fmt, ...);

#ifdef __cplusplus
}
#endif

#endif /* __UART_HANDLER_H */
