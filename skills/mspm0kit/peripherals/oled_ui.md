# OLED UI Framework on Tianqiaoxing G3519

**Source**: https://github.com/LaoGuaiGe/OLED_UI
**Local copy**: `E:\github\OLED_UI\OLED_UI_Examples\MSPM0G3519\ccs\oeldui`

## Hardware

- Display: SSD1312 128×64 monochrome OLED
- Interface: Software I2C on PA0(SDA) / PA1(SCL), 2.2kΩ pull-up on board
- Fonts: Built-in bitmap fonts (字模) in `OLED_Fonts.c/h`, no external Flash required

## Framework Layers

| Layer | Files | Responsibility |
|-------|-------|---------------|
| Driver | `OLED_driver.c/h` | Software I2C bit-bang (calls `myiic.c`) |
| Graphics | `OLED.c/h` | Point, line, rect, circle, arc, triangle, text, image, PrintfMix |
| Fonts | `OLED_Fonts.c/h` | ASCII 6x8/7x12/8x16/10x20 + Chinese 12x12/16x16/20x20 bitmaps |
| UI Engine | `OLED_UI.c/h` | Menu page system, cursor, animation, windows |
| Menu Data | `OLED_UI_MenuData.c/h` | MenuItem arrays, MenuPage definitions |
| HAL | `OLED_UI_Driver.c/h` | Delay, encoder (stub available for keyboard-less use) |

## Key Drawing APIs

```c
// Display control
void OLED_Init(void);
void OLED_Clear(void);
void OLED_Update(void);

// Graphics
void OLED_DrawPoint(uint8_t x, uint8_t y, uint8_t mode);
void OLED_DrawLine(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, uint8_t mode);
void OLED_DrawRectangle(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t mode);
void OLED_DrawCircle(uint8_t cx, uint8_t cy, uint8_t r, uint8_t mode);
void OLED_DrawTriangle(uint8_t x0,uint8_t y0,uint8_t x1,uint8_t y1,uint8_t x2,uint8_t y2,uint8_t mode);

// Text — font sizes: OLED_8x6 / OLED_12x6 / OLED_16x8 / OLED_20x10
void OLED_ShowChar(uint8_t x, uint8_t y, char ch, uint8_t fontSize);
void OLED_ShowString(uint8_t x, uint8_t y, const char *str, uint8_t fontSize);
// Mixed CJK+ASCII: UTF-8 mode (OLED_CHN_CHAR_WIDTH=3)
void OLED_PrintfMix(uint8_t x, uint8_t y, const char *fmt, uint8_t fontSize, ...);

// Images (bitmap from OLED_Fonts or user-defined)
void OLED_ShowImage(uint8_t x, uint8_t y, uint8_t w, uint8_t h, const uint8_t *img);
```

## Menu System

```c
// MenuItem — one entry in a menu
typedef struct {
    char *General_item_text;
    void (*General_callback)(void);
    MenuPage *General_SubMenuPage;
    bool *List_BoolRadioBox;
    const uint8_t *Tiles_Icon;  // for TILES menu type
} MenuItem;

// MenuPage — one screen
typedef struct {
    MenuType  General_MenuType;         // MENU_TYPE_LIST / MENU_TYPE_TILES / etc.
    CursorType General_CursorStyle;     // REVERSE_ROUNDRECTANGLE / etc.
    UI_FontSize General_FontSize;       // OLED_UI_FONT_8/12/16/20
    MenuPage *General_ParentMenuPage;
    uint8_t General_LineSpace;
    MoveStyle General_MoveStyle;        // UNLINEAR / PID_CURVE
    uint8_t General_MovingSpeed;
    void (*General_ShowAuxiliaryFunction)(void);
    MenuItem *General_MenuItems;        // array, last item has .General_item_text = NULL
    // ... type-specific fields (List_*, Tiles_*)
} MenuPage;

// Lifecycle
void OLED_UI_Init(MenuPage *rootPage);
void OLED_UI_MainLoop(void);       // call in while(1)
void OLED_UI_Back(void);           // navigate back
void OLED_UI_CreateWindow(MenuWindow *win);
```

## Minimal Example

```c
#include "OLED_UI.h"
extern MenuPage MainMenuPage;

int main(void) {
    SYSCFG_DL_init();
    OLED_Init();
    OLED_UI_Init(&MainMenuPage);
    while (1) { OLED_UI_MainLoop(); }
}
```

See `oledUI/OLED_UI_MenuData.c` in the generated project for how to define menu items and pages.

## Scaffold

When user asks "移植屏幕UI" / "add OLED UI":

```
python scripts/scaffold_oled.py <project_name>
```

This copies only the UI framework (oledUI/ + minimal hardware deps), NOT games, IMU, wireless, or WS2812.

## Encoder Support

The generated project includes `hardware/hw_encoder_stub.h` with empty stubs. To add real encoder (PA29/PA30 QEI), replace stubs with real driver from `hardware/hw_encoder_qei.c` in the full OLED_UI repo.
