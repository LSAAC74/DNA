"""《二重螺旋》挂机脚本 — 可视化控制界面"""

from __future__ import annotations

import logging
import queue
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

import config
from core.runner import ScriptRunner


class GuiLogHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("二重螺旋 · 夜航手册挂机")
        self.geometry("480x490")
        self.resizable(True, True)

        self._runner: ScriptRunner | None = None
        self._log_queue: queue.Queue[str] = queue.Queue()

        self._build_ui()
        self._setup_logging()
        self.after(200, self._poll_log)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, **pad)

        ttk.Label(frm, text="选择等级").grid(row=0, column=0, sticky=tk.W)
        self.level_var = tk.StringVar(value="65")
        level_box = ttk.Combobox(
            frm,
            textvariable=self.level_var,
            values=["20", "30", "40", "50", "65", "75"],
            width=10,
            state="readonly",
        )
        level_box.grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
        ttk.Label(frm, text="20/30=4前往 40/50=双图 65/75=5前往").grid(
            row=0, column=2, sticky=tk.W, padx=(8, 0)
        )

        ttk.Label(frm, text="额外参数").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.go_var = tk.StringVar(value="1")
        ttk.Entry(frm, textvariable=self.go_var, width=12).grid(
            row=1, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        ttk.Label(frm, text="(右侧第几个「前往」，1=第一个)").grid(
            row=1, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )

        ttk.Label(frm, text="倍率书").grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
        self.multiply_var = tk.StringVar(value="不选")
        multiply_box = ttk.Combobox(
            frm,
            textvariable=self.multiply_var,
            values=["不选", "绿", "蓝", "粉", "橙"],
            width=10,
            state="readonly",
        )
        multiply_box.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        ttk.Label(frm, text="(低→高，不选则跳过)").grid(
            row=2, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )

        ttk.Label(frm, text="倍率书轮数").grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
        self.multiply_rounds_var = tk.StringVar(value="1")
        ttk.Entry(frm, textvariable=self.multiply_rounds_var, width=12).grid(
            row=3, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        ttk.Label(frm, text="(选倍率书时生效，用多少轮)").grid(
            row=3, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )

        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill=tk.X, **pad)

        self.start_btn = ttk.Button(btn_frm, text="开始", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, padx=(12, 6), pady=4)

        self.stop_btn = ttk.Button(
            btn_frm, text="停止", command=self._on_stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=6, pady=4)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self, textvariable=self.status_var, foreground="#666").pack(
            anchor=tk.W, padx=12, pady=(4, 0)
        )

        ttk.Label(self, text="运行日志").pack(anchor=tk.W, padx=12, pady=(8, 0))
        self.log_text = scrolledtext.ScrolledText(
            self, height=16, state=tk.DISABLED, font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))

    def _setup_logging(self) -> None:
        handler = GuiLogHandler(self._log_queue)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")
        )
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        if not any(isinstance(h, GuiLogHandler) for h in root.handlers):
            root.addHandler(handler)

    def _poll_log(self) -> None:
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.after(200, self._poll_log)

    def _parse_inputs(self) -> tuple[int, int, str | None, int] | None:
        try:
            level = int(self.level_var.get().strip())
            go_index = int(self.go_var.get().strip())
        except ValueError:
            messagebox.showerror("输入错误", "等级和额外参数必须是整数")
            return None

        if level < 1:
            messagebox.showerror("输入错误", "等级须 >= 1")
            return None
        if go_index < 1:
            messagebox.showerror("输入错误", "额外参数（前往序号）须 >= 1")
            return None
        if level not in (20, 30, 40, 50, 65, 75):
            messagebox.showwarning(
                "等级提示",
                f"等级 {level} 未单独配置，将按 65 级默认走位与 5 个前往处理",
            )
        if level == 50:
            if go_index > 7:
                messagebox.showerror("输入错误", "50 级共 7 个副本，前往序号须 1–7")
                return None
        if level == 75:
            if go_index > 9:
                messagebox.showerror("输入错误", "75 级共 9 个副本，前往序号须 1–9")
                return None
            if go_index == 1:
                messagebox.showwarning(
                    "提示",
                    "75 级第 1 个副本尚未配置，启动后将无法进入战斗挂机",
                )

        multiply_label = self.multiply_var.get().strip()
        if multiply_label == "不选":
            multiply_book = None
            multiply_rounds = 0
        elif multiply_label in config.MULTIPLY_BOOK_BY_LABEL:
            multiply_book = config.MULTIPLY_BOOK_BY_LABEL[multiply_label]
            try:
                multiply_rounds = int(self.multiply_rounds_var.get().strip())
            except ValueError:
                messagebox.showerror("输入错误", "倍率书轮数必须是整数")
                return None
            if multiply_rounds < 1:
                messagebox.showerror("输入错误", "倍率书轮数须 >= 1")
                return None
        else:
            messagebox.showerror("输入错误", "倍率书须选择：不选 / 绿 / 蓝 / 粉 / 橙")
            return None

        return level, go_index, multiply_book, multiply_rounds

    def _on_start(self) -> None:
        if self._runner and self._runner.is_running:
            return

        parsed = self._parse_inputs()
        if not parsed:
            return

        level, go_index, multiply_book, multiply_rounds = parsed
        if multiply_book:
            multiply_text = (
                f"{config.MULTIPLY_BOOK_LABELS[multiply_book]}×{multiply_rounds}轮"
            )
        else:
            multiply_text = "无"
        self.status_var.set(
            f"运行中 | 等级 {level} | 前往 #{go_index} | 倍率书 {multiply_text}"
        )
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        self._runner = ScriptRunner(
            level=level,
            go_index=go_index,
            multiply_book=multiply_book,
            multiply_rounds=multiply_rounds,
            on_status=self._set_status,
            on_finished=self._on_finished,
        )
        self._runner.start()

    def _on_stop(self) -> None:
        if self._runner:
            self._runner.stop()

    def _set_status(self, msg: str) -> None:
        self.after(0, lambda: self.status_var.set(msg))

    def _on_finished(self) -> None:
        def _reset() -> None:
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
            if "停止" not in self.status_var.get():
                self.status_var.set("就绪")

        self.after(0, _reset)


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
