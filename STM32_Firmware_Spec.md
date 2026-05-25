# STM32 XY Cross-Slide Table Firmware Specification

> STM32F103ZET6 (正点原子精英版 V2) + Nidec DA2Z123 Servo Drive (×2) + GTTHS5 Cross-Slide Table
> Goal: Control two servo motors forming an XY cross-slide table for precise point positioning

---

## 1. System Overview

```
┌─────────────┐   USB-Serial (115200)   ┌──────────────┐   Pulse/Dir (via TLP281)  ┌──────────────┐
│  PC Software │ ◄────────────────────► │  STM32F103   │ ◄───────────────────────► │ DA2Z123 × 2  │
│  (tkinter)   │   PA9(TX)/PA10(RX)    │  ZET6        │   TIM2_CH1(PA15)         │ Servo Driver  │
└─────────────┘                         │  Elite V2    │   TIM3_CH1(PA6)          │ + Motors      │
                                        │  + OLED(I2C) │                           │ + Slide Table │
                                        └──────────────┘                           └──────────────┘

Confirmed Hardware:
  - MCU: STM32F103ZET6 (正点原子精英版 V2, ATK-DNF103 V2)
  - Servo Drive: Nidec DA2Z123 (100W) ×2
  - Servo Motor: Nidec MM101N2LN07B (100W) ×2
  - Slide Table: GTTHS5-L10-700-BC-H10-C4 (导程10mm, 行程700mm, 精度C4级)
  - OLED: SSD1306 128×64 I2C (共享开发板 I2C1 总线)
```

---

## 2. Slide Table Parameters (CONFIRMED)

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | GTTHS5-L10-700-BC-H10-C4 | User confirmed |
| Screw Lead (导程) | **10 mm/rev** | L10 in model number |
| Stroke (行程) | **700 mm** | 700 in model number |
| Accuracy Grade | **C4** (±10μm per 300mm) | C4 in model number |
| DA2Z123 Encoder Resolution | **10000 pulse/rev** | Standard: 2500 lines × 4× quadrature |

### Electronic Gear Ratio (CONFIRMED)

```
Encoder resolution:  10000 pulse/rev
Screw lead:          10 mm/rev
Natural resolution:  10mm ÷ 10000 = 0.001mm/pulse = 1μm/pulse

Electronic Gear Ratio:
  No.34.0 = 1
  No.36.0 = 1
  → 1 external pulse = 1 encoder count = 1μm displacement
```

**结论：电子齿轮比 1:1，不需要缩放。天然 1μm 分辨率。**

### Pulse Frequency Requirements

| Speed (mm/min) | Pulse Rate (Hz) | STM32 Capability |
|----------------|-----------------|------------------|
| 50 (homing) | 833 | Trivial |
| 500 | 8,333 | Easy |
| 1,000 | 16,667 | Easy |
| 3,000 | 50,000 | Fine |
| 5,000 | 83,333 | Near limit |

---

## 3. STM32 Pin Assignment (CORRECTED for Elite V2)

### 3.1 Elite V2 Board IO Constraints

The Elite V2 has pre-connected peripherals. These must be respected:

| Pin | Pre-connected | Usable? |
|-----|--------------|---------|
| PA0 | KEY_UP button (pull-up to 3.3V) | Avoid for PWM output |
| PB5 | DS0 green LED | Avoid |
| PB6 | 24C02 EEPROM I2C SCL | Shared for OLED |
| PB7 | 24C02 EEPROM I2C SDA | Shared for OLED |
| PB8 | Buzzer (BEEP) | Avoid |
| PB9 | IR receiver | Avoid |
| PA9/PA10 | CH340 USB-Serial (P3 jumper) | Used for UART |
| PA13/PA14 | SWD debug | Must keep for download/debug |

### 3.2 Final Pin Assignment

```
X-Axis:
  PA15 (TIM2_CH1) → X Pulse output     (需禁用JTAG，SWD不受影响)
  PC13            → X Direction
  PE0             → X Servo ON
  PE1             → X Alarm input
  PE2             → X Home sensor

Y-Axis:
  PA6  (TIM3_CH1) → Y Pulse output     (完全空闲)
  PA7             → Y Direction         (完全空闲)
  PA5             → Y Servo ON          (完全空闲)
  PA1             → Y Alarm input       (完全空闲)
  PF0             → Y Home sensor       (完全空闲)

UART (to PC via CH340):
  PA9  (USART1_TX) → PC receive        (开发板默认连接，P3跳线)
  PA10 (USART1_RX) → PC transmit       (开发板默认连接，P3跳线)

I2C OLED (shared bus with 24C02 EEPROM):
  PB6  (I2C1_SCL)  → OLED SCL          (与24C02共用，地址不同互不冲突)
  PB7  (I2C1_SDA)  → OLED SDA          (与24C02共用)
  I2C addresses: OLED = 0x3C, 24C02 = 0x50

Power:
  开发板 3.3V     → OLED VCC
  开发板 GND       → OLED GND
  开发板 5V/USB    → 开发板供电
```

### 3.3 Pin Summary Table

| Pin | Function | Direction | Connected To | Notes |
|-----|----------|-----------|--------------|-------|
| PA15 | TIM2_CH1 | Output → | X-axis PULSE+ (via TLP281) | Must disable JTAG first |
| PC13 | GPIO OUT | Output → | X-axis SIGN+ (via TLP281) | Direction |
| PE0 | GPIO OUT | Output → | X-axis SON (via TLP281) | Servo enable |
| PE1 | GPIO IN | Input ← | X-axis ALM+ (via TLP281) | Alarm (active LOW) |
| PE2 | GPIO IN | Input ← | X-axis Home sensor | NPN NO, active LOW |
| PA6 | TIM3_CH1 | Output → | Y-axis PULSE+ (via TLP281) | Completely free |
| PA7 | GPIO OUT | Output → | Y-axis SIGN+ (via TLP281) | Completely free |
| PA5 | GPIO OUT | Output → | Y-axis SON (via TLP281) | Completely free |
| PA1 | GPIO IN | Input ← | Y-axis ALM+ (via TLP281) | Free (shared w/ ADC pad) |
| PF0 | GPIO IN | Input ← | Y-axis Home sensor | NPN NO, active LOW |
| PA9 | USART1_TX | Output → | PC (CH340 USB-Serial) | Default, P3 jumper ON |
| PA10 | USART1_RX | Input ← | PC (CH340 USB-Serial) | Default, P3 jumper ON |
| PB6 | I2C1_SCL | Output → | OLED SCL + 24C02 SCL | Shared bus, addr 0x3C/0x50 |
| PB7 | I2C1_SDA | Bidir | OLED SDA + 24C02 SDA | Shared bus |
| PA13 | SWDIO | Debug | ST-Link/DAP | Keep for programming |
| PA14 | SWCLK | Debug | ST-Link/DAP | Keep for programming |

**JTAG 关闭方法：**
```c
GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);
// 只关闭 JTAG (PA15/PB3/PB4)，保留 SWD (PA13/PA14) 用于调试下载
```

---

## 4. STM32 ↔ DA2Z123 Servo Drive Connection

### 4.1 Wiring (per axis, through TLP281 optocoupler)

```
STM32 (3.3V)         TLP281 Optocoupler            DA2Z123 CN1 (24V)
─────────────        ──────────────────            ────────────────────
PA15/PA6 ──┬──R──► Anode (pin 2)
           │        Cathode (pin 3) ──► GND_3.3V
           │        Collector (pin 8) ──► PIN 3 PULSE+
           │        Emitter (pin 7)  ──► PIN 4 PULSE- + 24V GND
           │        5V pull-up on collector side

PC13/PA7  ──┬──R──► Anode (pin 2)
           │        Cathode (pin 3) ──► GND_3.3V
           │        Collector (pin 8) ──► PIN 5 SIGN+
           │        Emitter (pin 7)  ──► PIN 6 SIGN- + 24V GND

PE0/PA5   ──┬──R──► Anode (pin 2)
           │        Cathode (pin 3) ──► GND_3.3V
           │        Collector (pin 8) ──► PIN 7 SON

PE1/PA1   ◄────────── PIN 11 ALM+ ──► Optocoupler ──► GND_3.3V
           (24V→3.3V转换，反向光耦或电阻分压)

Power:
  24V PSU + ─────────────────────────► PIN 47 +24V (both drives)
  24V PSU GND ───────────────────────► PIN 48 GND (both drives)
```

### 4.2 Required Hardware

| Item | Qty | Purpose |
|------|-----|---------|
| TLP281-4 (4-ch optocoupler) | 2 | 3.3V→24V level shift + isolation |
| 24V switching PSU | 1 | Servo control power (CN1 PIN47/48) |
| NPN proximity switch | 2 | Home sensors (axis limits) |
| IDC50 breakout board | 2 | CN1 wiring |
| Resistors (330Ω, 2.2kΩ) | some | LED current limit, pull-up |
| Jumper wires | many | Connections |

### 4.3 DA2Z123 Parameters to Set (via S-TUNE Software)

S-TUNE runs on PC, connects to DA2Z123 via USB (CN3). Set once, save to EEPROM.

| Parameter | Value | Description |
|-----------|-------|-------------|
| No.2.0 | 0 | Position control mode |
| No.3.0 | 0 | Pulse + Direction command |
| No.32.0 | 0 | Pulse+Direction, positive logic |
| No.32.3 | 0 | Positive input logic |
| No.33.0 | 0 | Input filter OFF (fastest response) |
| No.34.0 | **1** | Electronic gear numerator |
| No.36.0 | **1** | Electronic gear denominator |
| No.68.0 | 10 | Position complete range (10 pulses = 10μm) |

S-TUNE workflow:
1. Connect PC → DA2Z123 via USB cable (CN3)
2. Launch S-TUNE, set COM port, connect
3. Set above parameters in parameter screen
4. Click "Download to EEPROM" to save permanently
5. Disconnect S-TUNE, disconnect USB cable
6. Power cycle the drive → new params loaded

---

## 5. STM32 ↔ PC Software Communication

### 5.1 Serial Configuration

| Parameter | Value |
|-----------|-------|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Stop Bits | 1 |
| Parity | None |
| Flow Control | None |
| UART Peripheral | USART1 |
| Pins | PA9(TX), PA10(RX) via CH340 USB-Serial |

### 5.2 Protocol: PC → STM32 (Commands)

All commands are ASCII text terminated with `\n` (newline). Coordinates in mm, speed in mm/min.

| Command | Format | Description |
|---------|--------|-------------|
| Rapid Move | `G00 X{x} Y{y}\n` | Move to position at max speed |
| Linear Move | `G01 X{x} Y{y} F{f}\n` | Move to position at speed F |
| Home | `G28\n` | Return to home position (both axes) |
| Servo ON | `M03\n` | Enable both servos |
| Servo OFF | `M05\n` | Disable both servos |
| Emergency Stop | `M112\n` | Immediate stop all motion |
| JOG Move | `JOG {dir} {step}\n` | Jog: X+, X-, Y+, Y- by step (mm) |
| Set Position | `G92 X{x} Y{y}\n` | Set current coordinates |
| Query Position | `M114\n` | Report current position |

### 5.3 Protocol: STM32 → PC (Responses)

| Response | Format | Description |
|----------|--------|-------------|
| OK | `OK\n` | Command accepted, execution started |
| Position Report | `POS X={x} Y={y}\n` | Current position |
| Ready | `READY\n` | System initialized |
| Home Done | `HOME DONE\n` | Homing complete, position=0 |
| Alarm | `ALM {code}\n` | Servo alarm code |
| Error | `ERR {msg}\n` | Command parse error |

### 5.4 Communication Flow

```
PC                                    STM32
│                                      │
│                                      │  (boot → "READY\n")
│◄──────────── "READY\n" ─────────────│
│                                      │
│──── "M03\n" ────────────────────────►│  (enable servos)
│◄─────── "OK\n" ─────────────────────│
│                                      │
│──── "G01 X100.000 Y50.000 F500\n" ──►│  (linear move)
│◄─────── "OK\n" ─────────────────────│
│                                      │  (moving...)
│                                      │  (arrived at 100, 50)
│◄─ "POS X=100.00 Y=50.00\n" ────────│
│                                      │
│──── "G28\n" ────────────────────────►│  (home)
│◄─── "HOME DONE\n" ──────────────────│
│                                      │
│──── "M114\n" ───────────────────────►│  (query position)
│◄─ "POS X=0.00 Y=0.00\n" ───────────│
```

---

## 6. Motion Control Implementation

### 6.1 Pulse Generation

```
Timer Configuration:
  TIM2 (X-axis): PA15, remapped via AFIO
  TIM3 (Y-axis): PA6, default mapping

  Clock:       72 MHz
  Prescaler:   71 → Timer clock = 1 MHz (1μs period)
  PWM Mode:    PWM Mode 1, 50% duty cycle
  CCR Value:   ARR / 2 (50% duty, clean pulse)

Pulse Frequency → Speed Conversion:
  freq(Hz) = speed(mm/min) / 60 × 1000   (since 1 pulse = 0.001mm)
  Example: 500mm/min → 500/60×1000 = 8,333 Hz
  ARR = 1,000,000 / freq - 1
  Example: 1,000,000/8,333 - 1 = 119 → period = 120μs

  Simple formula: ARR = 60000 / speed - 1
  (where speed is in mm/min)
```

### 6.2 Bresenham 2-Axis Linear Interpolation

```
1. Compute step targets:
   target_x_steps = target_x_mm × 1000  (1 step = 1μm)
   target_y_steps = target_y_mm × 1000
   dx = |target_x_steps - current_x_steps|
   dy = |target_y_steps - current_y_steps|

2. Dominant axis = max(dx, dy)
   step_count = dominant

3. Timer ISR (fires every pulse of dominant axis):
   dominant_axis: always step (toggle pulse)
   subordinate_axis: step when accumulator >= dominant
                     (accumulator += dy each tick, -= dx when stepped)

4. Set direction GPIOs based on sign of (target - current):
   DIR = HIGH for positive, LOW for negative
```

### 6.3 Trapezoidal Acceleration/Deceleration

```
Acceleration phases per move:
  1. Accel: speed ramps from MIN_SPEED to target_speed
  2. Cruise: constant target_speed
  3. Decel: speed ramps down to MIN_SPEED

Speed profile generation:
  - Update ARR in timer ISR every N pulses to change frequency
  - Pre-calculate step count for each phase:
    accel_steps = (v² - v_min²) / (2 × accel)
    decel_steps = accel_steps (same rate)
    cruise_steps = total_steps - accel_steps - decel_steps

If total_steps < accel_steps + decel_steps:
  - Skip cruise phase
  - Peak speed will be lower than target
  - Use triangular profile instead
```

### 6.4 Homing Sequence (G28)

```
1. Set direction negative, low speed (50mm/min)
2. Move until home sensor triggers (LOW)
3. Stop, set direction positive
4. Move at 10mm/min until home sensor releases (HIGH)
5. Stop immediately, set position = 0 on both axes
6. Send "HOME DONE\n" to PC
```

### 6.5 Emergency Stop (M112)

```
1. Disable TIM2 and TIM3 immediately (stop all pulses)
2. Set X_SON and Y_SON LOW (disable servos)
3. Clear motion planner state
4. Report current position to PC
5. System enters stopped state until new valid command
```

---

## 7. OLED Display (SSD1306 128×64, Shared I2C1 Bus)

### 7.1 Connection

```
Elite V2 I2C1 bus (PB6=SCL, PB7=SDA) already has 24C02 EEPROM at 0x50.
Connect OLED in parallel — different address, no conflict.

  PB6 ──┬──► 24C02 SCL  (on-board)
        └──► OLED SCL    (external, 3.3V)

  PB7 ──┬──► 24C02 SDA  (on-board)
        └──► OLED SDA    (external, 3.3V)

  3.3V ───────► OLED VCC
  GND  ───────► OLED GND

  Addressing:
    24C02 EEPROM: 0x50 (write) / 0x51 (read)
    SSD1306 OLED:  0x3C (default, most modules)
    → No conflict as long as code uses correct address
```

### 7.2 I2C Configuration

```
I2C1: PB6(SCL), PB7(SDA)
  - Standard (no remap needed), 400kHz Fast Mode
  - Init function must configure for both 24C02 and SSD1306
  - Write operations use different device addresses
```

### 7.3 Display Layout

```
┌────────────────────────────────┐
│  XY Table Controller           │  Title (small font, centered)
│                                │
│  X: +700.000 mm                │  X position (large font)
│  Y: +350.000 mm                │  Y position (large font)
│                                │
│  Status: MOVING                │  System status (READY/MOVING/HOMING/ALARM)
│  Spd:  500 mm/min              │  Current speed
└────────────────────────────────┘
```

---

## 8. Software Architecture

### 8.1 Module Structure

```
Project/
├── Core/
│   ├── Inc/
│   │   ├── config.h        // Pin defs, constants, all parameters
│   │   ├── uart.h          // USART1 driver
│   │   ├── timer.h         // TIM2/TIM3 pulse engine
│   │   ├── motion.h        // Motion planner + Bresenham
│   │   ├── servo.h         // Servo control + homing
│   │   ├── oled.h          // SSD1306 I2C driver
│   │   ├── protocol.h      // G-code parser
│   │   └── sys_tick.h      // System tick (1ms)
│   └── Src/
│       ├── main.c
│       ├── uart.c
│       ├── timer.c
│       ├── motion.c
│       ├── servo.c
│       ├── oled.c
│       ├── protocol.c
│       └── sys_tick.c
└── STM32F103ZET6_FLASH.ld
```

### 8.2 Main Loop

```c
int main(void) {
    // Init
    SysTick_Init();          // 1ms system tick
    GPIO_Init();             // All direction/SON/ALM/home pins
    UART1_Init(115200);      // PA9/PA10, interrupt RX, ring buffer
    TIM2_Init();             // PA15 remap, PWM mode, default freq 1kHz
    TIM3_Init();             // PA6, PWM mode, default freq 1kHz
    I2C1_Init();             // PB6/PB7, 400kHz, for OLED
    OLED_Init();             // SSD1306 init sequence
    Motion_Init();           // Reset step counters, state

    OLED_DrawTitle("XY Table Controller");
    UART1_Send("READY\n");

    while (1) {
        // 1. Process received commands
        if (UART1_HasCommand()) {
            Protocol_Parse(UART1_GetCommand());
        }

        // 2. Update motion engine
        Motion_Update();

        // 3. Check alarms
        if (Servo_AlarmCheck()) {
            Motion_Stop();
            UART1_Sendf("ALM %d\n", Servo_GetAlarmCode());
        }

        // 4. Refresh OLED (every 200ms)
        if (SysTick_200ms()) {
            OLED_Update(Motion_GetX(), Motion_GetY(), Motion_GetStatus());
        }

        // 5. Report position after move complete
        if (Motion_MoveComplete()) {
            UART1_Sendf("POS X=%.2f Y=%.2f\n",
                        Motion_GetX_mm(), Motion_GetY_mm());
        }
    }
}
```

### 8.3 Command Parser Logic

```c
void Protocol_Parse(char *cmd) {
    if      (starts_with(cmd, "G00")) Motion_RapidMove(parse_x(cmd), parse_y(cmd));
    else if (starts_with(cmd, "G01")) Motion_LinearMove(parse_x(cmd), parse_y(cmd), parse_f(cmd));
    else if (starts_with(cmd, "G28")) Servo_Home();
    else if (starts_with(cmd, "G92")) { set_x(parse_x(cmd)); set_y(parse_y(cmd)); UART1_Send("OK\n"); }
    else if (starts_with(cmd, "M03"))  { Servo_Enable();  UART1_Send("OK\n"); }
    else if (starts_with(cmd, "M05"))  { Servo_Disable(); UART1_Send("OK\n"); }
    else if (starts_with(cmd, "M112")) Motion_EmergencyStop();
    else if (starts_with(cmd, "M114")) UART1_Sendf("POS X=%.2f Y=%.2f\n", get_x_mm(), get_y_mm());
    else if (starts_with(cmd, "JOG"))  Motion_Jog(parse_dir(cmd), parse_step(cmd));
    else UART1_Send("ERR Unknown command\n");
}
```

---

## 9. Key Constants (config.h) — FINAL VALUES

```c
// ── Slide Table (GTTHS5-L10-700-BC-H10-C4) ──
#define LEAD_MM             10.0f       // Screw lead = 10mm/rev
#define ENCODER_RES         10000       // Encoder pulses per revolution
#define PULSE_PER_MM        1000.0f     // 1 pulse = 0.001mm (1μm) @ 1:1 gear ratio
#define GEAR_NUMERATOR      1           // No.34.0
#define GEAR_DENOMINATOR    1           // No.36.0
#define X_MAX_TRAVEL        700.0f      // mm
#define Y_MAX_TRAVEL        700.0f      // mm (assuming same table)

// ── Pin Definitions ──
// X-axis (TIM2 on PA15)
#define X_PULSE_PORT        GPIOA
#define X_PULSE_PIN         GPIO_Pin_15  // TIM2_CH1, remap via AFIO
#define X_DIR_PORT          GPIOC
#define X_DIR_PIN           GPIO_Pin_13
#define X_SON_PORT          GPIOE
#define X_SON_PIN           GPIO_Pin_0
#define X_ALM_PORT          GPIOE
#define X_ALM_PIN           GPIO_Pin_1
#define X_HOME_PORT         GPIOE
#define X_HOME_PIN          GPIO_Pin_2

// Y-axis (TIM3 on PA6)
#define Y_PULSE_PORT        GPIOA
#define Y_PULSE_PIN         GPIO_Pin_6   // TIM3_CH1, default mapping
#define Y_DIR_PORT          GPIOA
#define Y_DIR_PIN           GPIO_Pin_7
#define Y_SON_PORT          GPIOA
#define Y_SON_PIN           GPIO_Pin_5
#define Y_ALM_PORT          GPIOA
#define Y_ALM_PIN           GPIO_Pin_1
#define Y_HOME_PORT         GPIOF
#define Y_HOME_PIN          GPIO_Pin_0

// UART
#define UART_RX_PORT        GPIOA
#define UART_RX_PIN         GPIO_Pin_10
#define UART_TX_PORT        GPIOA
#define UART_TX_PIN         GPIO_Pin_9

// I2C (OLED + 24C02 shared)
#define I2C_SCL_PORT        GPIOB
#define I2C_SCL_PIN         GPIO_Pin_6
#define I2C_SDA_PORT        GPIOB
#define I2C_SDA_PIN         GPIO_Pin_7
#define OLED_ADDR           0x3C
#define EEPROM_ADDR         0x50

// ── Motion Parameters ──
#define SYSTEM_CLK          72000000    // 72 MHz
#define TIMER_PRESCALER     71          // Timer tick = 1 MHz
#define MAX_SPEED           5000.0f     // mm/min
#define MIN_SPEED           10.0f       // mm/min
#define ACCELERATION        500.0f      // mm/min² (adjust experimentally)
#define HOME_SPEED_FAST     50.0f       // mm/min (approach home)
#define HOME_SPEED_SLOW     10.0f       // mm/min (precise home)

// ── UART ──
#define UART_BAUDRATE       115200
#define RX_BUFFER_SIZE      256

// ── OLED ──
#define OLED_I2C_SPEED      400000      // 400 kHz Fast Mode
```

---

## 10. Critical Notes for Firmware Developer

1. **JTAG Disable**: First thing in main(), call `GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE)` to free PA15 for TIM2_CH1. SWD (PA13/PA14) still works.

2. **TIM2 remap**: X-axis uses TIM2_CH1 on PA15 (full remap). Configure: `GPIO_PinRemapConfig(GPIO_FullRemap_TIM2, ENABLE)`.

3. **I2C shared bus**: PB6/PB7 carries both EEPROM (0x50) and OLED (0x3C). Use correct device address for each operation. No bus conflict.

4. **Pulse mode**: PWM Mode 1, 50% duty at CCR = ARR/2. PULSE+ and PULSE- are differential inputs; single-ended drive via optocoupler works as long as PULSE- is tied to GND.

5. **Direction timing**: Set direction GPIO at least 5μs before first pulse. Violating setup time causes lost/missed steps.

6. **Step counting**: Use signed int32 step counters per axis. Range: ±2,147,483,647 steps = ±2,147,483mm. Always use float division for mm conversion: `mm = steps / 1000.0f`.

7. **Travel limits**: Before executing any move, clamp target coordinates to [0, MAX_TRAVEL]. Report error if out of bounds.

8. **Alarm handling**: ALM pins are active LOW. If alarm triggers, STOP IMMEDIATELY — do not wait for current move to finish.

9. **UART RX**: Use USART1 interrupt with ring buffer. Parse commands in main loop, NEVER in ISR. Commands end with `\n`.

10. **Position reporting**: Send position after every move completes (not during motion). Can also send periodic updates (every 200ms) during long moves.

11. **Servo enable sequence**: SON HIGH → wait 200ms (servo internal init) → then send commands. Sending commands immediately after SON can cause servo fault.

12. **Hardware safety**: Wire an external emergency stop button that physically cuts 24V power to CN1 PIN47. This is independent of STM32 and works even if MCU crashes.

---

## 11. PC Software

Already built: `D:\AI claude\sifu\XY_Table_Controller.exe`

Features: serial connection, XY canvas, JOG, coordinate input, homing, emergency stop, command log.
Source: `D:\AI claude\sifu\xy_table_control.py`
