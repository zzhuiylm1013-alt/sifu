# STM32F103ZET6 Makefile (GCC)
# XY Cross-Slide Table Controller
# Ensure PATH includes: scoop shims + arm-none-eabi-gcc/bin

TARGET = sifu_move
MCU = cortex-m3
CPUFLAGS = -mcpu=$(MCU) -mthumb

# Toolchain (uses PATH, set in VSCode tasks.json or shell profile)
CC = arm-none-eabi-gcc
CXX = arm-none-eabi-g++
AS = arm-none-eabi-gcc -x assembler-with-cpp
OBJCOPY = arm-none-eabi-objcopy
SZ = arm-none-eabi-size

# Source directories
CORE_SRC = Core/Src
HAL_SRC = Drivers/STM32F1xx_HAL_Driver/Src
GCC_STARTUP = Drivers/CMSIS/Device/ST/STM32F1xx/Source/Templates/gcc

# Source files
C_SOURCES = \
  $(CORE_SRC)/main.c \
  $(CORE_SRC)/gpio.c \
  $(CORE_SRC)/i2c.c \
  $(CORE_SRC)/usart.c \
  $(CORE_SRC)/stm32f1xx_it.c \
  $(CORE_SRC)/stm32f1xx_hal_msp.c \
  $(CORE_SRC)/system_stm32f1xx.c \
  $(CORE_SRC)/timer.c \
  $(CORE_SRC)/uart_handler.c \
  $(CORE_SRC)/motion.c \
  $(CORE_SRC)/servo.c \
  $(CORE_SRC)/protocol.c \
  $(CORE_SRC)/oled.c \
  $(CORE_SRC)/sys_tick.c \
  $(HAL_SRC)/stm32f1xx_hal.c \
  $(HAL_SRC)/stm32f1xx_hal_rcc.c \
  $(HAL_SRC)/stm32f1xx_hal_rcc_ex.c \
  $(HAL_SRC)/stm32f1xx_hal_gpio.c \
  $(HAL_SRC)/stm32f1xx_hal_gpio_ex.c \
  $(HAL_SRC)/stm32f1xx_hal_dma.c \
  $(HAL_SRC)/stm32f1xx_hal_cortex.c \
  $(HAL_SRC)/stm32f1xx_hal_pwr.c \
  $(HAL_SRC)/stm32f1xx_hal_flash.c \
  $(HAL_SRC)/stm32f1xx_hal_flash_ex.c \
  $(HAL_SRC)/stm32f1xx_hal_exti.c \
  $(HAL_SRC)/stm32f1xx_hal_uart.c \
  $(HAL_SRC)/stm32f1xx_hal_i2c.c \
  $(HAL_SRC)/stm32f1xx_hal_tim.c \
  $(HAL_SRC)/stm32f1xx_hal_tim_ex.c

ASM_SOURCES = $(GCC_STARTUP)/startup_stm32f103xe.s

# Include paths
INCLUDES = \
  -ICore/Inc \
  -IDrivers/STM32F1xx_HAL_Driver/Inc \
  -IDrivers/STM32F1xx_HAL_Driver/Inc/Legacy \
  -IDrivers/CMSIS/Device/ST/STM32F1xx/Include \
  -IDrivers/CMSIS/Include

# Defines
DEFINES = -DUSE_HAL_DRIVER -DSTM32F103xE

# Flags
CFLAGS = $(CPUFLAGS) -Wall -Wextra -Os -g3 -ffunction-sections -fdata-sections
CFLAGS += $(DEFINES) $(INCLUDES)
CFLAGS += -fno-common -fno-builtin -ffreestanding

LDFLAGS = $(CPUFLAGS) -T STM32F103ZETx_FLASH.ld -Wl,--gc-sections -specs=nosys.specs -specs=nano.specs

# Objects
OBJS = $(C_SOURCES:.c=.o) $(ASM_SOURCES:.s=.o)

all: $(TARGET).elf

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.s
	$(AS) $(CPUFLAGS) $(INCLUDES) $(DEFINES) -c $< -o $@

$(TARGET).elf: $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) -o $@
	$(SZ) $@

bin: $(TARGET).elf
	$(OBJCOPY) -O binary $(TARGET).elf $(TARGET).bin

hex: $(TARGET).elf
	$(OBJCOPY) -O ihex $(TARGET).elf $(TARGET).hex

flash: $(TARGET).elf
	openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program $(TARGET).elf verify reset exit"

clean:
	rm -f $(OBJS) $(TARGET).elf $(TARGET).bin $(TARGET).hex

.PHONY: all clean flash bin hex
