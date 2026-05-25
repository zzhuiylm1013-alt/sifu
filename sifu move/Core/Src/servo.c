#include "servo.h"
#include "motion.h"
#include "sys_tick.h"

static HomeState_t home_state = HOME_IDLE;
static uint32_t home_pulse_period_ms = 0;
static uint8_t homing_active = 0;    /* 归零中=1: 此时ALM表示撞限位, 不触发急停 */
static uint32_t home_start_ms = 0;   /* 归零起始时刻, 用于超时保护 */

void Servo_Init(void)
{
    X_SON_OFF();
    Y_SON_OFF();
    home_state = HOME_IDLE;
    homing_active = 0;
}

void Servo_Enable(void)
{
    X_SON_ON();
    Y_SON_ON();
    HAL_Delay(SERVO_ENABLE_DELAY);
}

void Servo_Disable(void)
{
    X_SON_OFF();
    Y_SON_OFF();
}

uint8_t Servo_AlarmCheck(void)
{
    if (homing_active) return 0;        /* homing ALM handled separately */
    if (X_ALM_READ()) return 1;
    if (Y_ALM_READ()) return 1;
    return 0;
}

uint8_t Servo_GetAlarmCode(void)
{
    uint8_t code = 0;
    if (X_ALM_READ()) code |= 0x01;
    if (Y_ALM_READ()) code |= 0x02;
    return code;
}

uint8_t Servo_IsHoming(void) { return homing_active; }

void Servo_Home_Abort(void)
{
    homing_active = 0;
    home_state = HOME_IDLE;
    home_start_ms = 0;

    /* 脉冲引脚从 GPIO 切回 AF (TIM PWM), 恢复可正常运动 */
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Pin = X_PULSE_PIN;
    HAL_GPIO_Init(X_PULSE_PORT, &GPIO_InitStruct);
    GPIO_InitStruct.Pin = Y_PULSE_PIN;
    HAL_GPIO_Init(Y_PULSE_PORT, &GPIO_InitStruct);
}

static void home_generate_pulse(uint8_t axis, uint8_t dir)
{
    if (axis == 0) {
        if (dir) X_DIR_HIGH(); else X_DIR_LOW();
        X_PULSE_PORT->BSRR = X_PULSE_PIN;
        for (volatile int d = 0; d < 50; d++) __NOP();
        X_PULSE_PORT->BRR = X_PULSE_PIN;
    } else {
        if (dir) Y_DIR_HIGH(); else Y_DIR_LOW();
        Y_PULSE_PORT->BSRR = Y_PULSE_PIN;
        for (volatile int d = 0; d < 50; d++) __NOP();
        Y_PULSE_PORT->BRR = Y_PULSE_PIN;
    }
}

static void home_setup_gpio(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    GPIO_InitStruct.Pin = X_PULSE_PIN;
    HAL_GPIO_Init(X_PULSE_PORT, &GPIO_InitStruct);
    GPIO_InitStruct.Pin = Y_PULSE_PIN;
    HAL_GPIO_Init(Y_PULSE_PORT, &GPIO_InitStruct);
}

void Servo_Home_Start(void)
{
    if (Motion_IsRunning()) return;
    home_setup_gpio();          /* 脉冲引脚切为GPIO输出 */
    homing_active = 1;
    home_state = HOME_X_FAST;
    home_pulse_period_ms = 1;   /* 1ms周期 ≈ 60mm/min */
    home_start_ms = SysTick_GetMs();
}

uint8_t Servo_Home_Update(void)
{
    static uint32_t last_ms = 0;
    uint32_t now = SysTick_GetMs();

    /* 30秒无ALM触发则自动中止归零 (无物理限位时避免卡死) */
    if (home_start_ms > 0 && (now - home_start_ms) > 30000) {
        Servo_Home_Abort();
        return 1;  /* 通知主循环发送 HOME DONE (实际是ABORT) */
    }

    switch (home_state) {

    /* ── X轴归零: 负向走→撞限位(ALM)→清报警→回退→设零点 ── */
    case HOME_X_FAST:
        if (X_ALM_READ()) {
            /* 撞限位 → 开关使能清伺服报警 */
            X_SON_OFF(); HAL_Delay(20); X_SON_ON();
            home_state = HOME_X_BACKOFF;
            home_pulse_period_ms = 8;   /* slower back-off */
            break;
        }
        if ((now - last_ms) >= home_pulse_period_ms) {
            last_ms = now;
            home_generate_pulse(0, 0);  /* X negative */
        }
        break;

    case HOME_X_BACKOFF:
        if ((now - last_ms) >= home_pulse_period_ms) {
            last_ms = now;
            home_generate_pulse(0, 1);  /* X positive: back off ~1mm */
            home_state = HOME_X_SETZERO;
        }
        break;

    case HOME_X_SETZERO:
        Motion_SetPosition(0.0f, Motion_GetY_mm());
        home_state = HOME_Y_FAST;
        home_pulse_period_ms = 1;
        break;

    /* ── Y轴归零: 同X ── */
    case HOME_Y_FAST:
        if (Y_ALM_READ()) {
            Y_SON_OFF(); HAL_Delay(20); Y_SON_ON();
            home_state = HOME_Y_BACKOFF;
            home_pulse_period_ms = 8;
            break;
        }
        if ((now - last_ms) >= home_pulse_period_ms) {
            last_ms = now;
            home_generate_pulse(1, 0);  /* Y negative */
        }
        break;

    case HOME_Y_BACKOFF:
        if ((now - last_ms) >= home_pulse_period_ms) {
            last_ms = now;
            home_generate_pulse(1, 1);  /* Y positive: back off ~1mm */
            home_state = HOME_Y_SETZERO;
        }
        break;

    case HOME_Y_SETZERO:
        Motion_SetPosition(0.0f, 0.0f);
        home_state = HOME_DONE;
        break;

    case HOME_DONE:
        home_state = HOME_IDLE;
        homing_active = 0;
        home_start_ms = 0;
        return 1;   /* homing complete */

    default:
        break;
    }
    return 0;
}

HomeState_t Servo_GetHomeState(void)
{
    return home_state;
}
