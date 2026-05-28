#ifndef HW_ENCODER_STUB_H
#define HW_ENCODER_STUB_H
#include "stdint.h"
void HW_Encoder_Init(void) {}
void HW_Encoder_Enable(void) {}
void HW_Encoder_Disable(void) {}
int16_t HW_Encoder_GetDelta(void){ return 0; }
#endif
