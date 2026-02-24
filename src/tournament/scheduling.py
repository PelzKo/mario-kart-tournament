"""
Group stage scheduling algorithm.

Given P players, S switches, and G games-per-player:
- Total game slots = P * G
- Each game has 3 or 4 players (max 4 due to Nintendo Switch limit)
- Distribute players so each plays exactly G games
- Minimize size variance between games (prefer 3+3 over 4+2)
- Assign games to rounds and switches round-robin

Returns a list of games, each game is a list of player indices.
"""
import math
import random
from typing import List


def compute_game_sizes(num_players: int, games_per_player: int) -> List[int]:
    """
    Determine how many players should be in each game.

    Total slots = num_players * games_per_player.
    Each game has 3 or 4 players.
    Minimize variance: use as many 3-player games as possible before going to 4.

    Returns a list of game sizes (each is 3 or 4).
    """
    total_slots = num_players * games_per_player

    # total_slots = 3*a + 4*b where a+b = num_games
    # We want to minimise variance, so prefer equal sizes.
    # Try all combos: for each number of 4-player games b, check if a = (total_slots - 4b) / 3 is integer.
    best = None
    for b in range(0, total_slots // 4 + 1):
        remainder = total_slots - 4 * b
        if remainder >= 0 and remainder % 3 == 0:
            a = remainder // 3
            sizes = [4] * b + [3] * a
            # Score: prefer smaller variance (more equal sizes)
            if best is None:
                best = sizes
            else:
                # Pick sizes with smaller max-min range
                if (max(sizes) - min(sizes)) < (max(best) - min(best)):
                    best = sizes
                elif (max(sizes) - min(sizes)) == (max(best) - min(best)):
                    # Same variance: prefer more games (smaller sizes)
                    if len(sizes) > len(best):
                        best = sizes
    if best is None:
        raise ValueError(
            f"Cannot schedule {num_players} players with {games_per_player} games each "
            f"into groups of 3-4."
        )
    return best


def schedule_group_stage(
    num_players: int, games_per_player: int, switch_count: int
) -> List[List[int]]:
    """
    Schedule group stage games.

    Returns a list of games in order. Each game is a list of player indices (0-based).
    The position in the returned list determines round and switch assignment:
      - game i is on round ceil((i+1) / switch_count), switch (i % switch_count) + 1

    Algorithm:
    1. Compute game sizes
    2. Assign players to games using a greedy approach:
       - Sort players by number of games remaining (descending), then randomize ties
       - For each game slot, pick the top-N players who haven't played together most recently
    """
    game_sizes = compute_game_sizes(num_players, games_per_player)
    num_games = len(game_sizes)

    # Track how many more games each player needs
    games_remaining = [games_per_player] * num_players
    # Track recent co-players to avoid repeating pairings
    recent_partners: List[set] = [set() for _ in range(num_players)]

    games: List[List[int]] = []

    for size in game_sizes:
        # Sort players: those with most games remaining go first
        # Break ties by fewest recent partners with others in the candidate pool
        eligible = [p for p in range(num_players) if games_remaining[p] > 0]

        # Greedy selection: pick player with most games remaining,
        # then choose companions who haven't played together recently
        eligible_sorted = sorted(eligible, key=lambda p: -games_remaining[p])

        # Seed with the player who has most games remaining
        game = [eligible_sorted[0]]
        remaining_eligible = [p for p in eligible_sorted if p != game[0]]

        while len(game) < size and remaining_eligible:
            # Score each candidate: prefer players with more games remaining,
            # and fewer overlaps with current game members
            def score(p):
                overlap = sum(1 for g in game if g in recent_partners[p])
                return (-games_remaining[p], overlap)

            remaining_eligible.sort(key=score)
            game.append(remaining_eligible.pop(0))

        if len(game) < size:
            # Fallback: pull from any player with games remaining (shouldn't happen normally)
            for p in range(num_players):
                if p not in game and games_remaining[p] > 0:
                    game.append(p)
                    if len(game) == size:
                        break

        # Update tracking
        for p in game:
            games_remaining[p] -= 1
            recent_partners[p].update(g for g in game if g != p)

        games.append(game)

    return games


def assign_rounds_and_switches(
    games: List[List[int]], switch_count: int
) -> List[dict]:
    """
    Given ordered list of games (each is a list of player indices),
    assign round numbers and switch numbers.

    Returns list of dicts: {players: [...], round_number: int, switch_number: int}
    """
    result = []
    for i, players in enumerate(games):
        round_number = i // switch_count + 1
        switch_number = i % switch_count + 1
        result.append(
            {
                "players": players,
                "round_number": round_number,
                "switch_number": switch_number,
            }
        )
    return result


def select_cup(votes: dict) -> str:
    """
    Weighted-random cup selection.

    votes: {cup_name: vote_count}
    Each cup gets (vote_count + 1) tickets.
    Draw one ticket at random.

    If votes is empty (no participants voted), falls back to uniform random
    over all cups.
    """
    from .constants import CUPS

    if not votes:
        return random.choice(CUPS)

    tickets = []
    for cup, count in votes.items():
        tickets.extend([cup] * (count + 1))

    return random.choice(tickets)


def bracket_size(total_players: int) -> int:
    """
    Largest power of 2 strictly less than total_players.

    Examples: 10→8, 15→8, 20→16, 32→16, 16→8
    """
    if total_players < 2:
        raise ValueError("Need at least 2 players for a bracket")
    exp = math.floor(math.log2(total_players))
    size = 2 ** exp
    if size == total_players:
        size = size // 2
    return size


def seed_bracket(players_by_seed: list, bracket_sz: int) -> List[List]:
    """
    Given players sorted by seed (best first), take the top bracket_sz players
    and arrange them into first-round bracket games of 4 players each.

    Seeding: game 1 gets seeds 1, N, N-1, 2 (top and bottom seeds together),
    in a snake pattern.

    Returns: list of games, each game is a list of players.
    """
    top = players_by_seed[:bracket_sz]
    num_games = bracket_sz // 4

    # Classic bracket seeding: pair seed 1 with N, 2 with N-1, etc.
    # For groups of 4: game i gets players at positions i and (bracket_sz-1-i)
    # and the middle two.
    # With groups of 4 we do: game i has seeds [i+1, bracket_sz-i, bracket_sz//2-i, bracket_sz//2+i+1]
    # but simpler: just snake-fill groups of 4.

    # Snake seeding for groups of 4:
    # Sort indices in a snake pattern: 0, N-1, 1, N-2, 2, N-3, ...
    indices = []
    lo, hi = 0, bracket_sz - 1
    toggle = True
    while lo <= hi:
        if toggle:
            indices.append(lo)
            lo += 1
        else:
            indices.append(hi)
            hi -= 1
        toggle = not toggle

    games = []
    for i in range(num_games):
        game_indices = indices[i * 4: (i + 1) * 4]
        games.append([top[j] for j in game_indices])

    return games
