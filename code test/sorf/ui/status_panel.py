"""状态信息面板 — 实时显示坐标、状态、报警"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QFrame,
)


class StatusPanel(QWidget):
    """状态信息面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── 当前位置 ──
        grp_pos = QGroupBox("当前位置")
        grid_pos = QGridLayout(grp_pos)
        grid_pos.setSpacing(8)

        grid_pos.addWidget(self._make_label("X 轴", "#6dd5ed"), 0, 0)
        self._lbl_x = self._make_value("0.00 mm")
        grid_pos.addWidget(self._lbl_x, 0, 1)

        grid_pos.addWidget(self._make_label("Y 轴", "#6dd5ed"), 0, 2)
        self._lbl_y = self._make_value("0.00 mm")
        grid_pos.addWidget(self._lbl_y, 0, 3)
        layout.addWidget(grp_pos)

        # ── 系统状态 ──
        grp_state = QGroupBox("系统状态")
        grid_state = QGridLayout(grp_state)
        grid_state.setSpacing(6)

        grid_state.addWidget(self._make_label("运动状态:"), 0, 0)
        self._lbl_motion = self._make_status("就绪", "#4aff9e")
        grid_state.addWidget(self._lbl_motion, 0, 1)

        grid_state.addWidget(self._make_label("伺服状态:"), 1, 0)
        self._lbl_servo = self._make_status("关闭", "#ffb347")
        grid_state.addWidget(self._lbl_servo, 1, 1)

        grid_state.addWidget(self._make_label("当前速度:"), 2, 0)
        self._lbl_speed = self._make_value("0 mm/min")
        grid_state.addWidget(self._lbl_speed, 2, 1)
        layout.addWidget(grp_state)

        # ── 报警状态 ──
        grp_alarm = QGroupBox("报警信息")
        alarm_layout = QVBoxLayout(grp_alarm)
        self._lbl_alarm = QLabel("无报警")
        self._lbl_alarm.setStyleSheet(
            "color: #4aff9e; font-size: 14px; font-weight: bold;"
            "padding: 6px; background-color: #0d2015;"
            "border: 1px solid #1a6e3e; border-radius: 4px;"
        )
        self._lbl_alarm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_alarm.setMinimumHeight(32)
        alarm_layout.addWidget(self._lbl_alarm)
        layout.addWidget(grp_alarm)

        # ── 连接状态 ──
        grp_conn = QGroupBox("通信状态")
        conn_layout = QHBoxLayout(grp_conn)
        self._led_conn = QLabel("●")
        self._led_conn.setStyleSheet("color: #555; font-size: 18px;")
        self._led_conn.setFixedWidth(20)
        conn_layout.addWidget(self._led_conn)
        self._lbl_conn = QLabel("未连接")
        self._lbl_conn.setStyleSheet("color: #666; font-size: 13px;")
        conn_layout.addWidget(self._lbl_conn)
        conn_layout.addStretch()
        layout.addWidget(grp_conn)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1e3a5f;")
        layout.addWidget(line)

        # ── 参数信息 ──
        grp_param = QGroupBox("系统参数")
        grid_param = QGridLayout(grp_param)
        grid_param.setSpacing(4)
        grid_param.addWidget(self._make_label("行程范围:", font_size=11), 0, 0)
        grid_param.addWidget(self._make_label("X: 0 ~ 700 mm, Y: 0 ~ 700 mm", font_size=11, color="#6dd5ed"), 0, 1)
        grid_param.addWidget(self._make_label("分辨率:", font_size=11), 1, 0)
        grid_param.addWidget(self._make_label("1 μm/pulse (1000 pul/mm)", font_size=11, color="#6dd5ed"), 1, 1)
        grid_param.addWidget(self._make_label("速度范围:", font_size=11), 2, 0)
        grid_param.addWidget(self._make_label("10 ~ 5000 mm/min", font_size=11, color="#6dd5ed"), 2, 1)
        layout.addWidget(grp_param)

        layout.addStretch()

    def _make_label(self, text: str, color: str = "#b0c4de", font_size: int = 12):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: {font_size}px;")
        return lbl

    def _make_value(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("value")
        return lbl

    def _make_status(self, text: str, color: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        return lbl

    # ── 更新方法 ──

    def update_position(self, x: float, y: float):
        self._lbl_x.setText(f"{x:.2f} mm")
        self._lbl_y.setText(f"{y:.2f} mm")

    def update_motion_status(self, status: str):
        color_map = {
            "就绪": "#4aff9e",
            "运行中": "#6dd5ed",
            "急停": "#ff4a4a",
            "归零中": "#ffb347",
        }
        color = color_map.get(status, "#b0c4de")
        self._lbl_motion.setText(status)
        self._lbl_motion.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")

    def update_servo_status(self, enabled: bool):
        if enabled:
            self._lbl_servo.setText("使能")
            self._lbl_servo.setStyleSheet("color: #4aff9e; font-size: 13px; font-weight: bold;")
        else:
            self._lbl_servo.setText("关闭")
            self._lbl_servo.setStyleSheet("color: #ffb347; font-size: 13px; font-weight: bold;")

    def update_speed(self, speed: float):
        self._lbl_speed.setText(f"{speed:.0f} mm/min")

    def update_alarm(self, code: int, desc: str):
        if code == 0:
            self._lbl_alarm.setText("无报警")
            self._lbl_alarm.setStyleSheet(
                "color: #4aff9e; font-size: 14px; font-weight: bold;"
                "padding: 6px; background-color: #0d2015;"
                "border: 1px solid #1a6e3e; border-radius: 4px;"
            )
        else:
            self._lbl_alarm.setText(f"⚠ {desc} (code={code})")
            self._lbl_alarm.setStyleSheet(
                "color: #ff4a4a; font-size: 14px; font-weight: bold;"
                "padding: 6px; background-color: #2d1010;"
                "border: 1px solid #8e1a1a; border-radius: 4px;"
            )

    def update_connection(self, connected: bool):
        if connected:
            self._led_conn.setStyleSheet("color: #4aff9e; font-size: 18px;")
            self._lbl_conn.setText("已连接")
            self._lbl_conn.setStyleSheet("color: #4aff9e; font-size: 13px;")
        else:
            self._led_conn.setStyleSheet("color: #555; font-size: 18px;")
            self._lbl_conn.setText("未连接")
            self._lbl_conn.setStyleSheet("color: #666; font-size: 13px;")
