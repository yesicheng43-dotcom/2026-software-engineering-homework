"""固定关卡数据和关卡校验。"""

from dataclasses import dataclass
from typing import Iterable, Tuple

ARROW_SYMBOLS = frozenset("^v<>")


@dataclass(frozen=True)
class Level:
    """一个由字符网格描述的关卡。"""

    name: str
    layout: Tuple[str, ...]
    mistakes: int = 3

    def __post_init__(self) -> None:
        if not self.layout:
            raise ValueError("关卡棋盘不能为空")
        width = len(self.layout[0])
        if width == 0:
            raise ValueError("关卡棋盘不能有空行")
        if any(len(row) != width for row in self.layout):
            raise ValueError("关卡每一行必须具有相同长度")
        invalid = sorted({char for row in self.layout for char in row if char not in ARROW_SYMBOLS and char not in ". "})
        if invalid:
            raise ValueError(f"关卡包含不支持的字符: {invalid}")
        if not any(char in ARROW_SYMBOLS for row in self.layout for char in row):
            raise ValueError("关卡至少需要一支箭头")
        if self.mistakes <= 0:
            raise ValueError("失误次数必须为正数")

    @property
    def rows(self) -> int:
        return len(self.layout)

    @property
    def cols(self) -> int:
        return len(self.layout[0])


def _level(name: str, rows: Iterable[str]) -> Level:
    return Level(name=name, layout=tuple(rows))


# 关卡按“可直接飞出 → 存在多层依赖”的方向递增，四种方向均有覆盖。
# 外层箭头提供可消除的入口，内层箭头会被外层或中层挡住，
# 因而第一关开始就需要观察和试错，而不是点击任意箭头都能通关。
LEVELS = (
    _level(
        "第 1 关 · 初识箭阵",
        (
            ".^.^.",
            "<^.>>",
            "<.>.>",
            "<<.v>",
            ".v.v.",
        ),
    ),
    _level(
        "第 2 关 · 交错箭阵",
        (
            ".^.^.^",
            "<^.^.>",
            "<<>.>>",
            "<<^^>>",
            "<v.v.>",
            ".v.v.v",
        ),
    ),
    _level(
        "第 3 关 · 纵深迷阵",
        (
            ".^.^.^.",
            "<<.^.>>",
            "<<<^>.>",
            "<<<^>>>",
            "<<<v>.>",
            "<<.v.>>",
            ".v.v.v.",
        ),
    ),
    _level(
        "第 4 关 · 棋盘风暴",
        (
            ".^.^.^.^",
            "<^...^.>",
            "<.<^>..>",
            "<<.^.>.>",
            "<.<..>.>",
            "<<.v>..>",
            "<v...v.>",
            ".v.v.v.v",
        ),
    ),
)


def get_levels() -> Tuple[Level, ...]:
    """返回固定关卡的不可变序列。"""

    return LEVELS
