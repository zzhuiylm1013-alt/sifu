"""交互式XY坐标平面 — 原点居中, 四象限 ±350mm, 十字坐标轴"""
import math

from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
    QTransform, QCursor, QFontMetrics,
)
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsPathItem,
)


HALF = 350.0
FULL = 700.0


class XYCanvas(QGraphicsView):
    """XY坐标平面 — 原点在中心, 十字坐标轴, 覆盖四象限"""

    point_clicked = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._margin = 55
        self._current_x = 0.0
        self._current_y = 0.0
        self._target_x: float | None = None
        self._target_y: float | None = None
        self._plot_rect = QRectF()

        self._setup_scene()
        self._setup_view()
        self._create_static_elements()
        self._create_dynamic_elements()

    def _setup_scene(self):
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )

    def _setup_view(self):
        self.setStyleSheet("border: 1px solid #1e3a5f; background-color: #080c15;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._zoom_level = 0
        self._zoom_factors = [0.5, 0.6, 0.75, 0.9, 1.0, 1.15, 1.35, 1.6, 1.9, 2.3, 2.8, 3.5]

    # ── 静态元素 ──

    def _create_static_elements(self):
        pen_limit = QPen(QColor("#2a5070"), 1, Qt.PenStyle.DashLine)
        self._limit_rect = QGraphicsRectItem()
        self._limit_rect.setPen(pen_limit)
        self._limit_rect.setZValue(0)
        self._scene.addItem(self._limit_rect)

        self._grid_lines: list[QGraphicsLineItem] = []
        self._grid_labels: list[QGraphicsTextItem] = []
        self._axis_items: list = []
        self._soft_limit_rect: QGraphicsRectItem | None = None
        self._soft_limit_dots: list[QGraphicsEllipseItem] = []
        self._soft_x_min = -HALF
        self._soft_x_max = HALF
        self._soft_y_min = -HALF
        self._soft_y_max = HALF
        self._soft_limit_visible = False
        self._soft_x_min_set = self._soft_x_max_set = False
        self._soft_y_min_set = self._soft_y_max_set = False

    def _make_arrow_head(self, tip: QPointF, direction: str, size: float = 8.0) -> list[QGraphicsLineItem]:
        """用两条线段组成箭头 (避免 QPolygonF 在 PyInstaller+Python3.13 下的崩溃)"""
        if direction == 'right':
            return [
                QGraphicsLineItem(tip.x(), tip.y(), tip.x() - size * 2, tip.y() - size),
                QGraphicsLineItem(tip.x(), tip.y(), tip.x() - size * 2, tip.y() + size),
            ]
        elif direction == 'up':
            return [
                QGraphicsLineItem(tip.x(), tip.y(), tip.x() - size, tip.y() + size * 2),
                QGraphicsLineItem(tip.x(), tip.y(), tip.x() + size, tip.y() + size * 2),
            ]
        return []

    def _add_arrow(self, tip: QPointF, direction: str, color: QColor, z: int = 2):
        """添加箭头到场景"""
        pen = QPen(color, 1.8)
        for line in self._make_arrow_head(tip, direction):
            line.setPen(pen)
            line.setZValue(z)
            self._scene.addItem(line)
            self._axis_items.append(line)

    def _build_axes(self):
        """绘制醒目的十字坐标轴 (带箭头和标签)"""
        for item in self._axis_items:
            self._scene.removeItem(item)
        self._axis_items.clear()

        r = self._plot_rect
        if r.width() < 1:
            return
        center = r.center()

        pen_axis = QPen(QColor("#3a70a0"), 1.8)
        arrow_size = 8.0

        # ── X 轴 水平线 ──
        x_line = QGraphicsLineItem(r.left() + 4, center.y(), r.right() - 4, center.y())
        x_line.setPen(pen_axis)
        x_line.setZValue(2)
        self._scene.addItem(x_line)
        self._axis_items.append(x_line)

        # X轴正方向箭头 (线段构成, 避免QPolygonF)
        x_tip = QPointF(r.right() - 4, center.y())
        self._add_arrow(x_tip, 'right', QColor("#3a70a0"), z=2)

        # X 轴标签
        x_lbl = QGraphicsTextItem("X")
        x_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        x_lbl.setDefaultTextColor(QColor("#6dd5ed"))
        x_lbl.setPos(r.right() - 20, center.y() + 6)
        x_lbl.setZValue(3)
        self._scene.addItem(x_lbl)
        self._axis_items.append(x_lbl)

        # ── Y 轴 垂直线 ──
        y_line = QGraphicsLineItem(center.x(), r.bottom() - 4, center.x(), r.top() + 4)
        y_line.setPen(pen_axis)
        y_line.setZValue(2)
        self._scene.addItem(y_line)
        self._axis_items.append(y_line)

        # Y轴正方向箭头 (线段构成, 避免QPolygonF)
        y_tip = QPointF(center.x(), r.top() + 4)
        self._add_arrow(y_tip, 'up', QColor("#3a70a0"), z=2)

        # Y 轴标签
        y_lbl = QGraphicsTextItem("Y")
        y_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        y_lbl.setDefaultTextColor(QColor("#6dd5ed"))
        y_lbl.setPos(center.x() + 10, r.top() + 2)
        y_lbl.setZValue(3)
        self._scene.addItem(y_lbl)
        self._axis_items.append(y_lbl)

        # ── 原点圆点 ──
        origin_dot = QGraphicsEllipseItem(-3, -3, 6, 6)
        origin_dot.setPos(center)
        origin_dot.setPen(QPen(QColor(0, 0, 0, 0)))  # 透明笔 (避免Qt.PenStyle.NoPen在PyInstaller+Py3.13崩溃)
        origin_dot.setBrush(QBrush(QColor("#6dd5ed")))
        origin_dot.setZValue(3)
        self._scene.addItem(origin_dot)
        self._axis_items.append(origin_dot)

        # 原点 "0" 标签
        o_lbl = QGraphicsTextItem("0")
        o_lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        o_lbl.setDefaultTextColor(QColor("#6dd5ed"))
        o_lbl.setPos(center.x() - 16, center.y() + 6)
        o_lbl.setZValue(3)
        self._scene.addItem(o_lbl)
        self._axis_items.append(o_lbl)

    def _build_grid(self):
        for item in self._grid_lines + self._grid_labels:
            self._scene.removeItem(item)
        self._grid_lines.clear()
        self._grid_labels.clear()

        rect = self._plot_rect
        if rect.width() < 1 or rect.height() < 1:
            return

        candidates = [100, 50, 25, 10, 5]
        step = 100
        for c in candidates:
            if FULL / c >= 5:
                step = c
                break

        pen_grid = QPen(QColor("#0f2840"), 0.5)
        pen_sub = QPen(QColor("#0a1c30"), 0.3)
        font = QFont("Consolas", 8)
        fm = QFontMetrics(font)

        # 竖线
        v = -HALF
        while v <= HALF + 0.01:
            px = rect.left() + ((v + HALF) / FULL) * rect.width()
            is_axis = abs(v) < 0.01
            is_main = int(v) % step == 0
            if is_axis:
                v += step if is_main else (step / (5 if step >= 25 else 4))
                continue
            pen = pen_grid if is_main else pen_sub
            line = QGraphicsLineItem(px, rect.top(), px, rect.bottom())
            line.setPen(pen)
            line.setZValue(0)
            self._scene.addItem(line)
            self._grid_lines.append(line)
            if is_main:
                label = QGraphicsTextItem(f"{int(v)}")
                label.setFont(font)
                label.setDefaultTextColor(QColor("#2a5070"))
                label.setPos(px - fm.horizontalAdvance(f"{int(v)}") / 2, rect.bottom() + 4)
                label.setZValue(1)
                self._scene.addItem(label)
                self._grid_labels.append(label)
            v += step if is_main else (step / (5 if step >= 25 else 4))

        # 横线
        h = -HALF
        while h <= HALF + 0.01:
            py = rect.bottom() - ((h + HALF) / FULL) * rect.height()
            is_axis = abs(h) < 0.01
            is_main = int(h) % step == 0
            if is_axis:
                h += step if is_main else (step / (5 if step >= 25 else 4))
                continue
            pen = pen_grid if is_main else pen_sub
            line = QGraphicsLineItem(rect.left(), py, rect.right(), py)
            line.setPen(pen)
            line.setZValue(0)
            self._scene.addItem(line)
            self._grid_lines.append(line)
            if is_main:
                label = QGraphicsTextItem(f"{int(h)}")
                label.setFont(font)
                label.setDefaultTextColor(QColor("#2a5070"))
                label.setPos(rect.left() - fm.horizontalAdvance(f"{int(h)}") - 6, py - 8)
                label.setZValue(1)
                self._scene.addItem(label)
                self._grid_labels.append(label)
            h += step if is_main else (step / (5 if step >= 25 else 4))

    # ── 动态元素 ──

    def _create_dynamic_elements(self):
        # 当前位置光标
        pen_pos = QPen(QColor("#4aff9e"), 2)
        self._pos_h = QGraphicsLineItem()
        self._pos_h.setPen(pen_pos)
        self._pos_h.setZValue(6)
        self._scene.addItem(self._pos_h)
        self._pos_v = QGraphicsLineItem()
        self._pos_v.setPen(pen_pos)
        self._pos_v.setZValue(6)
        self._scene.addItem(self._pos_v)
        self._pos_dot = QGraphicsEllipseItem(-5, -5, 10, 10)
        self._pos_dot.setPen(QPen(QColor("#4aff9e"), 2))
        self._pos_dot.setBrush(QBrush(QColor(0, 255, 100, 60)))
        self._pos_dot.setZValue(7)
        self._scene.addItem(self._pos_dot)

        self._pos_label = QGraphicsTextItem()
        self._pos_label.setFont(QFont("Consolas", 9))
        self._pos_label.setDefaultTextColor(QColor("#4aff9e"))
        self._pos_label.setZValue(8)
        self._scene.addItem(self._pos_label)

        # 目标标记
        self._target_dot = QGraphicsEllipseItem(-7, -7, 14, 14)
        self._target_dot.setPen(QPen(QColor("#ff6b35"), 2))
        self._target_dot.setBrush(QBrush(QColor(255, 107, 53, 40)))
        self._target_dot.setZValue(6)
        self._target_dot.setVisible(False)
        self._scene.addItem(self._target_dot)

        pen_path = QPen(QColor("#ff6b35"), 1, Qt.PenStyle.DashLine)
        self._path_line = QGraphicsLineItem()
        self._path_line.setPen(pen_path)
        self._path_line.setZValue(4)
        self._path_line.setVisible(False)
        self._scene.addItem(self._path_line)

        self._hint = QGraphicsTextItem()
        self._hint.setFont(QFont("Consolas", 9))
        self._hint.setDefaultTextColor(QColor("#b0c4de"))
        self._hint.setZValue(10)
        self._scene.addItem(self._hint)

    # ── 坐标转换 ──

    def _to_pixel(self, x_mm: float, y_mm: float) -> QPointF:
        r = self._plot_rect
        px = r.center().x() + (x_mm / HALF) * (r.width() / 2)
        py = r.center().y() - (y_mm / HALF) * (r.height() / 2)
        return QPointF(px, py)

    def _to_mm(self, px: float, py: float) -> tuple[float, float]:
        r = self._plot_rect
        if r.width() < 1 or r.height() < 1:
            return 0.0, 0.0
        x = ((px - r.center().x()) / (r.width() / 2)) * HALF
        y = ((r.center().y() - py) / (r.height() / 2)) * HALF
        x = max(-HALF, min(x, HALF))
        y = max(-HALF, min(y, HALF))
        return x, y

    # ── 电子限位矩形 ──

    def set_soft_limits(self, enabled: bool, x_min: float, x_max: float,
                        y_min: float, y_max: float, x_min_set=False, x_max_set=False,
                        y_min_set=False, y_max_set=False):
        self._soft_limit_visible = enabled
        self._soft_x_min_set, self._soft_x_max_set = x_min_set, x_max_set
        self._soft_y_min_set, self._soft_y_max_set = y_min_set, y_max_set
        # 绘制用: 未标定的限位用0(原点)代替, 红框出现在正确象限
        self._soft_x_min = x_min if x_min_set else 0.0
        self._soft_x_max = x_max if x_max_set else 0.0
        self._soft_y_min = y_min if y_min_set else 0.0
        self._soft_y_max = y_max if y_max_set else 0.0
        self._draw_soft_limit()

    def _draw_soft_limit(self):
        if self._soft_limit_rect:
            self._scene.removeItem(self._soft_limit_rect)
            self._soft_limit_rect = None
        for dot in self._soft_limit_dots:
            self._scene.removeItem(dot)
        self._soft_limit_dots.clear()
        if not self._soft_limit_visible:
            return
        if self._plot_rect.width() < 1:
            return
        # ── 限位标记点 (坐标轴上的小红点) ──
        dot_pen = QPen(QColor("#ff4444"), 2)
        dot_brush = QBrush(QColor(255, 68, 68, 180))
        # 四个限位方向 → 坐标轴上的标记点
        markers = [
            (self._soft_x_min, 0, self._soft_x_min_set),
            (self._soft_x_max, 0, self._soft_x_max_set),
            (0, self._soft_y_min, self._soft_y_min_set),
            (0, self._soft_y_max, self._soft_y_max_set),
        ]
        for mx, my, is_set in markers:
            if not is_set:
                continue
            p = self._to_pixel(mx, my)
            dot = QGraphicsEllipseItem(-4, -4, 8, 8)
            dot.setPos(p)
            dot.setPen(dot_pen)
            dot.setBrush(dot_brush)
            dot.setZValue(9)
            self._scene.addItem(dot)
            self._soft_limit_dots.append(dot)

        xmin, xmax = min(self._soft_x_min, self._soft_x_max), max(self._soft_x_min, self._soft_x_max)
        ymin, ymax = min(self._soft_y_min, self._soft_y_max), max(self._soft_y_min, self._soft_y_max)
        if xmin >= xmax or ymin >= ymax:
            return
        tl = self._to_pixel(xmin, ymax)
        br = self._to_pixel(xmax, ymin)
        r = QRectF(tl, br)
        pen = QPen(QColor("#ff4444"), 2, Qt.PenStyle.DashLine)
        self._soft_limit_rect = QGraphicsRectItem(r)
        self._soft_limit_rect.setPen(pen)
        self._soft_limit_rect.setBrush(QBrush(QColor(255, 68, 68, 15)))
        self._soft_limit_rect.setZValue(1)
        self._scene.addItem(self._soft_limit_rect)

    # ── 布局 ──

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_layout()

    def _update_layout(self):
        w = self.viewport().width()
        h = self.viewport().height()
        self._plot_rect = QRectF(
            self._margin + 20, 8,
            w - self._margin - 30, h - self._margin + 4
        )
        self._scene.setSceneRect(0, 0, w, h)
        self._build_grid()
        self._build_axes()
        self._draw_soft_limit()
        self._limit_rect.setRect(self._plot_rect)
        self._update_positions()

    def _update_positions(self):
        cp = self._to_pixel(self._current_x, self._current_y)
        cross_len = 20
        self._pos_h.setLine(cp.x() - cross_len, cp.y(), cp.x() + cross_len, cp.y())
        self._pos_v.setLine(cp.x(), cp.y() - cross_len, cp.x(), cp.y() + cross_len)
        self._pos_dot.setPos(cp)
        self._pos_label.setPlainText(f"({self._current_x:.1f}, {self._current_y:.1f})")
        self._pos_label.setPos(cp.x() + 14, cp.y() - 20)

        if self._target_x is not None:
            tp = self._to_pixel(self._target_x, self._target_y)
            self._target_dot.setPos(tp)
            self._target_dot.setVisible(True)
            self._path_line.setLine(cp.x(), cp.y(), tp.x(), tp.y())
            self._path_line.setVisible(True)
        else:
            self._target_dot.setVisible(False)
            self._path_line.setVisible(False)

    def update_position(self, x_mm: float, y_mm: float):
        self._current_x = x_mm
        self._current_y = y_mm
        self._update_positions()

    def set_target(self, x_mm: float, y_mm: float):
        self._target_x = x_mm
        self._target_y = y_mm
        self._update_positions()

    def clear_target(self):
        self._target_x = None
        self._target_y = None
        self._update_positions()

    # ── 鼠标交互 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            x, y = self._to_mm(pos.x(), pos.y())
            if self._plot_rect.contains(pos):
                self.set_target(x, y)
                self.point_clicked.emit(x, y)
        elif event.button() == Qt.MouseButton.RightButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        if self._plot_rect.contains(pos):
            x, y = self._to_mm(pos.x(), pos.y())
            self._hint.setPlainText(f"X={x:.1f}  Y={y:.1f}")
            self._hint.setPos(pos.x() + 15, pos.y() - 20)
            self._hint.setVisible(True)
        else:
            self._hint.setVisible(False)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        delta = 1 if event.angleDelta().y() > 0 else -1
        new_level = max(0, min(len(self._zoom_factors) - 1, self._zoom_level + delta))
        if new_level != self._zoom_level:
            self._zoom_level = new_level
            factor = self._zoom_factors[self._zoom_level]
            t = QTransform().scale(factor, factor)
            self.setTransform(t)
