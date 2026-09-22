"""关卡模板、随机棋盘生成和关卡校验。"""

from dataclasses import dataclass
import random
from typing import Iterable, Optional, Sequence, Tuple

ARROW_SYMBOLS = frozenset("^v<>")
_DIRECTION_DELTAS = {
    "^": (-1, 0),
    "v": (1, 0),
    "<": (0, -1),
    ">": (0, 1),
}


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


# 这些布局是关卡模板：尺寸、箭头数量和容错次数会被随机生成器继承。
# 实际游戏开始时不会直接使用模板，而是生成一张新的可解棋盘。
LEVELS = (
    _level(
        "第 1 关 · 初识箭阵",
        (
            "^.>.>",
            "^^>>>",
            "v>...",
            "...>v",
            "<<v..",
        ),
    ),
    _level(
        "第 2 关 · 交错箭阵",
        (
            "^<v.>>",
            ".<.>.>",
            "<<...v",
            ".<<..>",
            "<vvv^>",
            "^vv>.>",
        ),
    ),
    _level(
        "第 3 关 · 纵深迷阵",
        (
            "<^^...>",
            "<.^^^>>",
            ".....<.",
            "<<^v...",
            "v.^..v.",
            "..<<>>.",
            "<vvvvv^",
        ),
    ),
    _level(
        "第 4 关 · 棋盘风暴",
        (
            "<....^.>",
            "v.v.v>..",
            "<^<..^..",
            "..<^>..>",
            "..<..<<v",
            "..v.v^.v",
            ".^.^v..>",
            "<^v>vvvv",
        ),
    ),
)


def _arrow_count(level: Level) -> int:
    return sum(symbol in ARROW_SYMBOLS for row in level.layout for symbol in row)


def _has_arrow_ahead(
    position: Tuple[int, int],
    direction: str,
    occupied: set[Tuple[int, int]],
    rows: int,
    cols: int,
) -> bool:
    """判断某个方向的前方是否已经放置了箭头。"""

    row_step, col_step = _DIRECTION_DELTAS[direction]
    row, col = position[0] + row_step, position[1] + col_step
    while 0 <= row < rows and 0 <= col < cols:
        if (row, col) in occupied:
            return True
        row += row_step
        col += col_step
    return False


def generate_random_level(
    template: Level,
    rng: Optional[random.Random] = None,
    *,
    attempts: int = 80,
) -> Level:
    """根据模板生成一张新的、保证可解的随机棋盘。

    生成器逐步随机决定箭头位置，再按照“最终消除顺序”的逆序放置箭头。
    每次放置时，只选择当前前方没有已放置箭头的方向，因此反向构造出的
    顺序一定是一条合法解法。随机重试用于避开高密度棋盘中的死位置。
    """

    if attempts <= 0:
        raise ValueError("生成尝试次数必须为正数")
    randomizer = rng or random.Random()
    rows, cols = template.rows, template.cols
    count = _arrow_count(template)
    all_positions = [(row, col) for row in range(rows) for col in range(cols)]
    directions = tuple(_DIRECTION_DELTAS)

    for _ in range(attempts):
        occupied: set[Tuple[int, int]] = set()
        remaining_positions = set(all_positions)
        symbols = [["." for _ in range(cols)] for _ in range(rows)]
        failed = False

        # 每次随机选择一个仍有可用方向的位置。这样既能随机位置，
        # 又不会因为预先抽到一个“最后无法放置”的位置而浪费整次尝试。
        for _ in range(count):
            candidates = []
            for position in sorted(remaining_positions):
                available = [
                    direction
                    for direction in directions
                    if not _has_arrow_ahead(position, direction, occupied, rows, cols)
                ]
                if available:
                    candidates.append((position, available))
            if not candidates:
                failed = True
                break
            position, available = randomizer.choice(candidates)
            direction = randomizer.choice(available)
            row, col = position
            symbols[row][col] = direction
            occupied.add(position)
            remaining_positions.remove(position)

        if not failed:
            return Level(
                name=template.name,
                layout=tuple("".join(row) for row in symbols),
                mistakes=template.mistakes,
            )

    raise RuntimeError("无法生成满足当前密度的可解随机关卡")


def get_levels() -> Tuple[Level, ...]:
    """返回固定关卡的不可变序列。"""

    return LEVELS
