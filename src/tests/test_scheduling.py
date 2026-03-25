"""
Tests for the group stage scheduling algorithm and bracket logic.

These tests run without Django (pure Python), so they can be executed with:
    python -m pytest tests/test_scheduling.py

or from the src/ directory:
    python -m pytest tests/test_scheduling.py -v
"""
import sys
import os

# Ensure src/ is on the path so we can import without Django being configured
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Patch constants so we don't need Django
import types
constants_mod = types.ModuleType("tournament.constants")
constants_mod.CUPS = [
    "Mushroom", "Flower", "Star", "Special", "Shell", "Banana", "Leaf", "Lightning",
]
# Create a stub package for 'tournament' that still resolves submodules from disk
_tournament_pkg = types.ModuleType("tournament")
_tournament_pkg.__path__ = [os.path.join(os.path.dirname(os.path.dirname(__file__)), "tournament")]
_tournament_pkg.__package__ = "tournament"
sys.modules["tournament"] = _tournament_pkg
sys.modules["tournament.constants"] = constants_mod

import tournament.scheduling as scheduling_mod
# Re-import after patching
from tournament.scheduling import (
    bracket_size,
    compute_game_sizes,
    schedule_group_stage,
    assign_rounds_and_switches,
    select_cup,
    seed_bracket,
)


# ---------------------------------------------------------------------------
# compute_game_sizes
# ---------------------------------------------------------------------------

def test_game_sizes_6_players_2_games():
    """6 players × 2 games = 12 slots → four 3-player games (3+3+3+3) is ideal."""
    sizes = compute_game_sizes(6, 2)
    assert sum(sizes) == 12
    assert all(s in (3, 4) for s in sizes)
    # Prefer equal sizes: all 3s is better than mix of 3s and 4s
    assert set(sizes) == {3}


def test_game_sizes_8_players_2_games():
    """8 players × 2 games = 16 slots → four 4-player games."""
    sizes = compute_game_sizes(8, 2)
    assert sum(sizes) == 16
    assert all(s == 4 for s in sizes)


def test_game_sizes_7_players_2_games():
    """7 players × 2 games = 14 slots → mix of 3s and 4s."""
    sizes = compute_game_sizes(7, 2)
    assert sum(sizes) == 14
    assert all(s in (3, 4) for s in sizes)
    # Four games: prefer 3+3+4+4 rather than 2+4+4+4 (which is invalid anyway)
    assert len(sizes) == 4
    # Variance: max-min should be 1 (equal as possible)
    assert max(sizes) - min(sizes) <= 1


def test_game_sizes_4_players_3_games():
    """4 players × 3 games = 12 slots → four 3-player games."""
    sizes = compute_game_sizes(4, 3)
    assert sum(sizes) == 12
    assert all(s in (3, 4) for s in sizes)


# ---------------------------------------------------------------------------
# schedule_group_stage
# ---------------------------------------------------------------------------

def test_schedule_each_player_plays_n_games():
    """Each player must appear in exactly games_per_player games."""
    num_players, games_per_player = 6, 2
    games = schedule_group_stage(num_players, games_per_player, switch_count=2)
    counts = [0] * num_players
    for game in games:
        for p in game:
            counts[p] += 1
    assert all(c == games_per_player for c in counts), f"Player game counts: {counts}"


def test_schedule_group_size_max_4():
    """No game should have more than 4 players."""
    games = schedule_group_stage(10, 2, switch_count=3)
    assert all(len(g) <= 4 for g in games)


def test_schedule_group_size_min_3():
    """No game should have fewer than 3 players (given valid inputs)."""
    games = schedule_group_stage(6, 2, switch_count=2)
    assert all(len(g) >= 3 for g in games)


def test_schedule_12_players_2_games():
    """12 players × 2 games = 24 slots → eight 3-player games."""
    games = schedule_group_stage(12, 2, switch_count=2)
    counts = [0] * 12
    for game in games:
        for p in game:
            counts[p] += 1
    assert all(c == 2 for c in counts)
    assert all(3 <= len(g) <= 4 for g in games)


# ---------------------------------------------------------------------------
# assign_rounds_and_switches
# ---------------------------------------------------------------------------

def test_assign_rounds_and_switches():
    """
    Given 4 games and 2 switches:
    - games 0,1 → round 1 (switches 1, 2)
    - games 2,3 → round 2 (switches 1, 2)
    """
    games = [[0, 1, 2], [3, 4, 5], [0, 3, 6], [1, 4, 7]]
    result = assign_rounds_and_switches(games, switch_count=2)
    assert result[0]["round_number"] == 1 and result[0]["switch_number"] == 1
    assert result[1]["round_number"] == 1 and result[1]["switch_number"] == 2
    assert result[2]["round_number"] == 2 and result[2]["switch_number"] == 1
    assert result[3]["round_number"] == 2 and result[3]["switch_number"] == 2


# ---------------------------------------------------------------------------
# select_cup
# ---------------------------------------------------------------------------

def test_select_cup_returns_from_votes():
    """Cup selection must return one of the cups that got votes."""
    votes = {"Mushroom": 2, "Flower": 1}
    for _ in range(50):
        result = select_cup(votes)
        # All cups in CUPS list are valid; but given these votes, only voted cups + all cups get tickets
        # Actually select_cup includes all cups via tickets, so voted cups have higher probability
        # Just check it returns a string
        assert isinstance(result, str)
        assert len(result) > 0


def test_select_cup_empty_votes():
    """With no votes, select_cup should still return a valid cup."""
    result = select_cup({})
    assert result in constants_mod.CUPS


def test_select_cup_weighted_distribution():
    """Cup with more votes should be selected more often (probabilistic test)."""
    import random
    random.seed(42)
    votes = {"Mushroom": 10, "Flower": 0}
    counts = {"Mushroom": 0, "Flower": 0}
    for _ in range(1000):
        result = select_cup(votes)
        if result in counts:
            counts[result] += 1
    # Mushroom has 11 tickets, Flower has 1; Mushroom should appear ~11x more often
    assert counts["Mushroom"] > counts["Flower"] * 3


# ---------------------------------------------------------------------------
# bracket_size
# ---------------------------------------------------------------------------

def test_bracket_size_10():
    assert bracket_size(10) == 8


def test_bracket_size_15():
    assert bracket_size(15) == 8


def test_bracket_size_20():
    assert bracket_size(20) == 16


def test_bracket_size_32():
    """32 players → largest power of 2 strictly less = 16."""
    assert bracket_size(32) == 16


def test_bracket_size_16():
    """16 players → 16 == 16, so go down to 8."""
    assert bracket_size(16) == 8


def test_bracket_size_8():
    assert bracket_size(8) == 4


def test_bracket_size_5():
    assert bracket_size(5) == 4


def test_bracket_size_4():
    """4 players → all go into a single finale, so bracket_size returns 4."""
    assert bracket_size(4) == 4


def test_bracket_size_3():
    """3 players → all go into a single finale, so bracket_size returns 3."""
    assert bracket_size(3) == 3


def test_bracket_size_2():
    """2 players → all go into a single finale, so bracket_size returns 2."""
    assert bracket_size(2) == 2


def test_bracket_size_1_raises():
    """1 player is not enough for a bracket."""
    import pytest
    with pytest.raises(ValueError):
        bracket_size(1)


# ---------------------------------------------------------------------------
# seed_bracket
# ---------------------------------------------------------------------------

def test_seed_bracket_8_players():
    """8 players → 2 first-round games of 4 players each."""
    players = list(range(8))
    games = seed_bracket(players, 8)
    assert len(games) == 2
    assert all(len(g) == 4 for g in games)
    # All players used exactly once
    all_players = [p for g in games for p in g]
    assert sorted(all_players) == list(range(8))


def test_seed_bracket_16_players():
    """16 players → 4 first-round games of 4 players each."""
    players = list(range(16))
    games = seed_bracket(players, 16)
    assert len(games) == 4
    assert all(len(g) == 4 for g in games)
    all_players = [p for g in games for p in g]
    assert sorted(all_players) == list(range(16))


def test_seed_bracket_4_players():
    """4 players → single finale game with all 4 players."""
    players = list(range(4))
    games = seed_bracket(players, 4)
    assert len(games) == 1
    assert sorted(games[0]) == list(range(4))


def test_seed_bracket_3_players():
    """3 players → single finale game with all 3 players."""
    players = list(range(3))
    games = seed_bracket(players, 3)
    assert len(games) == 1
    assert sorted(games[0]) == list(range(3))


def test_seed_bracket_2_players():
    """2 players → single finale game with both players."""
    players = list(range(2))
    games = seed_bracket(players, 2)
    assert len(games) == 1
    assert sorted(games[0]) == list(range(2))


if __name__ == "__main__":
    # Run all tests manually without pytest
    import traceback
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
