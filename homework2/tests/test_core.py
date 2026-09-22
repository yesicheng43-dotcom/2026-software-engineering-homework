import random
import unittest

from homework2.core import Board, GameSession, GameStatus, find_solution, is_solvable
from homework2.levels import LEVELS, Level, generate_random_level


class BoardRuleTests(unittest.TestCase):
    def test_invalid_level_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            Level("不规则", (">..", ".."))
        with self.assertRaises(ValueError):
            Level("非法字符", ("x",))

    def test_all_fixed_levels_are_solvable(self):
        self.assertGreaterEqual(len(LEVELS), 3)
        for level in LEVELS:
            with self.subTest(level=level.name):
                self.assertTrue(is_solvable(level))
                self.assertIsNotNone(find_solution(level))

    def test_random_level_preserves_density_and_is_solvable(self):
        template = LEVELS[-1]
        generated = generate_random_level(template, random.Random(20260922))
        template_count = sum(symbol in "^v<>" for row in template.layout for symbol in row)
        generated_count = sum(symbol in "^v<>" for row in generated.layout for symbol in row)
        self.assertEqual((generated.rows, generated.cols), (template.rows, template.cols))
        self.assertEqual(generated_count, template_count)
        self.assertTrue(is_solvable(generated))

    def test_random_level_changes_between_generations(self):
        template = LEVELS[1]
        rng = random.Random(7)
        first = generate_random_level(template, rng)
        second = generate_random_level(template, rng)
        self.assertNotEqual(first.layout, second.layout)

    def test_randomized_session_regenerates_on_restart(self):
        session = GameSession((LEVELS[0],), randomize=True, rng=random.Random(11))
        session.start()
        first = session.current_level.layout
        session.restart()
        second = session.current_level.layout
        self.assertNotEqual(first, second)
        self.assertTrue(is_solvable(session.current_level))

    def test_path_only_checks_the_forward_ray(self):
        level = Level("方向", ("<..", ".^.", "..>"))
        board = Board(level)
        self.assertTrue(board.can_fly(board.arrow_at(0, 0)))
        self.assertTrue(board.can_fly(board.arrow_at(2, 2)))

    def test_blocker_is_found_in_same_row_or_column(self):
        level = Level("阻挡", (">.>", "...", "v.."))
        board = Board(level)
        left = board.arrow_at(0, 0)
        self.assertEqual(board.blocking_arrow(left).position, (0, 2))
        self.assertIsNone(board.blocking_arrow(board.arrow_at(0, 2)))

    def test_edge_arrow_does_not_read_out_of_bounds(self):
        for symbol, layout in (
            ("^", ("^",)),
            ("v", ("v",)),
            ("<", ("<",)),
            (">", (">",)),
        ):
            with self.subTest(symbol=symbol):
                board = Board(Level("边界", layout))
                self.assertTrue(board.can_fly(board.arrow_at(0, 0)))


class GameSessionTests(unittest.TestCase):
    def setUp(self):
        self.level = Level("测试关", (">.>", "...", "v.."))
        self.session = GameSession((self.level, Level("第二关", ("^",))))
        self.session.start()

    def test_clear_arrow_removes_it_and_updates_remaining_count(self):
        result = self.session.click(0, 2)
        self.assertEqual(result.kind, "fly")
        self.assertEqual(self.session.board.remaining, 2)
        self.assertEqual(self.session.status, GameStatus.PLAYING)

    def test_clicking_empty_cell_does_not_change_state(self):
        result = self.session.click(1, 1)
        self.assertEqual(result.kind, "invalid")
        self.assertEqual(self.session.board.remaining, 3)
        self.assertEqual(self.session.mistakes_left, 3)
        self.assertEqual(self.session.status, GameStatus.PLAYING)

    def test_blocked_arrow_consumes_one_mistake_and_stays(self):
        result = self.session.click(0, 0)
        self.assertEqual(result.kind, "blocked")
        self.assertEqual(result.blocker.position, (0, 2))
        self.assertEqual(self.session.mistakes_left, 2)
        self.assertIsNotNone(self.session.board.arrow_at(0, 0))

    def test_mistakes_exhaustion_enters_failed_state(self):
        for _ in range(3):
            result = self.session.click(0, 0)
        self.assertEqual(result.kind, "blocked")
        self.assertEqual(self.session.status, GameStatus.FAILED)
        self.assertEqual(self.session.mistakes_left, 0)
        self.assertEqual(self.session.click(0, 2).kind, "ignored")

    def test_restart_restores_layout_and_mistakes(self):
        self.session.click(0, 2)
        self.session.click(0, 0)
        self.session.restart()
        self.assertEqual(self.session.status, GameStatus.PLAYING)
        self.assertEqual(self.session.mistakes_left, 3)
        self.assertEqual(self.session.board.remaining, 3)

    def test_last_arrow_enters_won_and_next_level_can_start(self):
        self.session.click(0, 2)
        self.session.click(2, 0)
        result = self.session.click(0, 0)
        self.assertEqual(result.status, GameStatus.WON)
        self.assertFalse(self.session.next_level() is False)
        self.assertEqual(self.session.level_index, 1)
        self.assertEqual(self.session.status, GameStatus.PLAYING)

    def test_finishing_last_level_sets_all_cleared(self):
        self.session.start(1)
        self.session.click(0, 0)
        self.assertEqual(self.session.status, GameStatus.WON)
        self.assertFalse(self.session.next_level())
        self.assertEqual(self.session.status, GameStatus.ALL_CLEARED)


if __name__ == "__main__":
    unittest.main()
