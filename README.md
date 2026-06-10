# XY Table Controller (十字滑台控制系统)

基于 STM32F1xx 的十字滑台运动控制系统，包含上位机软件和下位机固件。

## 项目结构

```
├── code test/sorf/          # 上位机软件 (Python)
│   ├── main.py              # 程序入口
│   ├── requirements.txt     # Python 依赖
│   ├── core/                # 核心模块
│   │   ├── protocol.py      # 通信协议
│   │   ├── serial_manager.py # 串口管理
│   │   └── motion_state.py  # 运动状态
│   └── ui/                  # 界面模块
│       ├── main_window.py   # 主窗口
│       ├── control_panel.py # 控制面板
│       ├── monitor_panel.py # 监控面板
│       ├── serial_panel.py  # 串口面板
│       ├── status_panel.py  # 状态面板
│       ├── xy_canvas.py     # XY画布
│       └── theme.py         # 主题样式
│
├── sifu move/               # STM32 固件 (Keil/CubeMX)
│   ├── Core/
│   │   ├── Inc/             # 头文件
│   │   │   ├── main.h
│   │   │   ├── config.h     # 系统配置
│   │   │   ├── motion.h     # 运动控制
│   │   │   ├── protocol.h   # 通信协议
│   │   │   ├── servo.h      # 舵机驱动
│   │   │   ├── oled.h       # OLED显示
│   │   │   └── ...
│   │   └── Src/             # 源文件
│   │       ├── main.c
│   │       ├── motion.c     # 运动控制实现
│   │       ├── protocol.c   # 协议解析
│   │       ├── servo.c      # 舵机驱动
│   │       ├── oled.c       # OLED驱动
│   │       └── ...
│   └── Drivers/             # STM32 HAL 驱动
│
├── xy_table_control.py      # 旧版控制脚本
├── STM32_Firmware_Spec.md   # STM32 固件规格说明
└── CubeMX_Pin_Config.md     # CubeMX 引脚配置
```

## 功能特性

- **上位机**: Python GUI 界面，支持串口通信、实时监控、运动控制
- **下位机**: STM32F1xx 固件，支持多轴联动、OLED 显示、串口协议通信
- **通信协议**: 自定义串口协议，支持指令下发和状态上报

## 环境要求

### 上位机
- Python 3.x
- 依赖见 `code test/sorf/requirements.txt`

### 下位机
- Keil MDK / STM32CubeIDE
- STM32F1xx HAL 库
