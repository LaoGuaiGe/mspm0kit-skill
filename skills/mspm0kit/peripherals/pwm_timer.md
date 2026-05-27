# PWM / Timer on Tianqiaoxing G3519

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `timg_32bit_timer_mode_pwm_edge_sleep` | 32-bit PWM edge-aligned with sleep |
| `tima_timer_mode_periodic_repeat_count` | Periodic timer with repeat count |
| `timg_qei_mode` | Quadrature encoder (QEI) |

## Pin Mapping (LP → Tianqiaoxing)

SDK uses TIMG12 on PB6(C0)/PB7(C1).
Tianqiaoxing: PB6/PB7 occupied by SPI Flash → use TIMG0 or TIMG2 on free pins.

## Available Timer Instances

| Timer | Status | Tianqiaoxing Usage |
|-------|--------|--------------------|
| TIMA0 | Free | System tick, PWM, capture |
| TIMA1 | CC0 used | CC0 = WS2812 on PB26 |
| TIMG0 | Free | General PWM |
| TIMG6 | CC1 used | CCP1 = Buzzer on PB27 |
| TIMG8 | QEI used | PA29/PA30 encoder (optional) |
| TIMG12 | Free | General PWM (on free pins) |

## PWM Config Pattern (edge-aligned, 1 kHz on free pin)

```
PWM instance: TIMG0
Pin: PA3 (or any free pin)
Prescale: 80 (80 MHz / 80 = 1 MHz)
Period: 1000 (1 kHz)
Duty: 50%
```

## Generated Macros (example)

```
PWM_0_INST       → TIMG0
PWM_0_INST_CLK_FREQ → 1000000
GPIO_PWM_0_C0_IDX  → DL_TIMER_CC_0_INDEX
```
