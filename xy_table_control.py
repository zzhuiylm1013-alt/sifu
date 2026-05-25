#!/usr/bin/env python3
"""XY 十字滑台控制软件
STM32F103ZET6 + Nidec DA2Z123 伺服系统
"""

import threading
import time
import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports


class XYTableApp:
    """XY 十字滑台控制软件"""

    def __init__(self):
        self.root = ttk.Window(
            title="XY 十字滑台控制器",
            themename="cosmo",
            size=(1200, 780),
            resizable=(True, True),
        )
        self.root.place_window_center()

        self.ser = None
        self.connected = False
        self.running = True

        self.pos_x = 0.0
        self.pos_y = 0.0
        self.trail = []
        self.max_trail = 500

        self.canvas_w = 500
        self.canvas_h = 500
        self.margin = 40
        self.scale = 0.4

        self._build_ui()
        self.rx_thread = None
        self._update_canvas()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI 构建 ────────────────────────────────────────────────

    def _build_ui(self):
        self._build_top_bar()

        main = ttk.Frame(self.root, padding=5)
        main.pack(fill=BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True)

        right = ttk.Frame(main, width=380)
        right.pack(side=RIGHT, fill=Y, padx=(10, 0))

        self._build_canvas(left)
        self._build_status_bar(left)
        self._build_control_panel(right)
        self._build_log_panel(right)

    def _build_top_bar(self):
        bar = ttk.Frame(self.root, padding=(10, 8))
        bar.pack(fill=X)

        ttk.Label(
            bar, text="XY 十字滑台控制器",
            font=("Microsoft YaHei", 14, "bold"),
            bootstyle="primary",
        ).pack(side=LEFT, padx=(0, 20))

        ttk.Separator(bar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        ttk.Label(bar, text="串口:").pack(side=LEFT, padx=(10, 2))
        self.combo_port = ttk.Combobox(bar, width=10, state="readonly")
        self.combo_port.pack(side=LEFT, padx=2)

        ttk.Label(bar, text="波特率:").pack(side=LEFT, padx=(10, 2))
        self.combo_baud = ttk.Combobox(
            bar, width=8, state="readonly",
            values=["9600", "19200", "38400", "57600", "115200", "230400"],
        )
        self.combo_baud.set("115200")
        self.combo_baud.pack(side=LEFT, padx=2)

        self.btn_refresh = ttk.Button(
            bar, text="刷新", bootstyle="info-outline",
            command=self._refresh_ports, width=6,
        )
        self.btn_refresh.pack(side=LEFT, padx=(10, 2))

        self.btn_connect = ttk.Button(
            bar, text="连接", bootstyle="success",
            command=self._toggle_connection, width=8,
        )
        self.btn_connect.pack(side=LEFT, padx=2)

        self.lbl_conn_status = ttk.Label(
            bar, text="未连接", bootstyle="danger",
            font=("Microsoft YaHei", 10),
        )
        self.lbl_conn_status.pack(side=LEFT, padx=(15, 0))

        self._refresh_ports()

    def _build_canvas(self, parent):
        frame = ttk.LabelFrame(parent, text="XY 工作区")
        frame.pack(fill=BOTH, expand=True)

        self.canvas = tk.Canvas(
            frame, bg="#1a1a2e", highlightthickness=0,
            width=self.canvas_w, height=self.canvas_h,
        )
        self.canvas.pack(fill=BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._canvas_click)

        self.root.after(100, self._draw_grid)

    def _build_status_bar(self, parent):
        frame = ttk.Frame(parent, padding=(5, 5))
        frame.pack(fill=X)

        pos_frame = ttk.LabelFrame(frame, text="当前坐标")
        pos_frame.pack(side=LEFT, fill=X, expand=True)

        self.lbl_x = ttk.Label(
            pos_frame, text="X: 0.000 mm",
            font=("Consolas", 12, "bold"), bootstyle="info",
        )
        self.lbl_x.pack(side=LEFT, padx=10)

        self.lbl_y = ttk.Label(
            pos_frame, text="Y: 0.000 mm",
            font=("Consolas", 12, "bold"), bootstyle="info",
        )
        self.lbl_y.pack(side=LEFT, padx=10)

        srv_frame = ttk.LabelFrame(frame, text="伺服状态")
        srv_frame.pack(side=LEFT, padx=(10, 0))

        self.lbl_servo = ttk.Label(
            srv_frame, text="---",
            font=("Microsoft YaHei", 11), bootstyle="secondary",
        )
        self.lbl_servo.pack()

    def _build_control_panel(self, parent):
        # ── 坐标移动 ──
        coord_frame = ttk.LabelFrame(parent, text="坐标移动")
        coord_frame.pack(fill=X, pady=(0, 8))

        row0 = ttk.Frame(coord_frame)
        row0.pack(fill=X, pady=2)
        ttk.Label(row0, text="X (mm):", width=8).pack(side=LEFT)
        self.entry_x = ttk.Entry(row0, width=12, font=("Consolas", 11))
        self.entry_x.insert(0, "0.000")
        self.entry_x.pack(side=LEFT, padx=5)
        ttk.Label(row0, text="Y (mm):", width=8).pack(side=LEFT)
        self.entry_y = ttk.Entry(row0, width=12, font=("Consolas", 11))
        self.entry_y.insert(0, "0.000")
        self.entry_y.pack(side=LEFT, padx=5)

        row1 = ttk.Frame(coord_frame)
        row1.pack(fill=X, pady=2)
        ttk.Label(row1, text="速度:", width=8).pack(side=LEFT)
        self.entry_speed = ttk.Entry(row1, width=12, font=("Consolas", 11))
        self.entry_speed.insert(0, "500")
        self.entry_speed.pack(side=LEFT, padx=5)
        ttk.Label(row1, text="mm/分").pack(side=LEFT)

        row2 = ttk.Frame(coord_frame)
        row2.pack(fill=X, pady=(8, 0))

        self.btn_move = ttk.Button(
            row2, text="直线移动 (G01)", bootstyle="primary",
            command=self._cmd_move, width=15,
        )
        self.btn_move.pack(side=LEFT, padx=2)

        self.btn_rapid = ttk.Button(
            row2, text="快速定位 (G00)", bootstyle="info",
            command=self._cmd_rapid, width=15,
        )
        self.btn_rapid.pack(side=LEFT, padx=2)

        # ── 安全控制 ──
        safety_frame = ttk.LabelFrame(parent, text="安全控制")
        safety_frame.pack(fill=X, pady=(0, 8))

        row_s = ttk.Frame(safety_frame)
        row_s.pack(fill=X)

        self.btn_home = ttk.Button(
            row_s, text="归零 (G28)", bootstyle="warning",
            command=self._cmd_home, width=14,
        )
        self.btn_home.pack(side=LEFT, padx=2)

        self.btn_stop = ttk.Button(
            row_s, text="紧急停止 (M112)", bootstyle="danger",
            command=self._cmd_estop, width=18,
        )
        self.btn_stop.pack(side=LEFT, padx=2)

        row_s2 = ttk.Frame(safety_frame)
        row_s2.pack(fill=X, pady=(6, 0))

        self.btn_servo_on = ttk.Button(
            row_s2, text="伺服使能 (M03)", bootstyle="success-outline",
            command=self._cmd_servo_on, width=14,
        )
        self.btn_servo_on.pack(side=LEFT, padx=2)

        self.btn_servo_off = ttk.Button(
            row_s2, text="伺服关闭 (M05)", bootstyle="danger-outline",
            command=self._cmd_servo_off, width=14,
        )
        self.btn_servo_off.pack(side=LEFT, padx=2)

        # ── 点动控制 ──
        jog_frame = ttk.LabelFrame(parent, text="点动控制")
        jog_frame.pack(fill=X, pady=(0, 8))

        row_jog = ttk.Frame(jog_frame)
        row_jog.pack(fill=X, pady=(0, 6))
        ttk.Label(row_jog, text="步距:").pack(side=LEFT)
        self.combo_step = ttk.Combobox(
            row_jog, width=8, state="readonly",
            values=["0.01", "0.1", "0.5", "1", "5", "10", "50"],
        )
        self.combo_step.set("1")
        self.combo_step.pack(side=LEFT, padx=5)
        ttk.Label(row_jog, text="mm").pack(side=LEFT)

        btn_grid = ttk.Frame(jog_frame)
        btn_grid.pack()

        btn_style = {"width": 6, "bootstyle": "secondary"}
        ttk.Button(btn_grid, text="Y+", command=lambda: self._jog("Y+"), **btn_style).grid(
            row=0, column=1, padx=2, pady=2,
        )
        ttk.Button(btn_grid, text="X-", command=lambda: self._jog("X-"), **btn_style).grid(
            row=1, column=0, padx=2, pady=2,
        )
        ttk.Button(btn_grid, text="归零", command=self._cmd_home, **btn_style).grid(
            row=1, column=1, padx=2, pady=2,
        )
        ttk.Button(btn_grid, text="X+", command=lambda: self._jog("X+"), **btn_style).grid(
            row=1, column=2, padx=2, pady=2,
        )
        ttk.Button(btn_grid, text="Y-", command=lambda: self._jog("Y-"), **btn_style).grid(
            row=2, column=1, padx=2, pady=2,
        )

        # ── 手动指令 ──
        cmd_frame = ttk.LabelFrame(parent, text="手动指令")
        cmd_frame.pack(fill=X)

        row_cmd = ttk.Frame(cmd_frame)
        row_cmd.pack(fill=X)

        self.entry_cmd = ttk.Entry(row_cmd, font=("Consolas", 11))
        self.entry_cmd.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.entry_cmd.bind("<Return>", lambda e: self._send_manual_cmd())

        ttk.Button(
            row_cmd, text="发送", bootstyle="primary",
            command=self._send_manual_cmd, width=6,
        ).pack(side=LEFT)

    def _build_log_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="通信日志")
        frame.pack(fill=BOTH, expand=True, pady=(8, 0))

        self.log_text = ScrolledText(
            frame, height=10, font=("Consolas", 9),
            autohide=True,
        )
        self.log_text.pack(fill=BOTH, expand=True)

        row_btn = ttk.Frame(frame)
        row_btn.pack(fill=X, pady=(4, 0))
        ttk.Button(
            row_btn, text="清空日志", bootstyle="secondary-outline",
            command=self._clear_log, width=10,
        ).pack(side=RIGHT)

    # ─── 串口通信 ────────────────────────────────────────────────

    def _refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        self.combo_port["values"] = port_list
        if port_list:
            self.combo_port.set(port_list[0])

    def _toggle_connection(self):
        if self.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.combo_port.get()
        baud = int(self.combo_baud.get())
        if not port:
            messagebox.showwarning("警告", "请选择串口")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.connected = True
            self.btn_connect.configure(text="断开", bootstyle="danger")
            self.lbl_conn_status.configure(text=f"已连接: {port}", bootstyle="success")
            self._log(f"[系统] 已连接 {port} @ {baud}bps", "green")

            self.rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.rx_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"连接失败:\n{e}")

    def _disconnect(self):
        self.connected = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.btn_connect.configure(text="连接", bootstyle="success")
        self.lbl_conn_status.configure(text="未连接", bootstyle="danger")
        self._log("[系统] 已断开", "orange")

    def _send_cmd(self, cmd: str):
        if not self.connected or not self.ser:
            self._log("[错误] 未连接串口", "red")
            return
        try:
            data = (cmd.strip() + "\n").encode("ascii")
            self.ser.write(data)
            self._log(f" 发送: {cmd.strip()}", "#00bfff")
        except Exception as e:
            self._log(f"[错误] 发送失败: {e}", "red")

    def _receive_loop(self):
        while self.running and self.connected:
            try:
                if self.ser and self.ser.in_waiting:
                    line = self.ser.readline().decode("ascii", errors="ignore").strip()
                    if line:
                        self.root.after(0, self._process_response, line)
                else:
                    time.sleep(0.02)
            except Exception:
                if self.connected:
                    self.root.after(0, self._disconnect)
                break

    def _process_response(self, line: str):
        self._log(f" 收到: {line}", "#90ee90")

        if line.startswith("POS"):
            try:
                parts = line.split()
                for p in parts:
                    if p.startswith("X="):
                        self.pos_x = float(p[2:])
                    elif p.startswith("Y="):
                        self.pos_y = float(p[2:])
                self._update_position_display()
            except ValueError:
                pass

        elif line.startswith("ALM"):
            code = line.split()[-1] if len(line.split()) > 1 else "??"
            self.lbl_servo.configure(text=f"报警 {code}", bootstyle="danger")
            self._log(f"[报警] 伺服报警代码: {code}", "red")

        elif line == "READY":
            self.lbl_servo.configure(text="就绪", bootstyle="success")

        elif line == "HOME DONE":
            self.pos_x = 0.0
            self.pos_y = 0.0
            self.trail.clear()
            self._update_position_display()
            self.lbl_servo.configure(text="已归零", bootstyle="success")

    def _send_manual_cmd(self):
        cmd = self.entry_cmd.get().strip()
        if cmd:
            self._send_cmd(cmd)

    # ─── 指令处理 ────────────────────────────────────────────────

    def _cmd_move(self):
        try:
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            f = int(float(self.entry_speed.get()))
            self._send_cmd(f"G01 X{x:.3f} Y{y:.3f} F{f}")
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效数字")

    def _cmd_rapid(self):
        try:
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            self._send_cmd(f"G00 X{x:.3f} Y{y:.3f}")
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效数字")

    def _cmd_home(self):
        self._send_cmd("G28")

    def _cmd_estop(self):
        self._send_cmd("M112")
        self._log("[系统] 紧急停止已发送!", "red")

    def _cmd_servo_on(self):
        self._send_cmd("M03")

    def _cmd_servo_off(self):
        self._send_cmd("M05")

    def _jog(self, direction: str):
        step = float(self.combo_step.get())
        if direction == "X+":
            self.pos_x += step
        elif direction == "X-":
            self.pos_x -= step
        elif direction == "Y+":
            self.pos_y += step
        elif direction == "Y-":
            self.pos_y -= step

        self.entry_x.delete(0, END)
        self.entry_x.insert(0, f"{self.pos_x:.3f}")
        self.entry_y.delete(0, END)
        self.entry_y.insert(0, f"{self.pos_y:.3f}")

        self._send_cmd(f"JOG {direction} {step:.3f}")

    # ─── 画布 ────────────────────────────────────────────────────

    def _draw_grid(self):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w = self.canvas_w
            h = self.canvas_h

        margin = self.margin
        cx, cy = w // 2, h // 2

        grid_spacing = 50
        for x in range(margin, w - margin, grid_spacing):
            self.canvas.create_line(x, margin, x, h - margin, fill="#2a2a4a", tags="grid")
        for y in range(margin, h - margin, grid_spacing):
            self.canvas.create_line(margin, y, w - margin, y, fill="#2a2a4a", tags="grid")

        self.canvas.create_line(margin, cy, w - margin, cy, fill="#4a90d9", width=2, tags="grid")
        self.canvas.create_line(cx, margin, cx, h - margin, fill="#4a90d9", width=2, tags="grid")

        self.canvas.create_text(w - margin + 10, cy, text="X", fill="#4a90d9", anchor=W, tags="grid")
        self.canvas.create_text(cx, margin - 10, text="Y", fill="#4a90d9", anchor=S, tags="grid")
        self.canvas.create_text(cx, cy + 15, text="O", fill="#666", anchor=N, tags="grid")

        for i in range(-500, 501, 100):
            px = cx + i * self.scale
            if margin < px < w - margin:
                self.canvas.create_line(px, cy - 4, px, cy + 4, fill="#4a90d9", tags="grid")
                self.canvas.create_text(px, cy + 14, text=str(i), fill="#555", font=("Arial", 7), tags="grid")
            py = cy - i * self.scale
            if margin < py < h - margin:
                self.canvas.create_line(cx - 4, py, cx + 4, py, fill="#4a90d9", tags="grid")
                if i != 0:
                    self.canvas.create_text(cx - 14, py, text=str(i), fill="#555", font=("Arial", 7), anchor=E, tags="grid")

    def _update_canvas(self):
        self.canvas.delete("trail")
        self.canvas.delete("pos")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w = self.canvas_w
            h = self.canvas_h

        cx, cy = w // 2, h // 2
        margin = self.margin

        if len(self.trail) > 1:
            points = []
            for tx, ty in self.trail:
                px = cx + tx * self.scale
                py = cy - ty * self.scale
                if margin < px < w - margin and margin < py < h - margin:
                    points.extend([px, py])
            if len(points) >= 4:
                self.canvas.create_line(*points, fill="#ff6b6b", width=1, smooth=True, tags="trail")

        px = cx + self.pos_x * self.scale
        py = cy - self.pos_y * self.scale
        if margin < px < w - margin and margin < py < h - margin:
            r = 6
            self.canvas.create_oval(
                px - r, py - r, px + r, py + r,
                fill="#ff4757", outline="white", width=2, tags="pos",
            )
            self.canvas.create_text(
                px + 12, py - 8,
                text=f"({self.pos_x:.1f}, {self.pos_y:.1f})",
                fill="#ffa502", font=("Consolas", 9), anchor=W, tags="pos",
            )

        self.root.after(100, self._update_canvas)

    def _canvas_click(self, event):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2

        x = (event.x - cx) / self.scale
        y = (cy - event.y) / self.scale

        self.entry_x.delete(0, END)
        self.entry_x.insert(0, f"{x:.3f}")
        self.entry_y.delete(0, END)
        self.entry_y.insert(0, f"{y:.3f}")

    # ─── 工具方法 ────────────────────────────────────────────────

    def _update_position_display(self):
        self.lbl_x.configure(text=f"X: {self.pos_x:.3f} mm")
        self.lbl_y.configure(text=f"Y: {self.pos_y:.3f} mm")
        self.trail.append((self.pos_x, self.pos_y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    def _log(self, msg: str, color: str = "white"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.text.configure(state="normal")
        self.log_text.text.tag_configure(color, foreground=color)
        self.log_text.text.insert(END, f"[{timestamp}] {msg}\n", color)
        self.log_text.text.see(END)
        self.log_text.text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.text.configure(state="normal")
        self.log_text.text.delete("1.0", END)
        self.log_text.text.configure(state="disabled")

    def _on_close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = XYTableApp()
    app.run()
