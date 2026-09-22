"""游戏规则层：不依赖 GUI，可直接进行自动化测试。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .levels import ARROW_SYMBOLS, LEVELS, Level, generate_random_level

Position = Tuple[int, int]

DIRECTION_DELTAS: Dict[str, Position] = {
    "^": (-1, 0),
    "v": (1, 0),
    "<": (0, -1),
    ">": (0, 1),
}


class GameStatus(str, Enum):
    START = "start"
    PLAYING = "playing"
    WON = "won"
    FAILED = "failed"
    ALL_CLEARED = "all_cleared"


@dataclass(frozen=True)
class Arrow:
    row: int
    col: int
    direction: str

    @property
    def position(self) -> Position:
        return self.row, self.col


@dataclass(frozen=True)
class ActionResult:
    kind: str
    arrow: Optional[Arrow] = None
    blocker: Optional[Arrow] = None
    remaining_arrows: int = 0
    mistakes_left: int = 0
    status: GameStatus = GameStatus.START


class Board:
    """运行中的棋盘；箭头被移除后不会再参与后续路径判断。"""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.rows = level.rows
        self.cols = level.cols
        self._arrows: Dict[Position, Arrow] = {}
        for row, line in enumerate(level.layout):
            for col, symbol in enumerate(line):
                if symbol in ARROW_SYMBOLS:
                    self._arrows[(row, col)] = Arrow(row, col, symbol)

    @property
    def arrows(self) -> Tuple[Arrow, ...]:
        return tuple(self._arrows.values())

    @property
    def remaining(self) -> int:
        return len(self._arrows)

    def arrow_at(self, row: int, col: int) -> Optional[Arrow]:
        return self._arrows.get((row, col))

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def path_cells(self, arrow: Arrow) -> Tuple[Position, ...]:
        """返回箭头前方直到边界的所有棋盘内格子。"""

        row_step, col_step = DIRECTION_DELTAS[arrow.direction]
        row, col = arrow.row + row_step, arrow.col + col_step
        cells: List[Position] = []
        while self.in_bounds(row, col):
            cells.append((row, col))
            row += row_step
            col += col_step
        return tuple(cells)

    def blocking_arrow(self, arrow: Arrow) -> Optional[Arrow]:
        for position in self.path_cells(arrow):
            blocker = self._arrows.get(position)
            if blocker is not None:
                return blocker
        return None

    def can_fly(self, arrow: Arrow) -> bool:
        return self.blocking_arrow(arrow) is None

    def remove(self, arrow: Arrow) -> None:
        self._arrows.pop(arrow.position, None)


def find_solution(level: Level) -> Optional[Tuple[Position, ...]]:
    """用记忆化 DFS 找到一条可行的消除顺序；无解时返回 ``None``。"""

    arrows: List[Arrow] = []
    for row, line in enumerate(level.layout):
        for col, symbol in enumerate(line):
            if symbol in ARROW_SYMBOLS:
                arrows.append(Arrow(row, col, symbol))
    positions = tuple(arrow.position for arrow in arrows)
    index_by_position = {position: index for index, position in enumerate(positions)}
    full_mask = (1 << len(arrows)) - 1

    @lru_cache(maxsize=None)
    def search(mask: int) -> Optional[Tuple[int, ...]]:
        if mask == 0:
            return ()
        for index, arrow in enumerate(arrows):
            bit = 1 << index
            if not mask & bit:
                continue
            row_step, col_step = DIRECTION_DELTAS[arrow.direction]
            row, col = arrow.row + row_step, arrow.col + col_step
            blocked = False
            while 0 <= row < level.rows and 0 <= col < level.cols:
                other_index = index_by_position.get((row, col))
                if other_index is not None and mask & (1 << other_index):
                    blocked = True
                    break
                row += row_step
                col += col_step
            if blocked:
                continue
            result = search(mask ^ bit)
            if result is not None:
                return (index,) + result
        return None

    index_solution = search(full_mask)
    if index_solution is None:
        return None
    return tuple(positions[index] for index in index_solution)


def is_solvable(level: Level) -> bool:
    return find_solution(level) is not None


class GameSession:
    """管理关卡流程和玩家操作。"""

    def __init__(
        self,
        levels: Sequence[Level] = LEVELS,
        *,
        randomize: bool = False,
        rng: Optional[random.Random] = None,
    ) -> None:
        if not levels:
            raise ValueError("至少需要一个关卡")
        self._base_levels = tuple(levels)
        self._randomize = randomize
        self._rng = rng or random.Random()
        self.levels = self._base_levels
        self.level_index = 0
        self.board = Board(self.levels[0])
        self.mistakes_left = self.levels[0].mistakes
        self.status = GameStatus.START

    @property
    def current_level(self) -> Level:
        return self.levels[self.level_index]

    def start(self, level_index: int = 0) -> None:
        if not 0 <= level_index < len(self.levels):
            raise IndexError("关卡编号超出范围")
        self.level_index = level_index
        self.restart()

    def restart(self) -> None:
        if self._randomize:
            generated = generate_random_level(self._base_levels[self.level_index], self._rng)
            current_levels = list(self.levels)
            current_levels[self.level_index] = generated
            self.levels = tuple(current_levels)
        self.board = Board(self.current_level)
        self.mistakes_left = self.current_level.mistakes
        self.status = GameStatus.PLAYING

    def next_level(self) -> bool:
        if self.status is not GameStatus.WON:
            return False
        if self.level_index + 1 >= len(self.levels):
            self.status = GameStatus.ALL_CLEARED
            return False
        self.level_index += 1
        self.restart()
        return True

    def click(self, row: int, col: int) -> ActionResult:
        if self.status is not GameStatus.PLAYING:
            return ActionResult("ignored", remaining_arrows=self.board.remaining, mistakes_left=self.mistakes_left, status=self.status)
        arrow = self.board.arrow_at(row, col)
        if arrow is None:
            return ActionResult("invalid", remaining_arrows=self.board.remaining, mistakes_left=self.mistakes_left, status=self.status)

        blocker = self.board.blocking_arrow(arrow)
        if blocker is not None:
            self.mistakes_left -= 1
            if self.mistakes_left <= 0:
                self.mistakes_left = 0
                self.status = GameStatus.FAILED
            return ActionResult("blocked", arrow, blocker, self.board.remaining, self.mistakes_left, self.status)

        self.board.remove(arrow)
        if self.board.remaining == 0:
            self.status = GameStatus.WON
        return ActionResult("fly", arrow, None, self.board.remaining, self.mistakes_left, self.status)
