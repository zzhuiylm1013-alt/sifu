#ifndef __PROTOCOL_H
#define __PROTOCOL_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

void Protocol_Init(void);
void Protocol_Parse(const char *cmd);
uint8_t Protocol_HasResponse(void);
const char* Protocol_GetResponse(void);

#ifdef __cplusplus
}
#endif

#endif /* __PROTOCOL_H */
