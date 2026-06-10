"""协议层 — G-code命令生成与响应解析 (含居中坐标系转换)"""
import re

from PyQt6.QtCore import QObject, pyqtSignal

from core.motion_state import (
    MotionState, MotionStatus, AlarmStatus, to_stm32, from_stm32, HALF_TRAVEL
)


class Protocol(QObject):
    """协议处理器：命令生成 + 响应解析 + 信号通知"""

    position_updated = pyqtSignal(float, float)
    status_changed = pyqtSignal(str)
    alarm_triggered = pyqtSignal(int, str)
    homing_done = pyqtSignal()
    ready_received = pyqtSignal()
    response_logged = pyqtSignal(str, str)
    soft_limit_hit = pyqtSignal()  # 软限位拦截通知

    def __init__(self):
        super().__init__()
        self.state = MotionState()

    # ── 命令生成 (PC → STM32) ──
    # 输入为居中坐标, 发送前转为STM32坐标

    def cmd_g00(self, x: float, y: float) -> str:
        x, y = self.state.clamp_target(x, y)
        ox, oy = x, y
        x, y = self.state.clamp_soft_limits(x, y)
        if ox != x or oy != y:
            self.soft_limit_hit.emit()
        self.state.set_target(x, y)
        tx = to_stm32(x)
        ty = to_stm32(y)
        return f"G00 X{tx:.2f} Y{ty:.2f}"

    def cmd_g01(self, x: float, y: float, speed: float = 500.0) -> str:
        x, y = self.state.clamp_target(x, y)
        ox, oy = x, y
        x, y = self.state.clamp_soft_limits(x, y)
        if ox != x or oy != y:
            self.soft_limit_hit.emit()
        self.state.set_target(x, y)
        speed = max(self.state.min_speed, min(speed, self.state.max_speed))
        self.state.current_speed = speed
        tx = to_stm32(x)
        ty = to_stm32(y)
        return f"G01 X{tx:.2f} Y{ty:.2f} F{speed:.0f}"

    def cmd_g28(self) -> str:
        self.state.is_homing = True
        self.state.motion_status = MotionStatus.HOMING
        self.status_changed.emit("归零中")
        return "G28"

    def cmd_g92(self, x: float = 0.0, y: float = 0.0) -> str:
        x, y = self.state.clamp_target(x, y)
        self.state.set_position(x, y)
        tx = to_stm32(x)
        ty = to_stm32(y)
        return f"G92 X{tx:.2f} Y{ty:.2f}"

    def cmd_m03(self) -> str:
        return "M03"

    def cmd_m05(self) -> str:
        return "M05"

    def cmd_m112(self) -> str:
        self.state.motion_status = MotionStatus.ESTOP
        self.status_changed.emit("急停")
        return "M112"

    def cmd_m114(self) -> str:
        return "M114"

    def reset_estop(self):
        """急停复位: 清除PC端ESTOP状态, 伺服状态恢复"""
        self.state.motion_status = MotionStatus.IDLE
        self.state.alarm_status = AlarmStatus.NONE
        self.state.alarm_code = 0
        self.status_changed.emit("就绪")

    def cmd_jog(self, axis: str, direction: str, step: float) -> str:
        """JOG: 检查软限位, 超界则阻止"""
        if self.state.soft_limit_enabled:
            s = step if direction == '+' else -step
            nx = self.state.x_mm + (s if axis == 'X' else 0)
            ny = self.state.y_mm + (s if axis == 'Y' else 0)
            if not self.state.is_within_soft_limits(nx, ny):
                self.soft_limit_hit.emit()
                return ""  # 空字符串 = 不发送
        return f"JOG {axis}{direction} S{step:.1f}"

    # ── 响应解析 (STM32 → PC) ──
    # 收到的是STM32坐标, 转为居中坐标再通知UI

    def parse_line(self, line: str):
        if not line:
            return

        self.response_logged.emit("RX", line)

        # POS X=xxx Y=xxx  (STM32坐标 → 居中坐标)
        m = re.match(r"POS\s+X=([-\d.]+)\s+Y=([-\d.]+)", line, re.IGNORECASE)
        if m:
            raw_x = float(m.group(1))
            raw_y = float(m.group(2))
            x = from_stm32(raw_x)
            y = from_stm32(raw_y)
            self.state.update_position(x, y)
            self.position_updated.emit(x, y)
            return

        # HOME DONE
        if re.match(r"HOME\s+DONE", line, re.IGNORECASE):
            self.state.is_homing = False
            self.state.set_position(0.0, 0.0)
            self.state.motion_status = MotionStatus.IDLE
            self.homing_done.emit()
            self.position_updated.emit(0.0, 0.0)
            self.status_changed.emit("就绪")
            return

        # ALM <code>
        m = re.match(r"ALM\s+(\d+)", line, re.IGNORECASE)
        if m:
            code = int(m.group(1))
            desc = {1: "X轴报警", 2: "Y轴报警", 3: "双轴报警"}.get(code, f"未知报警({code})")
            self.state.update_alarm(code)
            self.state.motion_status = MotionStatus.ESTOP
            self.alarm_triggered.emit(code, desc)
            self.status_changed.emit(desc)
            return

        # READY
        if "READY" in line.upper():
            self.ready_received.emit()
            self.status_changed.emit("就绪")
            return

        # OK
        if line.strip().upper() == "OK":
            return

        # ERR
        if line.upper().startswith("ERR"):
            self.status_changed.emit(line)
            return

    def log_tx(self, cmd: str):
        self.response_logged.emit("TX", cmd.strip())
