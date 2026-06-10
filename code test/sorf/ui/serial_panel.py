"""串口设置面板 — COM口选择、波特率、连接控制"""
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QGroupBox, QPushButton, QLabel, QComboBox,
)


class SerialPanel(QWidget):
    """串口设置面板"""

    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    refresh_ports = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._init_ui()

        # 定时自动刷新端口列表
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._do_refresh)
        self._refresh_timer.start(2000)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)

        grp = QGroupBox("串口设置")
        layout = QVBoxLayout(grp)
        layout.setSpacing(6)

        # 端口选择行
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("端口:"))
        self._combo_port = QComboBox()
        self._combo_port.setMinimumWidth(100)
        self._combo_port.setEditable(False)
        row1.addWidget(self._combo_port, 1)

        self._btn_refresh = QPushButton("刷新")
        self._btn_refresh.setMinimumWidth(56)
        row1.addWidget(self._btn_refresh)
        layout.addLayout(row1)

        # 波特率
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("波特率:"))
        self._combo_baud = QComboBox()
        self._combo_baud.addItems([
            "9600", "19200", "38400", "57600", "115200",
            "230400", "460800", "921600"
        ])
        self._combo_baud.setCurrentText("115200")
        row2.addWidget(self._combo_baud, 1)
        layout.addLayout(row2)

        # 连接按钮 + 状态灯
        row3 = QHBoxLayout()
        self._btn_connect = QPushButton("连接")
        self._btn_connect.setMinimumHeight(30)
        row3.addWidget(self._btn_connect, 1)

        self._led = QLabel("●")
        self._led.setStyleSheet("color: #555; font-size: 20px;")
        self._led.setMinimumWidth(28)
        row3.addWidget(self._led)

        self._label_status = QLabel("未连接")
        self._label_status.setStyleSheet("color: #666;")
        row3.addWidget(self._label_status)
        layout.addLayout(row3)

        main_layout.addWidget(grp)

        # 信号
        self._btn_connect.clicked.connect(self._on_connect_clicked)
        self._btn_refresh.clicked.connect(self._do_refresh)

    def _on_connect_clicked(self):
        if self._connected:
            self.disconnect_requested.emit()
        else:
            port = self._combo_port.currentText()
            baud = int(self._combo_baud.currentText())
            if port:
                self.connect_requested.emit(port, baud)

    def _do_refresh(self):
        self.refresh_ports.emit()

    def update_port_list(self, ports: list[str]):
        current = self._combo_port.currentText()
        self._combo_port.blockSignals(True)
        self._combo_port.clear()
        if ports:
            self._combo_port.addItems(ports)
            if current in ports:
                self._combo_port.setCurrentText(current)
        else:
            self._combo_port.addItem("(无可用串口)")
        self._combo_port.blockSignals(False)

    def set_connected(self, connected: bool):
        self._connected = connected
        if connected:
            self._btn_connect.setText("断开")
            self._btn_connect.setStyleSheet(
                "QPushButton { color: #ff4a4a; border-color: #8e1a1a; }"
                "QPushButton:hover { border-color: #ff3030; }"
            )
            self._led.setStyleSheet("color: #4aff9e; font-size: 20px;")
            self._label_status.setText("已连接")
            self._label_status.setStyleSheet("color: #4aff9e;")
            self._combo_port.setEnabled(False)
            self._combo_baud.setEnabled(False)
        else:
            self._btn_connect.setText("连接")
            self._btn_connect.setStyleSheet("")
            self._led.setStyleSheet("color: #555; font-size: 20px;")
            self._label_status.setText("未连接")
            self._label_status.setStyleSheet("color: #666;")
            self._combo_port.setEnabled(True)
            self._combo_baud.setEnabled(True)
