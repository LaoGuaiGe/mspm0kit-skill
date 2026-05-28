# GPIO on Tianqiaoxing G3519

## SDK Example

`gpio_toggle_output` — toggles 4 pins (PB22, PB26, PB27, PB14) with delay

## Pin Mapping (LP → Tianqiaoxing)

| SDK Pin | SDK Name | Tianqiaoxing | Action |
|---------|----------|--------------|--------|
| PB22 | USER_LED_1 | PB22 (onboard LED) | Keep |
| PB26 | USER_LED_2 | PB26 (WS2812) | Remove (occupied) |
| PB27 | USER_LED_3 | PB27 (Buzzer) | Remove (occupied) |
| PB14 | USER_TEST | Free | Keep as test output |

## Recommended Pattern

```c
// LED on (active-low)
DL_GPIO_clearPins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
// LED off
DL_GPIO_setPins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
// Toggle
DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
```

## Generated Macros

```
GPIO_LEDS_PORT              → GPIOB
GPIO_LEDS_USER_LED_1_PIN    → DL_GPIO_PIN_22
```

## Free GPIO Pins (all ports)

PA3, PA4, PA7–PA9, PA12–PA17, PA21–PA26
PB0–PB5, PB10–PB16, PB19, PB20, PB24, PB25, PB28

(Excludes any pin listed as occupied in SKILL.md)

## SysConfig JS Snippet

### Output (LED, active-low)

```js
GPIO1.$name                         = "LED";
GPIO1.associatedPins[0].$name       = "LED";
GPIO1.associatedPins[0].assignedPort = "PORTB";
GPIO1.associatedPins[0].assignedPin  = "22";
GPIO1.associatedPins[0].pin.$assign  = "PB22";
```

### Input (button, pull-up)

```js
GPIO1.$name                              = "BTN";
GPIO1.associatedPins[0].$name            = "ENTER";
GPIO1.associatedPins[0].direction        = "INPUT";
GPIO1.associatedPins[0].internalResistor = "PULL_UP";
GPIO1.associatedPins[0].assignedPort     = "PORTB";
GPIO1.associatedPins[0].assignedPin      = "21";
GPIO1.associatedPins[0].pin.$assign      = "PB21";
```

### Cross-Port GPIO Instance

When one GPIO instance has pins on different ports (e.g. PA18 + PB21), each pin gets its own `_PORT` macro:
- `BTN_ENTER_PORT` → GPIOA (for PA18)
- Don't use a single `BTN_PORT` for all pins — it doesn't exist. Use `GPIOA`/`GPIOB` directly.
