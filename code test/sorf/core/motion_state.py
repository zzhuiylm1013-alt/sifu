"""运动状态数据模型 — 居中坐标系 (原点=十字滑台中心点)"""

from dataclasses import dataclass, field
from enum import Enum, auto

# STM32内部使用 0~700mm, PC端显示 -350~+350mm
HALF_TRAVEL = 350.0
TOTAL_TRAVEL = 700.0


class MotionStatus(Enum):
    IDLE = "就绪"
    RUNNING = "运行中"
    ESTOP = "急停"
    HOMING = "归零中"


class ServoStatus(Enum):
    OFF = "关闭"
    ON = "使能"


class AlarmStatus(Enum):
    NONE = "无报警"
    X_AXIS = "X轴报警"
    Y_AXIS = "Y轴报警"
    BOTH = "双轴报警"


def to_stm32(mm: float) -> float:
    """居中坐标 → STM32坐标 (加偏移)"""
    return mm + HALF_TRAVEL


def from_stm32(raw: float) -> float:
    """STM32坐标 → 居中坐标 (减偏移)"""
    return raw - HALF_TRAVEL


@dataclass
class MotionState:
    x_mm: float = 0.0
    y_mm: float = 0.0
    x_target_mm: float = 0.0
    y_target_mm: float = 0.0
    current_speed: float = 0.0

    motion_status: MotionStatus = MotionStatus.IDLE
    servo_status: ServoStatus = ServoStatus.OFF
    alarm_status: AlarmStatus = AlarmStatus.NONE
    alarm_code: int = 0

    is_homing: bool = False
    home_state: str = ""

    # 系统参数
    half_travel: float = HALF_TRAVEL
    total_travel: float = TOTAL_TRAVEL
    max_speed: float = 5000.0
    min_speed: float = 10.0
    pulse_per_mm: float = 1000.0

    # 电子限位 (软限位, 默认禁用=全行程)
    soft_limit_enabled: bool = False
    soft_x_min: float = -HALF_TRAVEL
    soft_x_max: float = HALF_TRAVEL
    soft_y_min: float = -HALF_TRAVEL
    soft_y_max: float = HALF_TRAVEL
    # 标记哪些限位已被用户显式标定（未标定的在绘制时用0代替，避免红框偏移）
    x_min_set: bool = False
    x_max_set: bool = False
    y_min_set: bool = False
    y_max_set: bool = False

    def _resolved_soft_limits(self) -> tuple[float, float, float, float]:
        """Return active bounds. Uncalibrated sides fall back to full travel."""
        x_min = self.soft_x_min if self.x_min_set else -HALF_TRAVEL
        x_max = self.soft_x_max if self.x_max_set else HALF_TRAVEL
        y_min = self.soft_y_min if self.y_min_set else -HALF_TRAVEL
        y_max = self.soft_y_max if self.y_max_set else HALF_TRAVEL
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min
        return x_min, x_max, y_min, y_max

    def _soft_limits_valid(self) -> bool:
        """电子限位有效性: 启用后至少一个边界已标定。"""
        return any([self.x_min_set, self.x_max_set, self.y_min_set, self.y_max_set])

    def _soft_limits_range_valid(self) -> bool:
        """Reject a zero-size calibrated box so stale bad limits cannot lock motion."""
        if self.x_min_set and self.x_max_set and self.soft_x_min == self.soft_x_max:
            return False
        if self.y_min_set and self.y_max_set and self.soft_y_min == self.soft_y_max:
            return False
        return True

    def clamp_soft_limits(self, x: float, y: float) -> tuple[float, float]:
        """软限位钳位: 禁用时完全直通; 未标定方向不参与限制。"""
        if (not self.soft_limit_enabled or not self._soft_limits_valid()
                or not self._soft_limits_range_valid()):
            return x, y
        x_min, x_max, y_min, y_max = self._resolved_soft_limits()
        x = max(x_min, min(x, x_max))
        y = max(y_min, min(y, y_max))
        return x, y

    def is_within_soft_limits(self, x: float, y: float) -> bool:
        if (not self.soft_limit_enabled or not self._soft_limits_valid()
                or not self._soft_limits_range_valid()):
            return True
        x_min, x_max, y_min, y_max = self._resolved_soft_limits()
        return x_min <= x <= x_max and y_min <= y <= y_max

    def reset_soft_limits(self):
        self.soft_limit_enabled = False
        self.soft_x_min = -HALF_TRAVEL
        self.soft_x_max = HALF_TRAVEL
        self.soft_y_min = -HALF_TRAVEL
        self.soft_y_max = HALF_TRAVEL
        self.x_min_set = self.x_max_set = self.y_min_set = self.y_max_set = False

    def clamp_target(self, x: float, y: float) -> tuple[float, float]:
        h = self.half_travel
        x = max(-h, min(x, h))
        y = max(-h, min(y, h))
        return x, y

    def set_position(self, x: float, y: float):
        self.x_mm = x
        self.y_mm = y
        self.x_target_mm = x
        self.y_target_mm = y

    def set_target(self, x: float, y: float):
        self.x_target_mm, self.y_target_mm = self.clamp_target(x, y)

    def update_position(self, x: float, y: float):
        self.x_mm = x
        self.y_mm = y

    def update_alarm(self, code: int):
        self.alarm_code = code
        if code == 0:
            self.alarm_status = AlarmStatus.NONE
        elif code == 1:
            self.alarm_status = AlarmStatus.X_AXIS
        elif code == 2:
            self.alarm_status = AlarmStatus.Y_AXIS
        elif code == 3:
            self.alarm_status = AlarmStatus.BOTH

    def reset(self):
        self.x_mm = 0.0
        self.y_mm = 0.0
        self.x_target_mm = 0.0
        self.y_target_mm = 0.0
        self.motion_status = MotionStatus.IDLE
        self.alarm_status = AlarmStatus.NONE
        self.alarm_code = 0
        self.is_homing = False
