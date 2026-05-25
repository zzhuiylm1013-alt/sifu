#include "motion.h"
#include "timer.h"
#include <stdlib.h>

/* 梯形加减速状态: 空闲→加速→匀速→减速→完成 */
typedef enum {
    PHASE_IDLE = 0,
    PHASE_ACCEL,
    PHASE_CRUISE,
    PHASE_DECEL,
    PHASE_DONE
} MovePhase_t;

static struct {
    int32_t x_pos, y_pos;
    int32_t x_target, y_target;
    int32_t dx, dy;
    int32_t dominant;
    uint8_t dom_is_x;
    int32_t accum;
    int32_t dom_done, sub_done;

    float target_speed_mm;

    uint32_t accel_steps;
    uint32_t cruise_steps;
    uint32_t decel_start;
    uint32_t total_steps;
    uint32_t step_n;
    uint32_t accel_n;

    float current_speed;       /* 当前速度 steps/s */
    float speed_inc;           /* 每步速度增量 */

    uint8_t dir_x, dir_y;
    uint8_t move_done_flag;

    MovePhase_t phase;
    MotionState_t state;
} mot;

#define V_MIN_STEPS  ((float)MIN_STEPS_PER_SEC)

void Motion_Init(void)
{
    mot.x_pos = 0;
    mot.y_pos = 0;
    mot.x_target = 0;
    mot.y_target = 0;
    mot.state = MOTION_IDLE;
    mot.phase = PHASE_IDLE;
    mot.move_done_flag = 0;
}

/* 规划并启动一次移动: 计算步数/方向/Bresenham/梯形曲线, 启动TIM2中断 */
static void start_move(float x_mm, float y_mm, float speed_mm_min)
{
    /* mm → steps (1μm/pulse) */
    mot.x_target = (int32_t)(x_mm * 1000.0f);
    mot.y_target = (int32_t)(y_mm * 1000.0f);

    if (mot.x_target < 0) mot.x_target = 0;
    if (mot.y_target < 0) mot.y_target = 0;
    if (mot.x_target > (int32_t)(X_MAX_TRAVEL_MM * 1000.0f)) mot.x_target = (int32_t)(X_MAX_TRAVEL_MM * 1000.0f);
    if (mot.y_target > (int32_t)(Y_MAX_TRAVEL_MM * 1000.0f)) mot.y_target = (int32_t)(Y_MAX_TRAVEL_MM * 1000.0f);

    mot.dx = abs(mot.x_target - mot.x_pos);
    mot.dy = abs(mot.y_target - mot.y_pos);

    if (mot.dx == 0 && mot.dy == 0) {
        mot.move_done_flag = 1;
        mot.state = MOTION_IDLE;
        mot.phase = PHASE_IDLE;
        return;
    }

    mot.dir_x = (mot.x_target >= mot.x_pos) ? 1 : 0;
    mot.dir_y = (mot.y_target >= mot.y_pos) ? 1 : 0;

    if (mot.dx >= mot.dy) {
        mot.dominant = mot.dx;
        mot.dom_is_x = 1;
    } else {
        mot.dominant = mot.dy;
        mot.dom_is_x = 0;
    }

    mot.accum = 0;
    mot.dom_done = 0;
    mot.sub_done = 0;
    mot.step_n = 0;
    mot.accel_n = 0;

    /* Clamp target speed */
    if (speed_mm_min < MIN_SPEED_MM_MIN) speed_mm_min = MIN_SPEED_MM_MIN;
    if (speed_mm_min > MAX_SPEED_MM_MIN) speed_mm_min = MAX_SPEED_MM_MIN;
    mot.target_speed_mm = speed_mm_min;

    float target_steps = speed_mm_min / 60.0f * 1000.0f;

    /* a: mm/s² → steps/s² (×1000) */
    float a_steps = DEFAULT_ACCEL * 1000.0f;
    mot.accel_steps = (uint32_t)((target_steps * target_steps - V_MIN_STEPS * V_MIN_STEPS)
                                 / (2.0f * a_steps));

    if (mot.accel_steps < 1) mot.accel_steps = 1;

    /* Check for triangular profile */
    if (mot.accel_steps * 2 > (uint32_t)mot.dominant) {
        mot.accel_steps = mot.dominant / 2;
        if (mot.accel_steps < 1) mot.accel_steps = 1;
        mot.cruise_steps = 0;
        mot.decel_start = mot.accel_steps;
    } else {
        mot.cruise_steps = mot.dominant - mot.accel_steps * 2;
        mot.decel_start = mot.accel_steps + mot.cruise_steps;
    }

    mot.total_steps = mot.dominant;
    mot.speed_inc = (target_steps - V_MIN_STEPS) / (float)mot.accel_steps;
    mot.current_speed = V_MIN_STEPS;
    mot.phase = PHASE_ACCEL;

    /* Set direction pins */
    if (mot.dir_x) X_DIR_HIGH(); else X_DIR_LOW();
    if (mot.dir_y) Y_DIR_HIGH(); else Y_DIR_LOW();

    /* Set initial ARR and CCRs */
    uint32_t arr = (uint32_t)((float)TIMER_TICK_HZ / V_MIN_STEPS) - 1;
    Timer_SetARR(arr);
    if (mot.dom_is_x) {
        Timer_SetCCR_Dom(arr / 2);   /* TIM2 = X dominant, always pulse */
        Timer_SetCCR_Sub(0);         /* TIM3 = Y subordinate, gated */
    } else {
        Timer_SetCCR_Dom(0);         /* TIM2 = X subordinate, gated */
        Timer_SetCCR_Sub(arr / 2);   /* TIM3 = Y dominant, always pulse */
    }

    mot.move_done_flag = 0;
    mot.state = MOTION_RUNNING;

    Timer_Start();
}

void Motion_LinearMove(float x_mm, float y_mm, float speed_mm_min)
{
    if (mot.state == MOTION_ESTOP) return;
    if (mot.state == MOTION_RUNNING) return;
    start_move(x_mm, y_mm, speed_mm_min);
}

void Motion_RapidMove(float x_mm, float y_mm)
{
    Motion_LinearMove(x_mm, y_mm, MAX_SPEED_MM_MIN);
}

void Motion_Jog(char axis, int8_t dir, float step_mm)
{
    if (mot.state == MOTION_RUNNING || mot.state == MOTION_ESTOP) return;

    float x_mm = Motion_GetX_mm();
    float y_mm = Motion_GetY_mm();

    if (axis == 'X') {
        x_mm = (dir > 0) ? x_mm + step_mm : x_mm - step_mm;
    } else if (axis == 'Y') {
        y_mm = (dir > 0) ? y_mm + step_mm : y_mm - step_mm;
    }

    if (x_mm < 0) x_mm = 0;
    if (y_mm < 0) y_mm = 0;
    if (x_mm > X_MAX_TRAVEL_MM) x_mm = X_MAX_TRAVEL_MM;
    if (y_mm > Y_MAX_TRAVEL_MM) y_mm = Y_MAX_TRAVEL_MM;

    start_move(x_mm, y_mm, 2000.0f);
}

void Motion_EmergencyStop(void)
{
    Timer_Stop();
    mot.state = MOTION_ESTOP;
    mot.phase = PHASE_IDLE;
    mot.move_done_flag = 1;
}

void Motion_ClearEstop(void)
{
    if (mot.state == MOTION_ESTOP) {
        mot.state = MOTION_IDLE;
        mot.phase = PHASE_IDLE;
    }
}

void Motion_SetPosition(float x_mm, float y_mm)
{
    mot.x_pos = (int32_t)(x_mm * 1000.0f);
    mot.y_pos = (int32_t)(y_mm * 1000.0f);
    mot.x_target = mot.x_pos;
    mot.y_target = mot.y_pos;
}

void Motion_Update(void)
{
    /* Main loop hook: nothing needed, ISR-driven */
}

/* 脉冲ISR — 运动核心,每步触发: ①统计已走步数 → ②梯形调速 → ③Bresenham判从轴 → ④检测结束 */
void Motion_TimerISR(void)
{
    if (mot.state != MOTION_RUNNING) return;
    if (mot.phase == PHASE_IDLE || mot.phase == PHASE_DONE) return;

    uint32_t arr = Timer_GetARR();

    /* ① 统计上周期完成的脉冲: 主轴必走, 从轴看CCR是否>0 */
    mot.step_n++;
    if (mot.dom_is_x) {
        mot.dom_done++;
        mot.x_pos += mot.dir_x ? 1 : -1;
        /* Read TIM3 CCR from previous cycle: >0 means Y also stepped */
        if (TIM3->CCR1 > 0) {
            mot.sub_done++;
            mot.y_pos += mot.dir_y ? 1 : -1;
        }
    } else {
        mot.dom_done++;
        mot.y_pos += mot.dir_y ? 1 : -1;
        /* Read TIM2 CCR from previous cycle: >0 means X also stepped */
        if (TIM2->CCR1 > 0) {
            mot.sub_done++;
            mot.x_pos += mot.dir_x ? 1 : -1;
        }
    }

    /* ② 线性速度斜坡: 每步 current_speed += speed_inc, ARR = 1MHz/speed - 1 */
    if (mot.phase == PHASE_ACCEL) {
        if (mot.step_n < mot.accel_steps) {
            mot.current_speed += mot.speed_inc;
            arr = (uint32_t)((float)TIMER_TICK_HZ / mot.current_speed) - 1;
            if (arr < 11) arr = 11;
            Timer_SetARR(arr);
        } else {
            mot.phase = (mot.cruise_steps > 0) ? PHASE_CRUISE : PHASE_DECEL;
            if (mot.phase == PHASE_DECEL) mot.accel_n = mot.accel_steps;
            float tgt = mot.target_speed_mm / 60.0f * 1000.0f;
            mot.current_speed = tgt;
            arr = (uint32_t)((float)TIMER_TICK_HZ / tgt) - 1;
            Timer_SetARR(arr);
        }
    } else if (mot.phase == PHASE_CRUISE) {
        if (mot.step_n >= mot.decel_start) {
            mot.phase = PHASE_DECEL;
            mot.accel_n = mot.accel_steps;
        }
    } else if (mot.phase == PHASE_DECEL) {
        if (mot.current_speed > V_MIN_STEPS + mot.speed_inc) {
            mot.current_speed -= mot.speed_inc;
            arr = (uint32_t)((float)TIMER_TICK_HZ / mot.current_speed) - 1;
            uint32_t max_arr = (TIMER_TICK_HZ / MIN_STEPS_PER_SEC) - 1;
            if (arr > max_arr) arr = max_arr;
            Timer_SetARR(arr);
        }
    }

    /* ③ Bresenham: 主轴CCR=ARR/2(必发), 从轴accum>=dominant时CCR=ARR/2(发)否则0(不发) */
    uint16_t half_arr = (uint16_t)(arr / 2);
    if (mot.dom_is_x) {
        Timer_SetCCR_Dom(half_arr);     /* X always pulses */
        mot.accum += (int32_t)mot.dy;
        if (mot.accum >= (int32_t)mot.dominant) {
            mot.accum -= (int32_t)mot.dominant;
            Timer_SetCCR_Sub(half_arr); /* Y pulses */
        } else {
            Timer_SetCCR_Sub(0);        /* Y no pulse */
        }
    } else {
        Timer_SetCCR_Sub(half_arr);     /* Y always pulses */
        mot.accum += (int32_t)mot.dx;
        if (mot.accum >= (int32_t)mot.dominant) {
            mot.accum -= (int32_t)mot.dominant;
            Timer_SetCCR_Dom(half_arr); /* X pulses */
        } else {
            Timer_SetCCR_Dom(0);        /* X no pulse */
        }
    }

    /* ④ 主轴步数走完 → 停定时器, 置完成标志 */
    if (mot.dom_done >= (int32_t)mot.total_steps) {
        Timer_Stop();
        mot.state = MOTION_IDLE;
        mot.phase = PHASE_IDLE;
        mot.move_done_flag = 1;
        mot.x_pos = mot.x_target;
        mot.y_pos = mot.y_target;
    }
}

int32_t Motion_GetXSteps(void)  { return mot.x_pos; }
int32_t Motion_GetYSteps(void)  { return mot.y_pos; }

float Motion_GetX_mm(void) { return (float)mot.x_pos / 1000.0f; }
float Motion_GetY_mm(void) { return (float)mot.y_pos / 1000.0f; }

uint8_t Motion_MoveComplete(void)
{
    if (mot.move_done_flag) {
        mot.move_done_flag = 0;
        return 1;
    }
    return 0;
}

MotionState_t Motion_GetState(void) { return mot.state; }

const char* Motion_GetStateStr(void)
{
    switch (mot.state) {
        case MOTION_IDLE:    return "READY";
        case MOTION_RUNNING: return "MOVING";
        case MOTION_ESTOP:   return "ALARM";
        default:             return "UNKNOWN";
    }
}

float Motion_GetCurrentSpeed(void) { return mot.target_speed_mm; }

uint8_t Motion_IsRunning(void)
{
    return (mot.state == MOTION_RUNNING);
}
