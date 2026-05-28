\
#include "ti_msp_dl_config.h"
#include "OLED.h"

int main(void)
{
    SYSCFG_DL_init();

    OLED_Init();
    OLED_Clear();
    OLED_ShowString(0, 0, "TianQiaoXing", 12);
    OLED_ShowString(0, 16, "MSPM0G3519 OLED", 12);
    OLED_ShowString(0, 32, "Hello World!", 12);
    OLED_Update();

    while (1) {
        /* Your drawing code here */
    }
}