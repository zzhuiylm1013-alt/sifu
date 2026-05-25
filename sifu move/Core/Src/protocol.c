#include "protocol.h"
#include "motion.h"
#include "servo.h"
#include "uart_handler.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

static char response_buf[128];
static uint8_t response_ready = 0;

void Protocol_Init(void)
{
    response_ready = 0;
    response_buf[0] = '\0';
}

static void set_response(const char *rsp)
{
    strncpy(response_buf, rsp, sizeof(response_buf) - 1);
    response_buf[sizeof(response_buf) - 1] = '\0';
    response_ready = 1;
}

uint8_t Protocol_HasResponse(void)
{
    return response_ready;
}

const char* Protocol_GetResponse(void)
{
    response_ready = 0;
    return response_buf;
}

static float parse_float(const char *cmd, char key)
{
    char *p = strchr(cmd, key);
    if (!p) return 0.0f;
    return (float)atof(p + 1);
}

static int parse_dir(const char *cmd)
{
    if (strstr(cmd, "X+")) return 1;
    if (strstr(cmd, "X-")) return 2;
    if (strstr(cmd, "Y+")) return 3;
    if (strstr(cmd, "Y-")) return 4;
    return 0;
}

static float parse_step(const char *cmd)
{
    char *p = strchr(cmd, 'S');
    if (!p) return 0.0f;
    return (float)atof(p + 1);
}

/* G-code解析入口: 匹配命令字 → 调对应动作函数 */
void Protocol_Parse(const char *cmd)
{
    if (!cmd || cmd[0] == '\0') return;

    /* 去掉尾部 \r\n */
    char buf[128];
    strncpy(buf, cmd, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    for (int i = strlen(buf) - 1; i >= 0; i--) {
        if (buf[i] == '\n' || buf[i] == '\r') buf[i] = '\0';
    }

    /* G00: Rapid move */
    if (strncmp(buf, "G00", 3) == 0) {
        float x = parse_float(buf, 'X');
        float y = parse_float(buf, 'Y');
        Motion_RapidMove(x, y);
        set_response("OK\n");
        return;
    }

    /* G01: Linear move */
    if (strncmp(buf, "G01", 3) == 0) {
        float x = parse_float(buf, 'X');
        float y = parse_float(buf, 'Y');
        float f = parse_float(buf, 'F');
        if (f <= 0) f = 500.0f;
        Motion_LinearMove(x, y, f);
        set_response("OK\n");
        return;
    }

    /* G28: Home */
    if (strncmp(buf, "G28", 3) == 0) {
        Servo_Home_Start();
        set_response("OK\n");
        return;
    }

    /* G92: Set position */
    if (strncmp(buf, "G92", 3) == 0) {
        float x = parse_float(buf, 'X');
        float y = parse_float(buf, 'Y');
        Motion_SetPosition(x, y);
        set_response("OK\n");
        return;
    }

    /* M03: Servo ON */
    if (strncmp(buf, "M03", 3) == 0) {
        Servo_Enable();
        Motion_ClearEstop();
        set_response("OK\n");
        return;
    }

    /* M05: Servo OFF */
    if (strncmp(buf, "M05", 3) == 0) {
        Servo_Disable();
        set_response("OK\n");
        return;
    }

    /* M112: Emergency stop */
    if (strncmp(buf, "M112", 4) == 0) {
        Servo_Home_Abort();       /* 强行中止归零 */
        Servo_Disable();
        Motion_EmergencyStop();
        set_response("OK\n");
        return;
    }

    /* M114: Query position */
    if (strncmp(buf, "M114", 4) == 0) {
        snprintf(response_buf, sizeof(response_buf),
                 "POS X=%.2f Y=%.2f\n",
                 Motion_GetX_mm(), Motion_GetY_mm());
        response_ready = 1;
        return;
    }

    /* JOG: Jog move */
    if (strncmp(buf, "JOG", 3) == 0) {
        int d = parse_dir(buf);
        float s = parse_step(buf);
        if (s <= 0) s = 1.0f;

        char axis = 'X';
        int8_t dir = 1;
        switch (d) {
            case 1: axis = 'X'; dir =  1; break;
            case 2: axis = 'X'; dir = -1; break;
            case 3: axis = 'Y'; dir =  1; break;
            case 4: axis = 'Y'; dir = -1; break;
            default: set_response("ERR Invalid JOG direction\n"); return;
        }
        Motion_Jog(axis, dir, s);
        set_response("OK\n");
        return;
    }

    set_response("ERR Unknown command\n");
}
