"""串口管理器 — 枚举、连接、异步收发"""
import re
import time
import threading
from dataclasses import dataclass

import serial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal


@dataclass
class SerialConfig:
    port: str = ""
    baudrate: int = 115200
    bytesize: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stopbits: int = serial.STOPBITS_ONE
    timeout: float = 0.02


class SerialScanner:
    """扫描系统可用串口"""

    @staticmethod
    def list_ports() -> list[str]:
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    @staticmethod
    def list_ports_with_desc() -> list[tuple[str, str]]:
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]


class _ReceiveThread(QThread):
    """后台接收线程 — 持续读取串口数据，按行解析后通过信号发出"""
    line_received = pyqtSignal(str)

    def __init__(self, ser: serial.Serial):
        super().__init__()
        self._serial = ser
        self._running = False
        self._buffer = b""
        self._lock = threading.Lock()

    def run(self):
        self._running = True
        while self._running:
            try:
                if self._serial.in_waiting:
                    with self._lock:
                        data = self._serial.read(self._serial.in_waiting)
                    self._buffer += data
                    while b"\n" in self._buffer:
                        line, self._buffer = self._buffer.split(b"\n", 1)
                        text = line.decode("utf-8", errors="replace").strip()
                        if text:
                            self.line_received.emit(text)
                else:
                    time.sleep(0.005)
            except (serial.SerialException, OSError):
                self._running = False
                break

    def stop(self):
        self._running = False
        self.wait(500)


class SerialManager(QThread):
    """串口管理器 — 封装连接/断开/发送，通过信号通知上层"""

    connected = pyqtSignal(bool)
    line_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._serial: serial.Serial | None = None
        self._config = SerialConfig()
        self._rx_thread: _ReceiveThread | None = None
        self._running = False
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def config(self) -> SerialConfig:
        return self._config

    def scan_ports(self) -> list[str]:
        return SerialScanner.list_ports()

    def scan_ports_with_desc(self) -> list[tuple[str, str]]:
        return SerialScanner.list_ports_with_desc()

    def set_config(self, port: str, baudrate: int = 115200):
        self._config.port = port
        self._config.baudrate = baudrate

    def connect(self, port: str = "", baudrate: int = 115200) -> bool:
        if self._is_connected:
            self.disconnect()

        if port:
            self._config.port = port
        if baudrate:
            self._config.baudrate = baudrate

        if not self._config.port:
            self.error_occurred.emit("未选择串口")
            return False

        try:
            self._serial = serial.Serial(
                port=self._config.port,
                baudrate=self._config.baudrate,
                bytesize=self._config.bytesize,
                parity=self._config.parity,
                stopbits=self._config.stopbits,
                timeout=self._config.timeout,
            )
            self._is_connected = True

            self._rx_thread = _ReceiveThread(self._serial)
            self._rx_thread.line_received.connect(self._on_line)
            self._rx_thread.start()

            self.connected.emit(True)
            return True
        except serial.SerialException as e:
            self._is_connected = False
            self.error_occurred.emit(f"串口连接失败: {e}")
            return False

    def disconnect(self):
        self._is_connected = False
        if self._rx_thread:
            self._rx_thread.stop()
            self._rx_thread = None
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except serial.SerialException:
                pass
        self._serial = None
        self.connected.emit(False)

    def send(self, text: str):
        if self._serial and self._serial.is_open:
            try:
                if not text.endswith("\n"):
                    text += "\n"
                self._serial.write(text.encode("utf-8"))
                self._serial.flush()
            except serial.SerialException as e:
                self.error_occurred.emit(f"发送失败: {e}")

    def sendf(self, fmt: str, *args):
        self.send(fmt % args)

    def _on_line(self, line: str):
        self.line_received.emit(line)

    def stop(self):
        self.disconnect()
        self._running = False
