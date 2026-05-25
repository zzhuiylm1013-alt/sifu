# STM32 CubeMX Pin Configuration

> STM32F103ZET6 (正点原子精英版 V2) + DA2Z123 Servo Drive ×2
> Generate CubeMX project with this table, then add firmware code

---

## Clock Configuration

| 项目 | 值 |
|------|-----|
| HSE | 8 MHz (精英版板载晶振) |
| PLL Source | HSE |
| PLL Multiplier | ×9 |
| **SYSCLK** | **72 MHz** |
| AHB Prescaler | /1 → 72 MHz |
| APB1 Prescaler | /2 → 36 MHz (max) |
| APB2 Prescaler | /1 → 72 MHz |
| **TIM2/TIM3 Clock** | **72 MHz** (APB1×2 when prescaler≠1) |

Timer tick after prescaler 71: `72MHz / 72 = 1MHz` (1μs resolution)

---

## STM32 Pin Configuration Table

### X-Axis (TIM2_CH1 on PA15)

| Pin | Function | CubeMX Mode | Output Mode | Speed | Pull | Note |
|-----|----------|-------------|-------------|-------|------|------|
| PA15 | TIM2_CH1 (X PULSE) | `TIM2_CH1` (AF_PP) | Alternate Function Push-Pull | **High** | No pull | 需禁用JTAG |

> **必须在 CubeMX → SYS → Debug 选 `Serial Wire`，释放 PA15/JTDI**

| Pin | Function | CubeMX Mode | Output Mode | Speed | Pull | Note |
|-----|----------|-------------|-------------|-------|------|------|
| PC13 | X DIR | `GPIO_Output` | Push-Pull | Low | No pull | 方向: HIGH=正向, LOW=负向 |
| PE0 | X SON | `GPIO_Output` | Push-Pull | Low | No pull | HIGH=使能伺服 |
| PE1 | X ALM | `GPIO_Input` | — | — | **Pull-up** | 报警信号, 低电平有效 |
| PE2 | X HOME | `GPIO_Input` | — | — | **Pull-up** | NPN限位, 低电平触发 |

### Y-Axis (TIM3_CH1 on PA6)

| Pin | Function | CubeMX Mode | Output Mode | Speed | Pull | Note |
|-----|----------|-------------|-------------|-------|------|------|
| PA6 | TIM3_CH1 (Y PULSE) | `TIM3_CH1` (AF_PP) | Alternate Function Push-Pull | **High** | No pull | 完全空闲引脚 |
| PA7 | Y DIR | `GPIO_Output` | Push-Pull | Low | No pull | 完全空闲 |
| PA5 | Y SON | `GPIO_Output` | Push-Pull | Low | No pull | 完全空闲 |
| PA1 | Y ALM | `GPIO_Input` | — | — | **Pull-up** | 空闲(与ADC焊盘复用) |
| PF0 | Y HOME | `GPIO_Input` | — | — | **Pull-up** | 完全空闲 |

### UART (to PC via CH340)

| Pin | Function | CubeMX Mode | Speed | Pull | Note |
|-----|----------|-------------|-------|------|------|
| PA9 | USART1_TX | `USART1_TX` (AF_PP) | High | No pull | 接CH340 (开发板默认P3跳线) |
| PA10 | USART1_RX | `USART1_RX` | — | No pull | 接CH340 (开发板默认P3跳线) |

### I2C1 (OLED + 24C02 shared bus)

| Pin | Function | CubeMX Mode | Speed | Pull | Note |
|-----|----------|-------------|-------|------|------|
| PB6 | I2C1_SCL | `I2C1_SCL` (AF_OD) | — | External pull-up required | 板载已有24C02+4.7kΩ上拉 |
| PB7 | I2C1_SDA | `I2C1_SDA` (AF_OD) | — | External pull-up required | 板载已有24C02+4.7kΩ上拉 |

> I2C 模式必须选 **Open-Drain (AF_OD)**，CubeMX 会自动设为该模式

### Debug

| Pin | Function | CubeMX Mode | Note |
|-----|----------|-------------|------|
| PA13 | SWDIO | `SYS_SWDIO` | 系统默认 |
| PA14 | SWCLK | `SYS_SWCLK` | 系统默认 |

> CubeMX → SYS → Debug → 选 **`Serial Wire`**（不是 JTAG）

---

## One-Sentence Summary per Pin

```
PA15: AF_PP, High speed  → X轴脉冲
PC13: Output PP          → X轴方向
PE0:  Output PP          → X轴使能
PE1:  Input PU           → X轴报警
PE2:  Input PU           → X轴限位

PA6:  AF_PP, High speed  → Y轴脉冲
PA7:  Output PP          → Y轴方向
PA5:  Output PP          → Y轴使能
PA1:  Input PU           → Y轴报警
PF0:  Input PU           → Y轴限位

PA9:  AF_PP USART1_TX    → PC通信
PA10: Input  USART1_RX   → PC通信

PB6:  AF_OD I2C1_SCL     → OLED+24C02
PB7:  AF_OD I2C1_SDA     → OLED+24C02

PA13: SWDIO              → 调试器
PA14: SWCLK              → 调试器
```

---

## CubeMX Step-by-Step

1. **New Project** → 选择 `STM32F103ZET6`

2. **Pinout → SYS**
   - Debug: `Serial Wire`
   - (不要选 JTAG 5-pin, 否则 PA15 无法释放)

3. **Pinout → RCC**
   - HSE: `Crystal/Ceramic Resonator`

4. **Pinout → 点选各个引脚**，按上表配置：
   - PA15 → `TIM2_CH1`
   - PA6 → `TIM3_CH1`
   - PA9 → `USART1_TX`
   - PA10 → `USART1_RX`
   - PB6 → `I2C1_SCL`
   - PB7 → `I2C1_SDA`
   - PC13, PE0, PA7, PA5 → 右键 `GPIO_Output`
   - PE1, PE2, PA1, PF0 → 右键 `GPIO_Input`

5. **Pinout → 逐一确认 GPIO 属性**：
   - 输入引脚：设置 `Pull-up`
   - 脉冲输出引脚：设置 `GPIO speed = High`（PA15, PA6）
   - 普通输出引脚：设置 `GPIO speed = Low`（PC13, PE0, PA7, PA5）

6. **Clock Configuration**：
   - HSE: 8 MHz
   - PLL Mul: ×9
   - SYSCLK: 72 MHz
   - APB1: /2 → 36 MHz
   - APB2: /1 → 72 MHz

7. **TIM2 Configuration** (X-axis, PA15)：
   - Clock Source: Internal Clock
   - Channel 1: PWM Generation CH1
   - Prescaler: 71
   - Counter Period: 1199 (对应 ~833Hz, 即 50mm/min 最低速)
   - Auto-reload preload: Enable

8. **TIM3 Configuration** (Y-axis, PA6)：
   - 同上，独立配置

9. **USART1 Configuration** (PA9/PA10)：
   - Mode: Asynchronous
   - Baud Rate: 115200
   - 8N1, no flow control
   - NVIC: USART1 global interrupt → Enable

10. **I2C1 Configuration** (PB6/PB7)：
    - Speed: Fast Mode (400 kHz)
    - Auto-addressing disabled

11. **Save → Generate Code**，选择 Toolchain/IDE 对应的项目格式

> 生成后用 CubeMX 的 .ioc 文件配合 `STM32_Firmware_Spec.md` 即可开始写固件代码。
