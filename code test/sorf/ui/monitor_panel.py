"""串口监视器 — 实时显示收发数据，支持手动发送命令"""
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLineEdit, QPlainTextEdit,
)


class MonitorPanel(QWidget):
    """串口通信监视器"""

    send_manual = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._line_count = 0
        self._max_lines = 2000
        self._paused = False

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        grp = QGroupBox("串口监视器")
        inner = QVBoxLayout(grp)
        inner.setSpacing(4)

        # 控制栏
        bar = QHBoxLayout()
        self._btn_clear = QPushButton("清空")
        self._btn_clear.setMinimumWidth(56)
        bar.addWidget(self._btn_clear)
        self._btn_pause = QPushButton("暂停")
        self._btn_pause.setMinimumWidth(56)
        self._btn_pause.setCheckable(True)
        bar.addWidget(self._btn_pause)
        bar.addStretch()
        inner.addLayout(bar)

        # 日志区域
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(5000)
        self._log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        inner.addWidget(self._log)

        # 手动发送栏
        send_layout = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("输入手动命令 (如 G00 X=100 Y=100)")
        self._input.returnPressed.connect(self._on_send)
        send_layout.addWidget(self._input, 1)
        self._btn_send = QPushButton("发送")
        self._btn_send.setMinimumWidth(66)
        send_layout.addWidget(self._btn_send)
        inner.addLayout(send_layout)

        layout.addWidget(grp)

        # 连接
        self._btn_clear.clicked.connect(self._log.clear)
        self._btn_pause.toggled.connect(self._on_pause)
        self._btn_send.clicked.connect(self._on_send)

    def _on_send(self):
        text = self._input.text().strip()
        if text:
            self.send_manual.emit(text)
            self._input.clear()

    def _on_pause(self, paused: bool):
        self._paused = paused
        self._btn_pause.setText("继续" if paused else "暂停")

    def append_tx(self, content: str):
        """添加发送记录"""
        if self._paused:
            return
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._append_html(f'<span style="color:#3a5068">[{ts}]</span> '
                          f'<span style="color:#4aff9e">TX →</span> '
                          f'<span style="color:#78c0a8">{content}</span>')

    def append_rx(self, content: str):
        """添加接收记录"""
        if self._paused:
            return
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._append_html(f'<span style="color:#3a5068">[{ts}]</span> '
                          f'<span style="color:#6dd5ed">RX ←</span> '
                          f'<span style="color:#b0c4de">{content}</span>')

    def append_info(self, content: str):
        """添加信息记录"""
        if self._paused:
            return
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._append_html(f'<span style="color:#3a5068">[{ts}]</span> '
                          f'<span style="color:#ffb347">** {content}</span>')

    def _append_html(self, html: str):
        self._log.appendHtml(html)
        # 自动滚动到底部
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log.setTextCursor(cursor)
