"""科技感深色主题 QSS 样式表"""

DARK_THEME = """
/* ── 全局 ── */
QWidget {
    background-color: #0a0e17;
    color: #b0c4de;
    font-family: "Microsoft YaHei", "微软雅黑", "SimHei", sans-serif;
    font-size: 13px;
    border: none;
}

QMainWindow {
    background-color: #0a0e17;
}

/* ── 菜单栏 ── */
QMenuBar {
    background-color: #111827;
    color: #6dd5ed;
    border-bottom: 1px solid #1e3a5f;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #1a3a5c;
    border-radius: 3px;
}
QMenu {
    background-color: #111827;
    border: 1px solid #1e3a5f;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
}
QMenu::item:selected {
    background-color: #1a3a5c;
    color: #6dd5ed;
}

/* ── 状态栏 ── */
QStatusBar {
    background-color: #111827;
    color: #6dd5ed;
    border-top: 1px solid #1e3a5f;
    font-size: 12px;
}

/* ── 分组框 / 面板 ── */
QGroupBox {
    background-color: #0d1525;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
    color: #6dd5ed;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #6dd5ed;
    background-color: #0d1525;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
}

/* ── 按钮通用 ── */
QPushButton {
    background-color: #132238;
    color: #6dd5ed;
    border: 1px solid #1e4a6e;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #1a3a5c;
    border-color: #3a8fc2;
}
QPushButton:pressed {
    background-color: #0d2238;
}
QPushButton:disabled {
    background-color: #0d1520;
    color: #3a5068;
    border-color: #1a2940;
}

/* ── 主要操作按钮 (绿色调) ── */
QPushButton#btnRun, QPushButton[primary="true"] {
    background-color: #0d3320;
    color: #4aff9e;
    border-color: #1a6e3e;
    font-weight: bold;
}
QPushButton#btnRun:hover, QPushButton[primary="true"]:hover {
    background-color: #154a2e;
    border-color: #3aff8e;
}

/* ── 急停按钮 ── */
QPushButton#btnEstop {
    background-color: #3d1010;
    color: #ff4a4a;
    border: 2px solid #8e1a1a;
    font-weight: bold;
    font-size: 15px;
    min-height: 36px;
    border-radius: 6px;
}
QPushButton#btnEstop:hover {
    background-color: #5a1818;
    border-color: #ff3030;
}
QPushButton#btnEstop:pressed {
    background-color: #2a0808;
}

/* ── 文本输入 ── */
QLineEdit {
    background-color: #0a1220;
    color: #6dd5ed;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #1a4a7a;
}
QLineEdit:focus {
    border-color: #3a8fc2;
}

QSpinBox, QDoubleSpinBox {
    background-color: #0a1220;
    color: #6dd5ed;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3a8fc2;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #1e3a5f;
    border-bottom: 1px solid #1e3a5f;
    border-top-right-radius: 3px;
    background-color: #132238;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #1a3a5c;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #1e3a5f;
    border-bottom-right-radius: 3px;
    background-color: #132238;
}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #1a3a5c;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #6dd5ed;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6dd5ed;
}

/* ── 下拉框 ── */
QComboBox {
    background-color: #0a1220;
    color: #6dd5ed;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #3a8fc2;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #0d1525;
    border: 1px solid #1e3a5f;
    selection-background-color: #1a3a5c;
    color: #b0c4de;
}

/* ── 标签 ── */
QLabel {
    background: transparent;
}
QLabel#title {
    color: #6dd5ed;
    font-size: 16px;
    font-weight: bold;
}
QLabel#value {
    color: #4aff9e;
    font-size: 14px;
    font-weight: bold;
    font-family: "Consolas", "Microsoft YaHei", monospace;
}

/* ── 滑动条 ── */
QSlider::groove:horizontal {
    background: #0a1220;
    height: 6px;
    border-radius: 3px;
    border: 1px solid #1e3a5f;
}
QSlider::handle:horizontal {
    background: #3a8fc2;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #1a4a7a;
    border-radius: 3px;
}

/* ── 滚动条 ── */
QScrollBar:vertical {
    background: #0a1220;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #1e3a5f;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #3a8fc2;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0a1220;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #1e3a5f;
    min-width: 30px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── 文本编辑器 ── */
QPlainTextEdit, QTextEdit {
    background-color: #0a1018;
    color: #78c0a8;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 6px;
    font-family: "Consolas", "Microsoft YaHei", monospace;
    font-size: 12px;
}

/* ── 标签页 ── */
QTabWidget::pane {
    background-color: #0d1525;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #0a1220;
    color: #6dd5ed;
    border: 1px solid #1e3a5f;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #132238;
    border-bottom: 2px solid #3a8fc2;
}
QTabBar::tab:hover {
    background-color: #1a3a5c;
}

/* ── 列表控件 ── */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #0a1220;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    alternate-background-color: #0d1828;
}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #1a3a5c;
    color: #6dd5ed;
}

/* ── 复选框 ── */
QCheckBox {
    spacing: 6px;
    color: #b0c4de;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #1e3a5f;
    border-radius: 3px;
    background-color: #0a1220;
}
QCheckBox::indicator:checked {
    background-color: #1a4a7a;
    border-color: #3a8fc2;
}

/* ── 工具提示 ── */
QToolTip {
    background-color: #111827;
    color: #6dd5ed;
    border: 1px solid #3a8fc2;
    padding: 4px;
    border-radius: 3px;
}

/* ── 分割线 ── */
QFrame[frameShape="4"] {
    color: #1e3a5f;
}
"""

# 日志颜色配置 (用于监视器HTML着色)
LOG_COLORS = {
    "TX": "#4aff9e",   # 发送 — 青色
    "RX": "#6dd5ed",   # 接收 — 蓝色
    "TS": "#3a5068",   # 时间戳 — 灰色
}
