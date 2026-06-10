"""运动控制面板 — 坐标输入、运动控制、JOG点动、伺服控制（紧凑布局）"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QPushButton, QLabel, QDoubleSpinBox,
    QComboBox, QSizePolicy,
)


class ControlPanel(QWidget):
    """控制面板"""

    cmd_g00 = pyqtSignal(float, float)
    cmd_g01 = pyqtSignal(float, float, float)
    cmd_g28 = pyqtSignal()
    cmd_g92 = pyqtSignal(float, float)
    cmd_m03 = pyqtSignal()
    cmd_m05 = pyqtSignal()
    cmd_m112 = pyqtSignal()
    cmd_jog = pyqtSignal(str, str, float)
    cmd_m114 = pyqtSignal()
    cmd_reset = pyqtSignal()
    cmd_jog_home = pyqtSignal()
    cmd_set_limit = pyqtSignal(str)       # 'xmin','xmax','ymin','ymax'
    cmd_limit_toggle = pyqtSignal(bool)    # enable/disable
    cmd_limit_reset = pyqtSignal()
    cmd_limit_center = pyqtSignal()   # 设限位中心为原点

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(5)

        # ── 目标坐标输入 ──
        grp_target = QGroupBox("目标坐标")
        grp_target.setStyleSheet(
            "QGroupBox { padding: 8px 8px 6px 8px; margin-top: 14px; }"
            "QGroupBox::title { padding: 1px 8px; }"
        )
        lt = QGridLayout(grp_target)
        lt.setContentsMargins(6, 10, 6, 6)
        lt.setHorizontalSpacing(6)
        lt.setVerticalSpacing(4)

        lt.addWidget(QLabel("X:"), 0, 0)
        self._spin_x = QDoubleSpinBox()
        self._spin_x.setRange(-350, 350)
        self._spin_x.setDecimals(1)
        self._spin_x.setValue(0)
        self._spin_x.setSuffix(" mm")
        self._spin_x.setSingleStep(10)
        self._spin_x.setMinimumWidth(90)
        self._spin_x.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        lt.addWidget(self._spin_x, 0, 1)

        lt.addWidget(QLabel("Y:"), 0, 2)
        self._spin_y = QDoubleSpinBox()
        self._spin_y.setRange(-350, 350)
        self._spin_y.setDecimals(1)
        self._spin_y.setValue(0)
        self._spin_y.setSuffix(" mm")
        self._spin_y.setSingleStep(10)
        self._spin_y.setMinimumWidth(90)
        self._spin_y.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        lt.addWidget(self._spin_y, 0, 3)

        lt.addWidget(QLabel("速度:"), 1, 0)
        self._spin_speed = QDoubleSpinBox()
        self._spin_speed.setRange(10, 5000)
        self._spin_speed.setDecimals(0)
        self._spin_speed.setValue(2000)
        self._spin_speed.setSuffix(" mm/min")
        self._spin_speed.setSingleStep(100)
        self._spin_speed.setMinimumWidth(90)
        self._spin_speed.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        lt.addWidget(self._spin_speed, 1, 1, 1, 3)

        lt.setColumnStretch(0, 0)   # label
        lt.setColumnStretch(1, 1)   # spinbox X
        lt.setColumnStretch(2, 0)   # label
        lt.setColumnStretch(3, 1)   # spinbox Y

        main_layout.addWidget(grp_target)

        # ── 运动命令按钮 ──
        grp_move = QGroupBox("运动控制")
        grp_move.setStyleSheet(
            "QGroupBox { padding: 8px 8px 6px 8px; margin-top: 14px; }"
            "QGroupBox::title { padding: 1px 8px; }"
        )
        lm = QGridLayout(grp_move)
        lm.setContentsMargins(6, 10, 6, 6)
        lm.setHorizontalSpacing(6)
        lm.setVerticalSpacing(4)

        btn_style = "QPushButton { padding: 5px 10px; min-height: 26px; font-size: 12px; }"

        self._btn_g00 = QPushButton("G00 快速移动")
        self._btn_g00.setObjectName("btnRun")
        self._btn_g00.setStyleSheet(btn_style)
        self._btn_g00.setMinimumWidth(100)
        lm.addWidget(self._btn_g00, 0, 0)

        self._btn_g01 = QPushButton("G01 线性移动")
        self._btn_g01.setStyleSheet(btn_style)
        self._btn_g01.setMinimumWidth(100)
        lm.addWidget(self._btn_g01, 0, 1)

        self._btn_m114 = QPushButton("M114 查询")
        self._btn_m114.setStyleSheet(btn_style)
        self._btn_m114.setMinimumWidth(100)
        lm.addWidget(self._btn_m114, 1, 0)

        self._btn_g92 = QPushButton("G92 设原点")
        self._btn_g92.setStyleSheet(btn_style)
        self._btn_g92.setMinimumWidth(100)
        lm.addWidget(self._btn_g92, 1, 1)

        lm.setColumnStretch(0, 1)
        lm.setColumnStretch(1, 1)

        main_layout.addWidget(grp_move)

        # ── JOG 点动 ──
        grp_jog = QGroupBox("JOG 点动")
        grp_jog.setStyleSheet(
            "QGroupBox { padding: 8px 8px 6px 8px; margin-top: 14px; }"
            "QGroupBox::title { padding: 1px 8px; }"
        )
        lj = QVBoxLayout(grp_jog)
        lj.setContentsMargins(6, 10, 6, 6)
        lj.setSpacing(5)

        # 步距选择
        row_step = QHBoxLayout()
        row_step.addWidget(QLabel("步距:"))
        self._combo_step = QComboBox()
        self._combo_step.addItems(["0.1 mm","0.5 mm","1 mm","5 mm","10 mm","50 mm","100 mm"])
        self._combo_step.setCurrentIndex(2)
        self._combo_step.setMinimumWidth(80)
        row_step.addWidget(self._combo_step, 1)
        lj.addLayout(row_step)

        # 方向按钮十字
        gj = QGridLayout()
        gj.setSpacing(4)
        gj.setContentsMargins(4, 2, 4, 2)
        jog_btn = "QPushButton { padding: 5px 8px; min-height: 28px; font-size: 13px; }"

        self._btn_yp = QPushButton("Y+ ↑")
        self._btn_yp.setStyleSheet(jog_btn)
        self._btn_yp.setMinimumWidth(64)
        gj.addWidget(self._btn_yp, 0, 1)
        self._btn_xm = QPushButton("← X-")
        self._btn_xm.setStyleSheet(jog_btn)
        self._btn_xm.setMinimumWidth(64)
        gj.addWidget(self._btn_xm, 1, 0)
        self._btn_home_center = QPushButton("归零")
        self._btn_home_center.setStyleSheet(jog_btn + "font-weight:bold;")
        self._btn_home_center.setMinimumWidth(64)
        gj.addWidget(self._btn_home_center, 1, 1)
        self._btn_xp = QPushButton("X+ →")
        self._btn_xp.setStyleSheet(jog_btn)
        self._btn_xp.setMinimumWidth(64)
        gj.addWidget(self._btn_xp, 1, 2)
        self._btn_ym = QPushButton("Y- ↓")
        self._btn_ym.setStyleSheet(jog_btn)
        self._btn_ym.setMinimumWidth(64)
        gj.addWidget(self._btn_ym, 2, 1)

        gj.setColumnStretch(0, 1)
        gj.setColumnStretch(1, 1)
        gj.setColumnStretch(2, 1)
        lj.addLayout(gj)
        main_layout.addWidget(grp_jog)

        # ── 伺服控制 ──
        grp_servo = QGroupBox("伺服")
        grp_servo.setStyleSheet(
            "QGroupBox { padding: 8px 8px 6px 8px; margin-top: 14px; }"
            "QGroupBox::title { padding: 1px 8px; }"
        )
        ls = QGridLayout(grp_servo)
        ls.setContentsMargins(6, 10, 6, 6)
        ls.setHorizontalSpacing(6)
        ls.setVerticalSpacing(4)

        self._btn_m03 = QPushButton("M03 伺服ON")
        self._btn_m03.setStyleSheet(
            "QPushButton { color: #4aff9e; border-color: #1a6e3e;"
            " padding: 5px 10px; min-height: 28px; font-size: 12px; }"
        )
        self._btn_m03.setMinimumWidth(82)
        ls.addWidget(self._btn_m03, 0, 0)

        self._btn_m05 = QPushButton("M05 伺服OFF")
        self._btn_m05.setStyleSheet(
            "QPushButton { color: #ffb347; border-color: #6e5a1a;"
            " padding: 5px 10px; min-height: 28px; font-size: 12px; }"
        )
        self._btn_m05.setMinimumWidth(82)
        ls.addWidget(self._btn_m05, 0, 1)

        self._btn_g28 = QPushButton("G28 归零")
        self._btn_g28.setStyleSheet(
            "QPushButton { color: #6dd5ed; border-color: #1e6e8a; font-weight: bold;"
            " padding: 5px 10px; min-height: 28px; font-size: 12px; }"
        )
        self._btn_g28.setMinimumWidth(82)
        ls.addWidget(self._btn_g28, 0, 2)

        self._btn_estop = QPushButton("M112 急停")
        self._btn_estop.setObjectName("btnEstop")
        self._btn_estop.setMinimumHeight(32)
        ls.addWidget(self._btn_estop, 1, 0, 1, 2)

        self._btn_reset = QPushButton("急停复位")
        self._btn_reset.setStyleSheet(
            "QPushButton { color: #ffb347; border-color: #6e5a1a; font-weight: bold;"
            " padding: 5px 10px; min-height: 32px; font-size: 12px; }"
            "QPushButton:hover { background-color: #3d2a10; border-color: #ffb347; }"
        )
        self._btn_reset.setMinimumWidth(82)
        ls.addWidget(self._btn_reset, 1, 2)

        ls.setColumnStretch(0, 1)
        ls.setColumnStretch(1, 1)
        ls.setColumnStretch(2, 1)

        main_layout.addWidget(grp_servo)

        # ── 电子限位 ──
        grp_limit = QGroupBox("电子限位")
        grp_limit.setStyleSheet(
            "QGroupBox { padding: 8px 8px 6px 8px; margin-top: 14px; }"
            "QGroupBox::title { padding: 1px 8px; }"
        )
        ll = QVBoxLayout(grp_limit)
        ll.setContentsMargins(6, 10, 6, 6)
        ll.setSpacing(4)

        # 启用 + 清除行
        row_toggle = QHBoxLayout()
        self._chk_limit_enable = QPushButton("● 启用限位")
        self._chk_limit_enable.setCheckable(True)
        self._chk_limit_enable.setStyleSheet(
            "QPushButton { padding: 4px 10px; min-height: 26px; font-size: 12px;"
            " color: #ffb347; border-color: #6e5a1a; font-weight: bold; }"
            "QPushButton:checked { color: #4aff9e; border-color: #1a6e3e; }"
        )
        row_toggle.addWidget(self._chk_limit_enable)
        row_toggle.addStretch()
        self._btn_limit_reset = QPushButton("清除")
        self._btn_limit_reset.setStyleSheet(
            "QPushButton { padding: 4px 12px; min-height: 26px; font-size: 11px;"
            " color: #ff6b6b; border-color: #8e1a1a; }"
        )
        row_toggle.addWidget(self._btn_limit_reset)
        ll.addLayout(row_toggle)

        # 四方向限位值+按钮 (2行×4列网格)
        gl = QGridLayout()
        gl.setSpacing(3)
        gl.setContentsMargins(2, 2, 2, 2)
        val_style = "QLabel { color: #6dd5ed; font-size: 11px; font-weight: bold;"
        val_style += " background-color: #0a1220; border: 1px solid #1e3a5f;"
        val_style += " border-radius: 2px; padding: 2px 4px; }"
        unset_style = "QLabel { color: #555; font-size: 11px;"
        unset_style += " background-color: #0a1220; border: 1px solid #1a2840;"
        unset_style += " border-radius: 2px; padding: 2px 4px; }"

        # 方向标签列
        for row, axis in enumerate(["X", "Y"]):
            lbl = QLabel(f"{axis}:")
            lbl.setStyleSheet("color: #b0c4de; font-size: 11px; font-weight: bold;")
            gl.addWidget(lbl, row, 0, alignment=Qt.AlignmentFlag.AlignRight)

        # 四个限位值标签 + 按钮
        limits_config = [
            (0, 1, "xmin", "X-"), (0, 3, "xmax", "X+"),
            (1, 1, "ymin", "Y-"), (1, 3, "ymax", "Y+"),
        ]
        self._lbl_limit_vals_widgets = {}
        for row, col, tag, label_text in limits_config:
            # 数值标签
            val_lbl = QLabel("--")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setMinimumWidth(72)
            val_lbl.setMaximumHeight(20)
            val_lbl.setStyleSheet(unset_style)
            gl.addWidget(val_lbl, row, col)
            self._lbl_limit_vals_widgets[tag] = val_lbl
            # 设定按钮
            btn = QPushButton(f"设{label_text}")
            btn.setStyleSheet("QPushButton { padding: 2px 5px; min-height: 22px; font-size: 10px; }")
            btn.clicked.connect(lambda checked, t=tag: self.cmd_set_limit.emit(t))
            gl.addWidget(btn, row, col + 1)
            setattr(self, f"_btn_limit_{tag}", btn)

        # 列拉伸
        gl.setColumnStretch(0, 0)  # 轴标签
        gl.setColumnStretch(1, 1)  # 数值
        gl.setColumnStretch(2, 0)  # 按钮
        gl.setColumnStretch(3, 1)  # 数值
        gl.setColumnStretch(4, 0)  # 按钮
        ll.addLayout(gl)

        # 设限位中心为原点
        self._btn_limit_center = QPushButton("设限位中心为原点")
        self._btn_limit_center.setStyleSheet(
            "QPushButton { padding: 4px 8px; min-height: 26px; font-size: 12px;"
            " color: #6dd5ed; border-color: #1e6e8a; font-weight: bold; }"
            "QPushButton:hover { background-color: #1a3a30; }"
        )
        ll.addWidget(self._btn_limit_center)

        # 范围摘要
        self._lbl_limit_vals = QLabel("未启用 · 限位尚未标定")
        self._lbl_limit_vals.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")
        self._lbl_limit_vals.setWordWrap(True)
        ll.addWidget(self._lbl_limit_vals)

        main_layout.addWidget(grp_limit)
        main_layout.addStretch()

        # ── 信号连接 ──
        self._btn_g00.clicked.connect(lambda: self.cmd_g00.emit(
            self._spin_x.value(), self._spin_y.value()))
        self._btn_g01.clicked.connect(lambda: self.cmd_g01.emit(
            self._spin_x.value(), self._spin_y.value(), self._spin_speed.value()))
        self._btn_g28.clicked.connect(self.cmd_g28.emit)
        self._btn_g92.clicked.connect(lambda: self.cmd_g92.emit(
            self._spin_x.value(), self._spin_y.value()))
        self._btn_m03.clicked.connect(self.cmd_m03.emit)
        self._btn_m05.clicked.connect(self.cmd_m05.emit)
        self._btn_estop.clicked.connect(self.cmd_m112.emit)
        self._btn_reset.clicked.connect(self.cmd_reset.emit)
        self._btn_m114.clicked.connect(self.cmd_m114.emit)
        self._btn_xp.clicked.connect(lambda: self._emit_jog('X', '+'))
        self._btn_xm.clicked.connect(lambda: self._emit_jog('X', '-'))
        self._btn_yp.clicked.connect(lambda: self._emit_jog('Y', '+'))
        self._btn_ym.clicked.connect(lambda: self._emit_jog('Y', '-'))
        self._btn_home_center.clicked.connect(self.cmd_jog_home.emit)
        self._chk_limit_enable.toggled.connect(self.cmd_limit_toggle.emit)
        self._btn_limit_reset.clicked.connect(self.cmd_limit_reset.emit)
        self._btn_limit_center.clicked.connect(self.cmd_limit_center.emit)

    def _emit_jog(self, axis: str, direction: str):
        step_text = self._combo_step.currentText().split()[0]
        step = float(step_text)
        self.cmd_jog.emit(axis, direction, step)

    def set_position(self, x: float, y: float):
        self._spin_x.setValue(x)
        self._spin_y.setValue(y)

    def update_limit_display(self, enabled: bool,
                             x_min: float, x_max: float,
                             y_min: float, y_max: float,
                             x_min_set=False, x_max_set=False,
                             y_min_set=False, y_max_set=False):
        """更新限位面板: 按钮状态 + 各方向数值 + 范围摘要"""
        self._chk_limit_enable.setChecked(enabled)
        set_style = "QLabel { color: #4aff9e; font-size: 11px; font-weight: bold;"
        set_style += " background-color: #0a1220; border: 1px solid #1a6e3e;"
        set_style += " border-radius: 2px; padding: 2px 4px; }"
        unset_style = "QLabel { color: #555; font-size: 11px;"
        unset_style += " background-color: #0a1220; border: 1px solid #1a2840;"
        unset_style += " border-radius: 2px; padding: 2px 4px; }"

        tags = {'xmin': (x_min, x_min_set), 'xmax': (x_max, x_max_set),
                'ymin': (y_min, y_min_set), 'ymax': (y_max, y_max_set)}

        for tag, (val, is_set) in tags.items():
            w = self._lbl_limit_vals_widgets.get(tag)
            if w:
                if is_set:
                    w.setText(f"{val:.0f} mm")
                    w.setStyleSheet(set_style)
                else:
                    w.setText("--")
                    w.setStyleSheet(unset_style)

        set_count = sum([x_min_set, x_max_set, y_min_set, y_max_set])
        if enabled and set_count > 0:
            self._chk_limit_enable.setText(f"● 限位已启用 ({set_count}/4)")
            self._lbl_limit_vals.setText(
                f"范围: X[{x_min:.0f}~{x_max:.0f}]  Y[{y_min:.0f}~{y_max:.0f}]")
            self._lbl_limit_vals.setStyleSheet("color: #4aff9e; font-size: 10px; padding: 2px;")
        elif enabled:
            self._chk_limit_enable.setText("● 限位已启用")
            self._lbl_limit_vals.setText("未标定 · 限位暂不生效")
            self._lbl_limit_vals.setStyleSheet("color: #ffb347; font-size: 10px; padding: 2px;")
        else:
            self._chk_limit_enable.setText("● 启用限位")
            self._lbl_limit_vals.setText("未启用 · 限位未生效" if set_count == 0
                else f"未启用 · 已标定 {set_count}/4 个限位")
            self._lbl_limit_vals.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")

    def set_enabled(self, enabled: bool):
        for w in [self._spin_x, self._spin_y, self._spin_speed,
                  self._btn_g00, self._btn_g01, self._btn_g28, self._btn_g92,
                  self._btn_m03, self._btn_m05, self._btn_m114,
                  self._btn_xp, self._btn_xm, self._btn_yp, self._btn_ym,
                  self._btn_home_center]:
            w.setEnabled(enabled)
        self._btn_estop.setEnabled(True)
        self._btn_reset.setEnabled(True)
