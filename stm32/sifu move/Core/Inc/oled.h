#ifndef __OLED_H
#define __OLED_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"

void OLED_Init(void);
void OLED_Clear(void);
void OLED_ShowString(uint8_t x, uint8_t y, const char *str, uint8_t size);
void OLED_DrawTitle(const char *title);
void OLED_Update(float x_mm, float y_mm, const char *status, float speed);
void OLED_SetCursor(uint8_t x, uint8_t y);
void OLED_Refresh(void);

#ifdef __cplusplus
}
#endif

#endif /* __OLED_H */
