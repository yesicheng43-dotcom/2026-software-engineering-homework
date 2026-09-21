"""Tkinter 图形界面。运行：python -m homework2。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple

from .core import ActionResult, Arrow, GameSession, GameStatus


WINDOW_BG = "#0d1426"
CARD_BG = "#172440"
GRID_BG = "#111c34"
GRID_LINE = "#30476e"
TEXT = "#f4f7ff"
MUTED = "#a8b5d1"
ACCENT = "#70a7ff"
SUCCESS = "#54d69b"
DANGER = "#ff6b78"
ARROW_COLORS = {"^": "#ff6b7a", "v": "#55d99c", "<": "#ffb454", ">": "#70a7ff"}
ARROW_NAMES = {"^": "上", "v": "下", "<": "左", ">": "右"}


class ArrowGameApp(tk.Tk):
    """完整的开始、游戏、通关和失败页面。"""

    def __init__(self, session: Optional[GameSession] = None) -> None:
        super().__init__()
        self.title("一箭又一箭")
        self.geometry("820x760")
        self.minsize(680, 620)
        self.configure(bg=WINDOW_BG)
        self.session = session or GameSession()
        self._view: Optional[tk.Frame] = None
        self.canvas: Optional[tk.Canvas] = None
        self._layout: Optional[Tuple[float, float, float]] = None
        self._flash_position: Optional[Tuple[int, int]] = None
        self._animating = False
        self._message_var = tk.StringVar(value="")
        self._level_var = tk.StringVar()
        self._remaining_var = tk.StringVar()
        self._mistakes_var = tk.StringVar()
        self.show_start()

    def _clear_view(self) -> tk.Frame:
        if self._view is not None:
            self._view.destroy()
        self._view = tk.Frame(self, bg=WINDOW_BG)
        self._view.pack(fill="both", expand=True)
        return self._view

    def _button(self, parent: tk.Widget, text: str, command, *, primary: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=WINDOW_BG if primary else TEXT,
            bg=ACCENT if primary else CARD_BG,
            activeforeground=WINDOW_BG if primary else TEXT,
            activebackground="#95bdff" if primary else "#24365c",
            relief="flat",
            bd=0,
            padx=22,
            pady=10,
            cursor="hand2",
        )

    def show_start(self) -> None:
        view = self._clear_view()
        view.columnconfigure(0, weight=1)
        view.rowconfigure(0, weight=1)
        card = tk.Frame(view, bg=CARD_BG, padx=46, pady=38)
        card.grid(row=0, column=0, padx=32, pady=32)

        tk.Label(card, text="一箭又一箭", font=("Microsoft YaHei UI", 32, "bold"), fg=TEXT, bg=CARD_BG).pack()
        tk.Label(card, text="观察方向，找出每支箭头的出路", font=("Microsoft YaHei UI", 14), fg=MUTED, bg=CARD_BG).pack(pady=(8, 26))
        rules = (
            "点击箭头后，它会沿指向方向飞向棋盘边界。\n"
            "前方没有箭头即可消除；撞到阻挡会消耗一次失误机会。\n"
            "清空棋盘即可通关，失误次数耗尽则需要重试。"
        )
        tk.Label(card, text=rules, justify="left", font=("Microsoft YaHei UI", 12), fg=TEXT, bg=CARD_BG).pack()

        legend = tk.Frame(card, bg=CARD_BG)
        legend.pack(pady=28)
        for symbol in ("^", "v", "<", ">"):
            tk.Label(legend, text=f"{symbol}  {ARROW_NAMES[symbol]}", font=("Segoe UI Symbol", 16, "bold"), fg=ARROW_COLORS[symbol], bg=CARD_BG, padx=10).pack(side="left")

        self._button(card, "开始游戏", lambda: self._start_game(0), primary=True).pack(pady=(4, 10), fill="x")
        tk.Label(card, text=f"共 {len(self.session.levels)} 个关卡 · 每关默认 3 次失误机会", font=("Microsoft YaHei UI", 10), fg=MUTED, bg=CARD_BG).pack()

    def _start_game(self, level_index: int) -> None:
        self.session.start(level_index)
        self.show_playing()

    def show_playing(self) -> None:
        view = self._clear_view()
        view.rowconfigure(1, weight=1)
        view.columnconfigure(0, weight=1)

        header = tk.Frame(view, bg=WINDOW_BG, padx=24, pady=18)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        tk.Label(header, textvariable=self._level_var, font=("Microsoft YaHei UI", 17, "bold"), fg=TEXT, bg=WINDOW_BG).grid(row=0, column=0, sticky="w")
        stats = tk.Frame(header, bg=WINDOW_BG)
        stats.grid(row=0, column=1, sticky="e")
        tk.Label(stats, textvariable=self._remaining_var, font=("Microsoft YaHei UI", 11), fg=MUTED, bg=WINDOW_BG).pack(side="left", padx=12)
        tk.Label(stats, textvariable=self._mistakes_var, font=("Microsoft YaHei UI", 11, "bold"), fg=DANGER, bg=WINDOW_BG).pack(side="left", padx=12)

        board_card = tk.Frame(view, bg=CARD_BG, padx=16, pady=16)
        board_card.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="nsew")
        board_card.rowconfigure(0, weight=1)
        board_card.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(board_card, bg=GRID_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self._draw_board())

        footer = tk.Frame(view, bg=WINDOW_BG, padx=24, pady=14)
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        tk.Label(footer, textvariable=self._message_var, font=("Microsoft YaHei UI", 11), fg=MUTED, bg=WINDOW_BG, anchor="w").grid(row=0, column=0, sticky="w")
        buttons = tk.Frame(footer, bg=WINDOW_BG)
        buttons.grid(row=0, column=1, sticky="e")
        self._button(buttons, "重新开始", self._restart_level).pack(side="left", padx=4)
        self._button(buttons, "返回首页", self.show_start).pack(side="left", padx=4)

        self._message_var.set("请选择一支前方畅通的箭头")
        self._update_stats()
        self.after_idle(self._draw_board)

    def _restart_level(self) -> None:
        if self._animating:
            return
        self.session.restart()
        self.show_playing()

    def _update_stats(self) -> None:
        self._level_var.set(self.session.current_level.name)
        self._remaining_var.set(f"剩余箭头：{self.session.board.remaining}")
        self._mistakes_var.set(f"失误机会：{'❤' * self.session.mistakes_left}")

    def _draw_board(self) -> None:
        if self.canvas is None:
            return
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        rows, cols = self.session.board.rows, self.session.board.cols
        cell = max(30.0, min((width - 48) / cols, (height - 48) / rows))
        board_width, board_height = cols * cell, rows * cell
        origin_x, origin_y = (width - board_width) / 2, (height - board_height) / 2
        self._layout = origin_x, origin_y, cell
        for row in range(rows):
            for col in range(cols):
                x1, y1 = origin_x + col * cell, origin_y + row * cell
                self.canvas.create_rectangle(x1 + 2, y1 + 2, x1 + cell - 2, y1 + cell - 2, fill=GRID_BG, outline=GRID_LINE, width=1)
        for arrow in self.session.board.arrows:
            self._draw_arrow_at(arrow, *self._center_for(arrow.row, arrow.col))
        if self._flash_position is not None:
            row, col = self._flash_position
            cx, cy = self._center_for(row, col)
            radius = cell * 0.37
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=DANGER, width=4)

    def _center_for(self, row: int, col: int) -> Tuple[float, float]:
        if self._layout is None:
            return 0.0, 0.0
        origin_x, origin_y, cell = self._layout
        return origin_x + (col + 0.5) * cell, origin_y + (row + 0.5) * cell

    def _draw_arrow_at(self, arrow: Arrow, cx: float, cy: float) -> None:
        if self.canvas is None or self._layout is None:
            return
        _, _, cell = self._layout
        color = ARROW_COLORS[arrow.direction]
        vectors = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}
        dx, dy = vectors[arrow.direction]
        tail = cell * 0.25
        tip = cell * 0.29
        line_start = (cx - dx * tail, cy - dy * tail)
        line_end = (cx + dx * tail, cy + dy * tail)
        self.canvas.create_line(*line_start, *line_end, fill=color, width=max(3, int(cell * 0.07)), capstyle="round")
        px, py = -dy, dx
        points = (
            cx + dx * tip,
            cy + dy * tip,
            cx - dx * tip * 0.45 + px * tip * 0.65,
            cy - dy * tip * 0.45 + py * tip * 0.65,
            cx - dx * tip * 0.45 - px * tip * 0.65,
            cy - dy * tip * 0.45 - py * tip * 0.65,
        )
        self.canvas.create_polygon(*points, fill=color, outline=color)

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self._animating or self._layout is None:
            return
        origin_x, origin_y, cell = self._layout
        col = int((event.x - origin_x) // cell)
        row = int((event.y - origin_y) // cell)
        if not self.session.board.in_bounds(row, col):
            return
        result = self.session.click(row, col)
        if result.kind == "invalid":
            return
        self._update_stats()
        if result.kind == "blocked":
            self._flash_position = result.arrow.position
            blocker_text = f"（挡路箭头在第 {result.blocker.row + 1} 行第 {result.blocker.col + 1} 列）" if result.blocker else ""
            self._message_var.set(f"碰撞！失误机会 -1 {blocker_text}")
            self._draw_board()
            self.after(460, self._finish_blocked_feedback)
            if result.status is GameStatus.FAILED:
                self.after(650, self.show_result)
            return
        self._animating = True
        self._message_var.set("箭头飞出中……")
        self._animate_fly(result.arrow, 0)

    def _finish_blocked_feedback(self) -> None:
        self._flash_position = None
        if self.session.status is GameStatus.PLAYING:
            self._message_var.set("请选择一支前方畅通的箭头")
            self._draw_board()

    def _animate_fly(self, arrow: Arrow, step: int) -> None:
        if self.canvas is None:
            return
        total_steps = 12
        self._draw_board()
        start_x, start_y = self._center_for(arrow.row, arrow.col)
        vectors = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}
        dx, dy = vectors[arrow.direction]
        _, _, cell = self._layout or (0, 0, 40)
        progress = step / total_steps
        distance = cell * 1.8 * progress
        self._draw_arrow_at(arrow, start_x + dx * distance, start_y + dy * distance)
        if step < total_steps:
            self.after(25, lambda: self._animate_fly(arrow, step + 1))
            return
        self._animating = False
        if self.session.status is GameStatus.WON:
            self.show_result()
        else:
            self._message_var.set("消除成功，请继续观察下一支箭头")
            self._update_stats()
            self._draw_board()

    def show_result(self) -> None:
        view = self._clear_view()
        view.columnconfigure(0, weight=1)
        view.rowconfigure(0, weight=1)
        card = tk.Frame(view, bg=CARD_BG, padx=54, pady=44)
        card.grid(row=0, column=0, padx=32, pady=32)
        if self.session.status is GameStatus.FAILED:
            title, subtitle, color = "本关失败", "失误机会已经用完，再试一次吧！", DANGER
            primary_text, primary_command = "重新开始", self._restart_level
        else:
            is_last = self.session.level_index == len(self.session.levels) - 1
            title = "全部通关" if is_last else "本关通关"
            subtitle = "太棒了！棋盘上的箭头已经全部清除。" if is_last else "准备好迎接下一关了吗？"
            color = SUCCESS
            primary_text = "返回首页" if is_last else "下一关"
            primary_command = self._next_level if not is_last else self.show_start
        tk.Label(card, text=title, font=("Microsoft YaHei UI", 30, "bold"), fg=color, bg=CARD_BG).pack()
        tk.Label(card, text=subtitle, font=("Microsoft YaHei UI", 13), fg=TEXT, bg=CARD_BG).pack(pady=(12, 28))
        if self.session.status is GameStatus.FAILED:
            tk.Label(card, text=f"当前关卡：{self.session.current_level.name}", font=("Microsoft YaHei UI", 11), fg=MUTED, bg=CARD_BG).pack(pady=(0, 20))
        else:
            tk.Label(card, text=f"已清除 {self.session.current_level.name} 的全部箭头", font=("Microsoft YaHei UI", 11), fg=MUTED, bg=CARD_BG).pack(pady=(0, 20))
        self._button(card, primary_text, primary_command, primary=True).pack(fill="x", pady=5)
        if self.session.status is GameStatus.WON:
            self._button(card, "重新挑战本关", self._restart_level).pack(fill="x", pady=5)
        self._button(card, "返回首页", self.show_start).pack(fill="x", pady=5)

    def _next_level(self) -> None:
        self.session.next_level()
        self.show_playing()


def run() -> None:
    app = ArrowGameApp()
    app.mainloop()


if __name__ == "__main__":
    run()
