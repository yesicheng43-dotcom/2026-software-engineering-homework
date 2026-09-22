"""Tkinter 图形界面。运行：python -m homework2。"""

from __future__ import annotations

import tkinter as tk
from math import sin
from typing import Optional, Tuple

from .core import ActionResult, Arrow, GameSession, GameStatus


WINDOW_BG = "#eaf1f7"
CARD_BG = "#ffffff"
GRID_BG = "#f7fbff"
GRID_LINE = "#c7d7e8"
TEXT = "#2b3a55"
MUTED = "#72819a"
ACCENT = "#6d94d6"
SUCCESS = "#4aa88a"
DANGER = "#d66c78"

# 颜色不再与方向绑定：方向由箭头形状表达，颜色只用于区分相邻箭头。
# 使用低饱和度调色板，按箭头位置和关卡编号轮换，避免同方向箭头全部同色。
ARROW_PALETTE = (
    "#d8898f",  # 柔和珊瑚
    "#77aaa4",  # 灰青绿
    "#d7ad67",  # 暖金
    "#789bd0",  # 雾蓝
    "#a889c4",  # 淡紫
    "#d59672",  # 杏橙
    "#6fa7b9",  # 湖蓝
    "#c883a5",  # 莓粉
)
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
        self._shake_position: Optional[Tuple[int, int]] = None
        self._error_position: Optional[Tuple[int, int]] = None
        self._shake_step = 0
        self._heart_burst_frame = ""
        self._animating = False
        self._message_var = tk.StringVar(value="")
        self._level_var = tk.StringVar()
        self._remaining_var = tk.StringVar()
        self._mistakes_var = tk.StringVar()
        self.show_start()

    def _clear_view(self) -> tk.Frame:
        if self._view is not None:
            self._view.destroy()
        # 让已经排队的动画回调在切换页面后安全退出。
        self.canvas = None
        self._layout = None
        self._animating = False
        self._shake_position = None
        self._error_position = None
        self._heart_burst_frame = ""
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
            activebackground="#88a8df" if primary else "#edf3f9",
            relief="flat",
            bd=0,
            padx=22,
            pady=10,
            cursor="hand2",
        )

    def show_start(self) -> None:
        view = self._clear_view()
        view.columnconfigure(0, weight=1)
        view.rowconfigure(1, weight=1)

        hero = tk.Canvas(view, height=214, bg="#dceaf7", highlightthickness=0)
        hero.grid(row=0, column=0, sticky="ew")
        self._draw_home_hero(hero)

        content = tk.Frame(view, bg=WINDOW_BG, padx=28, pady=20)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        card = tk.Frame(content, bg=CARD_BG, padx=34, pady=24, highlightbackground="#d3e1ee", highlightthickness=1)
        card.grid(row=0, column=0, sticky="ew")

        badge = tk.Label(card, text="轻量解谜 · 四向箭头", font=("Microsoft YaHei UI", 10, "bold"), fg=ACCENT, bg="#edf4fc", padx=12, pady=5)
        badge.pack(anchor="w")
        tk.Label(card, text="找出每支箭头的出路", font=("Microsoft YaHei UI", 18, "bold"), fg=TEXT, bg=CARD_BG).pack(anchor="w", pady=(13, 5))
        tk.Label(card, text="观察前方是否有阻挡，按正确顺序清空棋盘。", font=("Microsoft YaHei UI", 11), fg=MUTED, bg=CARD_BG).pack(anchor="w")

        info_row = tk.Frame(card, bg=CARD_BG)
        info_row.pack(fill="x", pady=(20, 18))
        self._home_chip(info_row, "4", "个固定关卡").pack(side="left", expand=True, fill="x", padx=(0, 8))
        self._home_chip(info_row, "4", "个箭头方向").pack(side="left", expand=True, fill="x", padx=4)
        self._home_chip(info_row, "3", "次容错机会").pack(side="left", expand=True, fill="x", padx=(8, 0))

        self._button(card, "▶  开始挑战", lambda: self._start_game(0), primary=True).pack(fill="x", pady=(2, 12))
        legend = tk.Frame(card, bg=CARD_BG)
        legend.pack()
        for index, symbol in enumerate(("^", "v", "<", ">")):
            tk.Label(legend, text=f"{symbol} {ARROW_NAMES[symbol]}", font=("Segoe UI Symbol", 11, "bold"), fg=ARROW_PALETTE[index], bg=CARD_BG, padx=10).pack(side="left")

    def _draw_home_hero(self, canvas: tk.Canvas) -> None:
        """绘制首页的游戏化视觉头图，避免首页像普通说明文档。"""

        width = max(canvas.winfo_width(), 820)
        canvas.create_oval(width - 210, -58, width + 55, 206, fill="#c9def3", outline="")
        canvas.create_oval(width - 150, 14, width + 18, 182, fill="#d3e6f6", outline="")
        canvas.create_text(36, 38, text="ARROW PUZZLE", anchor="w", fill="#6686ae", font=("Segoe UI", 10, "bold"))
        canvas.create_text(34, 91, text="一箭又一箭", anchor="w", fill=TEXT, font=("Microsoft YaHei UI", 33, "bold"))
        canvas.create_text(38, 143, text="每一次点击，都是一次出路判断", anchor="w", fill="#68809e", font=("Microsoft YaHei UI", 13))
        for x, y, symbol, color in ((width - 165, 68, "↑", ARROW_PALETTE[3]), (width - 92, 115, "→", ARROW_PALETTE[1]), (width - 205, 137, "←", ARROW_PALETTE[0]), (width - 92, 47, "↓", ARROW_PALETTE[2])):
            canvas.create_text(x, y, text=symbol, fill=color, font=("Segoe UI Symbol", 31, "bold"))

    def _home_chip(self, parent: tk.Widget, value: str, label: str) -> tk.Frame:
        chip = tk.Frame(parent, bg="#f2f7fc", padx=10, pady=8, highlightbackground="#e0eaf3", highlightthickness=1)
        tk.Label(chip, text=value, font=("Microsoft YaHei UI", 17, "bold"), fg=ACCENT, bg="#f2f7fc").pack()
        tk.Label(chip, text=label, font=("Microsoft YaHei UI", 9), fg=MUTED, bg="#f2f7fc").pack()
        return chip

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
        tk.Label(stats, textvariable=self._remaining_var, font=("Microsoft YaHei UI", 12, "bold"), fg=MUTED, bg=WINDOW_BG, padx=12, pady=6).pack(side="left", padx=6)
        self._mistakes_label = tk.Label(stats, textvariable=self._mistakes_var, font=("Segoe UI Symbol", 15, "bold"), fg=DANGER, bg="#fff1f2", padx=14, pady=6)
        self._mistakes_label.pack(side="left", padx=6)

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
        hearts = " ".join("❤" for _ in range(self.session.mistakes_left)) or "—"
        burst = f"  {self._heart_burst_frame}" if self._heart_burst_frame else ""
        self._mistakes_var.set(f"生命  {hearts}{burst}")

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
            cx, cy = self._center_for(arrow.row, arrow.col)
            if arrow.position == self._shake_position:
                shake = sin(self._shake_step * 1.9) * cell * 0.12
                if arrow.direction in "<>":
                    cx += shake
                else:
                    cy += shake
            error_color = DANGER if arrow.position == self._error_position else None
            self._draw_arrow_at(arrow, cx, cy, error_color)

    def _center_for(self, row: int, col: int) -> Tuple[float, float]:
        if self._layout is None:
            return 0.0, 0.0
        origin_x, origin_y, cell = self._layout
        return origin_x + (col + 0.5) * cell, origin_y + (row + 0.5) * cell

    def _draw_arrow_at(self, arrow: Arrow, cx: float, cy: float, color_override: Optional[str] = None) -> None:
        if self.canvas is None or self._layout is None:
            return
        _, _, cell = self._layout
        color = color_override or self._arrow_color(arrow)
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

    def _arrow_color(self, arrow: Arrow) -> str:
        """按位置稳定分配颜色，让同方向箭头也能拥有不同颜色。"""

        palette_index = (
            arrow.row * 7
            + arrow.col * 11
            + self.session.level_index * 3
        ) % len(ARROW_PALETTE)
        return ARROW_PALETTE[palette_index]

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
            self._animating = True
            self._shake_position = result.arrow.position
            self._error_position = result.blocker.position if result.blocker else None
            self._shake_step = 0
            blocker_text = f"（挡路箭头在第 {result.blocker.row + 1} 行第 {result.blocker.col + 1} 列）" if result.blocker else ""
            self._message_var.set(f"无法飞出，箭头发生震动 {blocker_text}")
            self._animate_heart_burst(0)
            self._animate_blocked(result.status, 0)
            return
        self._animating = True
        self._message_var.set("箭头飞出中……")
        self._animate_fly(result.arrow, 0)

    def _animate_heart_burst(self, frame: int) -> None:
        """用短促的破碎符号反馈一次失误，明显但不过度。"""

        frames = ("❤", "✦✦", "·", "")
        if frame >= len(frames):
            self._heart_burst_frame = ""
            self._update_stats()
            return
        self._heart_burst_frame = frames[frame]
        self._update_stats()
        self.after(72, lambda: self._animate_heart_burst(frame + 1))

    def _animate_blocked(self, result_status: GameStatus, step: int) -> None:
        """让被点击箭头震动，同时让真正的阻挡箭头短暂变红。"""

        total_steps = 10
        if self.canvas is None:
            return
        self._shake_step = step
        self._draw_board()
        if step < total_steps:
            self.after(36, lambda: self._animate_blocked(result_status, step + 1))
            return
        self._shake_position = None
        self._error_position = None
        self._animating = False
        if result_status is GameStatus.FAILED:
            self.after(280, self.show_result)
        else:
            self._message_var.set("请选择一支前方畅通的箭头")
            self._draw_board()

    def _animate_fly(self, arrow: Arrow, step: int) -> None:
        if self.canvas is None:
            return
        total_steps = 14
        self._draw_board()
        start_x, start_y = self._center_for(arrow.row, arrow.col)
        vectors = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}
        dx, dy = vectors[arrow.direction]
        _, _, cell = self._layout or (0, 0, 40)
        progress = step / total_steps
        # 飞行距离覆盖整个棋盘并再多走两个格，确保箭头完整离屏。
        distance = cell * (max(self.session.board.rows, self.session.board.cols) + 2.0) * progress
        self._draw_arrow_at(arrow, start_x + dx * distance, start_y + dy * distance)
        if step < total_steps:
            self.after(18, lambda: self._animate_fly(arrow, step + 1))
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
