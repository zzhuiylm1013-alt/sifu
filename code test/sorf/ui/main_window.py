"""主窗口 — 布局中枢，信号/槽连接"""
import json, os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QLabel, QMenuBar, QMenu,
    QMessageBox, QApplication, QTabWidget, QScrollArea,
)
from PyQt6.QtGui import QAction

from core.serial_manager import SerialManager
from core.protocol import Protocol
from core.motion_state import HALF_TRAVEL
from ui.xy_canvas import XYCanvas
from ui.control_panel import ControlPanel
from ui.serial_panel import SerialPanel
from ui.monitor_panel import MonitorPanel
from ui.status_panel import StatusPanel
from ui.theme import DARK_THEME

LIMITS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "limits.json")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("十字滑台控制系统 — XY Cross-Slide Table Controller")
        self.resize(1450, 920)
        self.setMinimumSize(1100, 700)

        self._serial = SerialManager()
        self._protocol = Protocol()
        self._origin_synced = False

        self._init_menu()
        self._init_ui()
        self._connect_signals()
        self._load_limits()
        self._on_refresh_ports()

    def _init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件(&F)")
        act_exit = QAction("退出(&X)", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)
        port_menu = menubar.addMenu("串口(&S)")
        act_refresh = QAction("刷新端口(&R)", self)
        act_refresh.triggered.connect(self._on_refresh_ports)
        port_menu.addAction(act_refresh)
        help_menu = menubar.addMenu("帮助(&H)")
        act_about = QAction("关于(&A)", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_h = QHBoxLayout(central)
        main_h.setContentsMargins(6, 6, 6, 6)
        main_h.setSpacing(6)

        # ── 左侧：XY画布 + 状态面板 ──
        left = QVBoxLayout()
        left.setSpacing(6)
        self._canvas = XYCanvas()
        left.addWidget(self._canvas, 1)
        self._status_panel = StatusPanel()
        left.addWidget(self._status_panel)

        # ── 右侧：标签页组织 (运动控制 | 串口通信) ──
        right_tabs = QTabWidget()
        right_tabs.setMinimumWidth(420)

        # 标签页1: 运动控制
        tab_motion = QScrollArea()
        tab_motion.setWidgetResizable(True)
        tab_motion.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._control_panel = ControlPanel()
        tab_motion.setWidget(self._control_panel)
        right_tabs.addTab(tab_motion, "运动控制")

        # 标签页2: 串口通信
        tab_serial = QWidget()
        serial_layout = QVBoxLayout(tab_serial)
        serial_layout.setSpacing(6)
        serial_layout.setContentsMargins(4, 4, 4, 4)
        self._serial_panel = SerialPanel()
        serial_layout.addWidget(self._serial_panel)
        self._monitor = MonitorPanel()
        serial_layout.addWidget(self._monitor, 1)
        right_tabs.addTab(tab_serial, "串口监视")

        # ── 放入主布局 ──
        left_widget = QWidget()
        left_widget.setLayout(left)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([1000, 420])
        main_h.addWidget(splitter)

        # 状态栏
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._lbl_sb_conn = QLabel("串口: 未连接")
        self._lbl_sb_conn.setStyleSheet("color: #666; padding: 0 8px;")
        self._statusbar.addPermanentWidget(self._lbl_sb_conn)
        self._lbl_sb_pos = QLabel("位置: X=0.00 Y=0.00 mm")
        self._lbl_sb_pos.setStyleSheet("color: #6dd5ed; padding: 0 8px;")
        self._statusbar.addPermanentWidget(self._lbl_sb_pos)

    # ── 信号连接 ──

    def _connect_signals(self):
        self._serial_panel.refresh_ports.connect(self._on_refresh_ports)
        self._serial_panel.connect_requested.connect(self._on_connect)
        self._serial_panel.disconnect_requested.connect(self._on_disconnect)
        self._serial.connected.connect(self._on_serial_connected)
        self._serial.line_received.connect(self._on_serial_line)
        self._serial.error_occurred.connect(self._on_serial_error)
        self._protocol.position_updated.connect(self._on_position_update)
        self._protocol.status_changed.connect(self._on_status_change)
        self._protocol.alarm_triggered.connect(self._on_alarm)
        self._protocol.homing_done.connect(self._on_homing_done)
        self._protocol.ready_received.connect(self._on_ready)
        self._protocol.response_logged.connect(self._on_response_log)
        self._control_panel.cmd_g00.connect(self._send_g00)
        self._control_panel.cmd_g01.connect(self._send_g01)
        self._control_panel.cmd_g28.connect(self._send_g28)
        self._control_panel.cmd_g92.connect(self._send_g92)
        self._control_panel.cmd_m03.connect(self._send_m03)
        self._control_panel.cmd_m05.connect(self._send_m05)
        self._control_panel.cmd_m112.connect(self._send_m112)
        self._control_panel.cmd_m114.connect(self._send_m114)
        self._control_panel.cmd_jog.connect(self._send_jog)
        self._control_panel.cmd_jog_home.connect(self._on_jog_home)
        self._control_panel.cmd_reset.connect(self._on_reset_estop)
        self._control_panel.cmd_set_limit.connect(self._on_set_limit)
        self._control_panel.cmd_limit_toggle.connect(self._on_limit_toggle)
        self._control_panel.cmd_limit_reset.connect(self._on_limit_reset)
        self._control_panel.cmd_limit_center.connect(self._on_limit_center)
        self._protocol.soft_limit_hit.connect(self._on_soft_limit_hit)
        self._canvas.point_clicked.connect(self._on_canvas_click)
        self._monitor.send_manual.connect(self._on_manual_send)

    # ── 串口操作 ──

    def _on_refresh_ports(self):
        ports = self._serial.scan_ports()
        self._serial_panel.update_port_list(ports)

    def _on_connect(self, port: str, baud: int):
        self._serial.connect(port, baud)

    def _on_disconnect(self):
        self._serial.disconnect()

    def _on_serial_connected(self, connected: bool):
        self._serial_panel.set_connected(connected)
        self._status_panel.update_connection(connected)
        self._control_panel.set_enabled(connected)
        self._origin_synced = False
        if connected:
            self._lbl_sb_conn.setText(
                f"串口: {self._serial.config.port} @ {self._serial.config.baudrate}"
            )
            self._lbl_sb_conn.setStyleSheet("color: #4aff9e; padding: 0 8px;")
        else:
            self._lbl_sb_conn.setText("串口: 未连接")
            self._lbl_sb_conn.setStyleSheet("color: #666; padding: 0 8px;")

    def _on_serial_line(self, line: str):
        self._protocol.parse_line(line)

    def _on_serial_error(self, msg: str):
        self._monitor.append_info(f"错误: {msg}")
        QMessageBox.warning(self, "串口错误", msg)

    # ── 协议层回调 ──

    def _on_position_update(self, x: float, y: float):
        self._canvas.update_position(x, y)
        self._status_panel.update_position(x, y)
        self._lbl_sb_pos.setText(f"位置: X={x:.2f} Y={y:.2f} mm")
        # 仅当实际位置到达目标附近(容差0.5mm)时才清除目标, 避免JOG目标闪烁
        if self._canvas._target_x is not None:
            dx = abs(x - self._canvas._target_x)
            dy = abs(y - self._canvas._target_y)
            if dx < 0.5 and dy < 0.5:
                self._canvas.clear_target()

    def _on_status_change(self, status: str):
        self._status_panel.update_motion_status(status)

    def _on_alarm(self, code: int, desc: str):
        self._status_panel.update_alarm(code, desc)
        self._monitor.append_info(f"报警: {desc}")

    def _on_homing_done(self):
        self._status_panel.update_alarm(0, "")
        self._monitor.append_info("归零完成")

    def _on_ready(self):
        self._monitor.append_info("设备就绪 (READY)")
        self._ensure_origin_synced()

    def _on_response_log(self, direction: str, content: str):
        if direction == "TX":
            self._monitor.append_tx(content)
        else:
            self._monitor.append_rx(content)

    # ── 命令发送 ──

    def _send_command(self, cmd: str):
        self._protocol.log_tx(cmd)
        self._serial.send(cmd)

    def _ensure_origin_synced(self):
        """Make STM32 raw 350,350 match the PC centered origin before motion."""
        if self._origin_synced:
            return
        cmd = self._protocol.cmd_g92(0, 0)
        self._send_command(cmd)
        self._origin_synced = True
        self._canvas.update_position(0, 0)
        self._status_panel.update_position(0, 0)
        self._control_panel.set_position(0, 0)
        self._monitor.append_info("已同步坐标原点: 当前位置=软件原点(0,0)")

    def _send_g00(self, x: float, y: float):
        self._ensure_origin_synced()
        cmd = self._protocol.cmd_g00(x, y)
        self._send_command(cmd)
        self._canvas.set_target(self._protocol.state.x_target_mm,
                                self._protocol.state.y_target_mm)
        self._status_panel.update_motion_status("运行中")

    def _send_g01(self, x: float, y: float, speed: float):
        self._ensure_origin_synced()
        cmd = self._protocol.cmd_g01(x, y, speed)
        self._send_command(cmd)
        self._canvas.set_target(self._protocol.state.x_target_mm,
                                self._protocol.state.y_target_mm)
        self._status_panel.update_speed(speed)
        self._status_panel.update_motion_status("运行中")

    def _send_g28(self):
        cmd = self._protocol.cmd_g28()
        self._send_command(cmd)

    def _send_g92(self, x: float, y: float):
        cmd = self._protocol.cmd_g92(x, y)
        self._send_command(cmd)
        self._origin_synced = True
        self._canvas.update_position(x, y)
        self._status_panel.update_position(x, y)
        self._control_panel.set_position(x, y)
        self._lbl_sb_pos.setText(f"位置: X={x:.2f} Y={y:.2f} mm")

    def _on_jog_home(self):
        """JOG归零: G00移动到原点 + 即时刷新画布/输入框"""
        self._send_g00(0, 0)
        self._control_panel.set_position(0, 0)
        self._canvas.update_position(0, 0)
        self._canvas.clear_target()

    def _send_m03(self):
        self._send_command(self._protocol.cmd_m03())
        self._status_panel.update_servo_status(True)

    def _send_m05(self):
        self._send_command(self._protocol.cmd_m05())
        self._status_panel.update_servo_status(False)

    def _send_m112(self):
        self._send_command(self._protocol.cmd_m112())
        self._monitor.append_info("紧急停止!")

    def _on_reset_estop(self):
        """急停复位: 重置PC端状态 + 重使能伺服 + 恢复就绪"""
        self._protocol.reset_estop()
        self._send_command(self._protocol.cmd_m03())
        self._status_panel.update_motion_status("就绪")
        self._status_panel.update_alarm(0, "")
        self._status_panel.update_servo_status(True)
        self._monitor.append_info("急停已复位, 伺服重新使能")

    def _send_m114(self):
        self._send_command(self._protocol.cmd_m114())

    def _send_jog(self, axis: str, direction: str, step: float):
        self._ensure_origin_synced()
        cmd = self._protocol.cmd_jog(axis, direction, step)
        if not cmd:  # 软限位拦截
            return
        self._send_command(cmd)
        s = step if direction == '+' else -step
        h = HALF_TRAVEL
        if axis == 'X':
            exp_x = max(-h, min(h, self._protocol.state.x_mm + s))
            exp_y = self._protocol.state.y_mm
        else:
            exp_x = self._protocol.state.x_mm
            exp_y = max(-h, min(h, self._protocol.state.y_mm + s))
        self._protocol.state.update_position(exp_x, exp_y)
        self._control_panel.set_position(exp_x, exp_y)
        self._status_panel.update_position(exp_x, exp_y)
        self._lbl_sb_pos.setText(f"位置: X={exp_x:.2f} Y={exp_y:.2f} mm")
        self._canvas.update_position(exp_x, exp_y)
        self._canvas.set_target(exp_x, exp_y)

    def _on_canvas_click(self, x: float, y: float):
        self._ensure_origin_synced()
        cmd = self._protocol.cmd_g00(x, y)
        self._send_command(cmd)
        self._canvas.set_target(self._protocol.state.x_target_mm,
                                self._protocol.state.y_target_mm)
        self._status_panel.update_motion_status("运行中")

    def _on_manual_send(self, text: str):
        self._send_command(text)

    # ── 电子限位 ──

    def _on_set_limit(self, tag: str):
        """标定限位: 将当前实际位置设为指定边界, 自动排序确保min<max"""
        self._ensure_origin_synced()
        x = self._protocol.state.x_mm
        y = self._protocol.state.y_mm
        s = self._protocol.state
        if tag == 'xmin':
            s.soft_x_min = x; s.x_min_set = True
        elif tag == 'xmax':
            s.soft_x_max = x; s.x_max_set = True
        elif tag == 'ymin':
            s.soft_y_min = y; s.y_min_set = True
        elif tag == 'ymax':
            s.soft_y_max = y; s.y_max_set = True
        s.soft_limit_enabled = True
        self._save_limits()
        self._sync_limit_display()
        self._canvas.set_soft_limits(True, s.soft_x_min, s.soft_x_max, s.soft_y_min, s.soft_y_max, s.x_min_set, s.x_max_set, s.y_min_set, s.y_max_set)
        names = {'xmin': '左', 'xmax': '右', 'ymin': '下', 'ymax': '上'}
        self._monitor.append_info(
            f"限位 设{names.get(tag,tag)} = {x if 'x' in tag else y:.1f}mm | "
            f"当前范围 X:[{s.soft_x_min:.0f},{s.soft_x_max:.0f}] Y:[{s.soft_y_min:.0f},{s.soft_y_max:.0f}]")

    def _on_limit_toggle(self, enabled: bool):
        s = self._protocol.state
        if enabled:
            set_count = sum([s.x_min_set, s.x_max_set, s.y_min_set, s.y_max_set])
            if set_count == 0:
                self._monitor.append_info("提示: 请先用JOG走至限位点, 点[设X-/X+/Y-/Y+]标定限位")
        s.soft_limit_enabled = enabled
        self._save_limits()
        self._sync_limit_display()
        if enabled and s._soft_limits_valid() and s._soft_limits_range_valid():
            self._canvas.set_soft_limits(enabled, s.soft_x_min, s.soft_x_max,
                s.soft_y_min, s.soft_y_max, s.x_min_set, s.x_max_set, s.y_min_set, s.y_max_set)
        else:
            self._canvas.set_soft_limits(False, -HALF_TRAVEL, HALF_TRAVEL, -HALF_TRAVEL, HALF_TRAVEL)
            if enabled and s._soft_limits_valid():
                self._monitor.append_info("限位范围无效: 请清除后按原点重新标定")
        self._monitor.append_info(f"电子限位: {'启用' if enabled else '禁用'}")

    def _on_limit_reset(self):
        self._protocol.state.reset_soft_limits()
        self._save_limits()
        self._sync_limit_display()
        self._canvas.set_soft_limits(False, -HALF_TRAVEL, HALF_TRAVEL, -HALF_TRAVEL, HALF_TRAVEL)
        self._monitor.append_info("电子限位已清除")

    def _on_limit_center(self):
        """设限位中心为原点: 计算几何中心 → G00移动到位 → G92设原点"""
        s = self._protocol.state
        if not s.soft_limit_enabled or not s._soft_limits_valid():
            self._monitor.append_info("请先完整标定四个限位边界")
            return
        cx = (s.soft_x_min + s.soft_x_max) / 2
        cy = (s.soft_y_min + s.soft_y_max) / 2
        self._send_g00(cx, cy)
        # G00移动后设原点
        self._send_g92(0, 0)
        self._control_panel.set_position(0, 0)
        self._canvas.clear_target()
        self._monitor.append_info(f"限位中心({cx:.1f}, {cy:.1f})已设为原点")

    def _on_soft_limit_hit(self):
        self._statusbar.showMessage("已到达电子限位边界", 2000)

    def _sync_limit_display(self):
        s = self._protocol.state
        self._control_panel.update_limit_display(
            s.soft_limit_enabled, s.soft_x_min, s.soft_x_max,
            s.soft_y_min, s.soft_y_max,
            s.x_min_set, s.x_max_set, s.y_min_set, s.y_max_set)

    def _load_limits(self):
        try:
            if os.path.exists(LIMITS_FILE):
                with open(LIMITS_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                s = self._protocol.state
                s.soft_limit_enabled = d.get('enabled', False)
                s.soft_x_min = d.get('x_min', -HALF_TRAVEL)
                s.soft_x_max = d.get('x_max', HALF_TRAVEL)
                s.soft_y_min = d.get('y_min', -HALF_TRAVEL)
                s.soft_y_max = d.get('y_max', HALF_TRAVEL)
                s.x_min_set = d.get('x_min_set', False)
                s.x_max_set = d.get('x_max_set', False)
                s.y_min_set = d.get('y_min_set', False)
                s.y_max_set = d.get('y_max_set', False)
                if s.soft_limit_enabled and not s._soft_limits_range_valid():
                    s.soft_limit_enabled = False
                self._sync_limit_display()
                self._canvas.set_soft_limits(s.soft_limit_enabled and s._soft_limits_range_valid(),
                    s.soft_x_min, s.soft_x_max, s.soft_y_min, s.soft_y_max,
                    s.x_min_set, s.x_max_set, s.y_min_set, s.y_max_set)
        except Exception:
            pass

    def _save_limits(self):
        try:
            s = self._protocol.state
            d = {
                'enabled': s.soft_limit_enabled,
                'x_min': s.soft_x_min, 'x_max': s.soft_x_max,
                'y_min': s.soft_y_min, 'y_max': s.soft_y_max,
                'x_min_set': s.x_min_set, 'x_max_set': s.x_max_set,
                'y_min_set': s.y_min_set, 'y_max_set': s.y_max_set,
            }
            with open(LIMITS_FILE, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2)
        except Exception:
            pass

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "十字滑台控制系统 v1.1\n\n"
            "基于 STM32F103ZET6 + Nidec DA2Z123 伺服驱动器\n"
            "通信协议: G-code over UART (115200, 8N1)\n\n"
            "坐标系: 居中四象限, 原点=滑台中心\n"
            "行程: X/Y = ±350 mm\n\n"
            "功能:\n"
            "• XY坐标平面交互式点击定位\n"
            "• G00/G01 绝对定位\n"
            "• JOG 点动控制\n"
            "• G28 自动归零\n"
            "• M03/M05 伺服开关\n"
            "• 实时串口监视\n"
        )

    def closeEvent(self, event):
        self._serial.disconnect()
        super().closeEvent(event)
