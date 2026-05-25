#ifndef __CONFIG_H
#define __CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f1xx_hal.h"

/* ── 滑台参数 (GTTHS5-L10-700-BC-H10-C4) ── */
#define LEAD_MM             10.0f
#define ENCODER_RES         10000
#define PULSE_PER_MM        1000.0f
#define GEAR_NUMERATOR      1
#define GEAR_DENOMINATOR    1
#define X_MAX_TRAVEL_MM     700.0f
#define Y_MAX_TRAVEL_MM     700.0f

/* ── 引脚定义 ── */
/* X轴: TIM2_CH1 脉冲, 方向, 使能, 报警, 限位(预留) */
#define X_PULSE_PORT        GPIOA
#define X_PULSE_PIN         GPIO_PIN_15   /* PA15 X轴脉冲 */
#define X_DIR_PORT          GPIOC
#define X_DIR_PIN           GPIO_PIN_13   /* PC13 X轴方向 */
#define X_SON_PORT          GPIOE
#define X_SON_PIN           GPIO_PIN_0    /* PE0  X轴伺服使能 */
#define X_ALM_PORT          GPIOE
#define X_ALM_PIN           GPIO_PIN_1    /* PE1  X轴报警输入(低有效) */
#define X_HOME_PORT         GPIOE
#define X_HOME_PIN          GPIO_PIN_2    /* PE2  X轴限位(预留,不用) */

/* Y轴: TIM3_CH1 脉冲, 方向, 使能, 报警, 限位(预留) */
#define Y_PULSE_PORT        GPIOA
#define Y_PULSE_PIN         GPIO_PIN_6    /* PA6  Y轴脉冲 */
#define Y_DIR_PORT          GPIOA
#define Y_DIR_PIN           GPIO_PIN_7    /* PA7  Y轴方向 */
#define Y_SON_PORT          GPIOA
#define Y_SON_PIN           GPIO_PIN_5    /* PA5  Y轴伺服使能 */
#define Y_ALM_PORT          GPIOA
#define Y_ALM_PIN           GPIO_PIN_1    /* PA1  Y轴报警输入(低有效) */
#define Y_HOME_PORT         GPIOF
#define Y_HOME_PIN          GPIO_PIN_0    /* PF0  Y轴限位(预留,不用) */

/* UART1: CH340 USB转串口 */
#define UART_TX_PORT        GPIOA
#define UART_TX_PIN         GPIO_PIN_9    /* PA9  USART1_TX */
#define UART_RX_PORT        GPIOA
#define UART_RX_PIN         GPIO_PIN_10   /* PA10 USART1_RX */

/* I2C1: OLED(0x3C) + 板载24C02(0x50) 共用总线 */
#define I2C_SCL_PORT        GPIOB
#define I2C_SCL_PIN         GPIO_PIN_6    /* PB6  I2C1_SCL */
#define I2C_SDA_PORT        GPIOB
#define I2C_SDA_PIN         GPIO_PIN_7    /* PB7  I2C1_SDA */
#define OLED_ADDR           0x3C
#define EEPROM_ADDR         0x50

/* ── 引脚读写宏 ── */
#define X_DIR_HIGH()        HAL_GPIO_WritePin(X_DIR_PORT, X_DIR_PIN, GPIO_PIN_SET)
#define X_DIR_LOW()         HAL_GPIO_WritePin(X_DIR_PORT, X_DIR_PIN, GPIO_PIN_RESET)
#define Y_DIR_HIGH()        HAL_GPIO_WritePin(Y_DIR_PORT, Y_DIR_PIN, GPIO_PIN_SET)
#define Y_DIR_LOW()         HAL_GPIO_WritePin(Y_DIR_PORT, Y_DIR_PIN, GPIO_PIN_RESET)

#define X_SON_ON()          HAL_GPIO_WritePin(X_SON_PORT, X_SON_PIN, GPIO_PIN_SET)
#define X_SON_OFF()         HAL_GPIO_WritePin(X_SON_PORT, X_SON_PIN, GPIO_PIN_RESET)
#define Y_SON_ON()          HAL_GPIO_WritePin(Y_SON_PORT, Y_SON_PIN, GPIO_PIN_SET)
#define Y_SON_OFF()         HAL_GPIO_WritePin(Y_SON_PORT, Y_SON_PIN, GPIO_PIN_RESET)

#define X_ALM_READ()        (HAL_GPIO_ReadPin(X_ALM_PORT, X_ALM_PIN) == GPIO_PIN_RESET)
#define Y_ALM_READ()        (HAL_GPIO_ReadPin(Y_ALM_PORT, Y_ALM_PIN) == GPIO_PIN_RESET)
#define X_HOME_READ()       (HAL_GPIO_ReadPin(X_HOME_PORT, X_HOME_PIN) == GPIO_PIN_RESET)
#define Y_HOME_READ()       (HAL_GPIO_ReadPin(Y_HOME_PORT, Y_HOME_PIN) == GPIO_PIN_RESET)

/* ── 系统时钟: 72MHz, 定时器1MHz(72分频) ── */
#define SYSTEM_CLK          72000000UL
#define TIMER_PRESCALER     71          /* 72MHz/72=1MHz滴答 */
#define TIMER_TICK_HZ       1000000UL

/* ── 运动参数 ── */
#define MAX_SPEED_MM_MIN    5000.0f
#define MIN_SPEED_MM_MIN    10.0f
#define DEFAULT_ACCEL       500.0f     /* mm/s² */
#define HOME_SPEED_FAST     50.0f
#define HOME_SPEED_SLOW     10.0f

/* Derived */
#define MIN_STEPS_PER_SEC   ((uint32_t)(MIN_SPEED_MM_MIN / 60.0f * 1000.0f))
#define MAX_STEPS_PER_SEC   ((uint32_t)(MAX_SPEED_MM_MIN / 60.0f * 1000.0f))

/* ── 串口: 115200, 8N1, 256字节环形缓冲 ── */
#define UART_BAUDRATE       115200
#define RX_BUFFER_SIZE      256

/* ── OLED: 128x64, I2C 400kHz ── */
#define OLED_I2C_SPEED      400000
#define OLED_WIDTH          128
#define OLED_HEIGHT         64

/* ── 时序参数 ── */
#define SERVO_ENABLE_DELAY  200         /* 伺服使能后稳定200ms */
#define OLED_REFRESH_MS     200         /* OLED刷新间隔 */
#define POS_REPORT_MS       200         /* 位置上报间隔 */

#ifdef __cplusplus
}
#endif

#endif /* __CONFIG_H */
