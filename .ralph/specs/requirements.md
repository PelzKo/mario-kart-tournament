# Technical Specifications — Mario Kart Tournament App

## Overview
A Django web application for running and visualizing Mario Kart 8 Deluxe tournaments on multiple Nintendo Switches. Supports a group stage followed by a bracket (knockout) stage.

---

## System Architecture

- **Backend**: Django (Python 3.11+)
- **Database**: SQLite for development; PostgreSQL recommended for production
- **Frontend**: Django templates; minimal JavaScript (HTMX preferred for dynamic updates)
- **Hosting**: Private server (single-instance deployment)
- **Authentication**: Token-based tournament access (no user accounts required)
  - Admin token (URL path segment) → full edit access
  - Viewer token → read-only access

---

## Data Models

### Tournament
| Field | Type | Notes |
|---|---|---|
| id | UUID (PK) | Auto-generated |
| name | CharField | Optional display name |
| admin_token | CharField(32) | Random secret, grants edit access |
| viewer_token | CharField(32) | Random secret, grants read-only access |
| switch_count | PositiveIntegerField | Number of Nintendo Switches (default 2) |
| games_per_player | PositiveIntegerField | Group stage games per player (default 2) |
| stage | CharField | `setup` → `group` → `bracket` → `complete` |
| created_at | DateTimeField | Auto |

### Player
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| tournament | FK → Tournament | |
| name | CharField | |
| seed | PositiveIntegerField | Ranking after group stage (null until computed) |

### GroupGame
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| tournament | FK → Tournament | |
| round_number | PositiveIntegerField | 1-based |
| switch_number | PositiveIntegerField | 1-based |
| cup | CharField(50) | Selected cup (null until voting complete) |
| status | CharField | `pending` / `voting` / `in_progress` / `complete` |

### GroupGameParticipant
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| game | FK → GroupGame | |
| player | FK → Player | |
| points_earned | PositiveIntegerField | null until results entered |

### CupVote
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| game | FK → GroupGame | |
| player | FK → Player | |
| cup_name | CharField | Name of voted cup |

### BracketGame
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| tournament | FK → Tournament | |
| round_number | PositiveIntegerField | 1-based (1 = first round, highest = final) |
| game_number | PositiveIntegerField | Position within the round |
| switch_number | PositiveIntegerField | Assigned switch |
| cup | CharField(50) | Selected cup (null until chosen) |
| status | CharField | `pending` / `complete` |
| next_game | FK → BracketGame (nullable) | Where winners advance |

### BracketParticipant
| Field | Type | Notes |
|---|---|---|
| id | AutoField (PK) | |
| game | FK → BracketGame | |
| player | FK → Player (nullable) | Null until seeded/advanced |
| points_earned | PositiveIntegerField | null until results entered |
| advanced | BooleanField | True if this player advances to next round |

---

## Business Logic

### Group Stage Scheduling Algorithm
1. Given P players, S switches, and G games-per-player:
   - Total game slots needed = `P * G`
   - Target group size = 3 or 4 (max 4, Nintendo Switch limit)
   - Find a mix of 3-player and 4-player games that fills all slots, minimizing size variance
2. Assign each player to exactly G games across all rounds
3. Within each round, assign games to switches 1..S round-robin
4. Round number = `ceil(game_index / S)`

**Group size distribution example**: 7 players, 2 games each → 14 slots → prefer 4+4+3+3 (4 games) over 4+4+4+2.

### Cup Selection (Weighted Random)
```python
import random

def select_cup(votes: dict[str, int]) -> str:
    """
    votes: {cup_name: vote_count}
    Each cup gets (vote_count + 1) tickets. Draw one ticket at random.
    """
    tickets = []
    for cup, count in votes.items():
        tickets.extend([cup] * (count + 1))
    return random.choice(tickets)
```
All cups start with 1 ticket even with zero votes, ensuring every cup has a chance.

### Bracket Seeding
```python
import math

def bracket_size(total_players: int) -> int:
    """Largest power of 2 strictly less than total_players."""
    exp = math.floor(math.log2(total_players))
    size = 2 ** exp
    if size == total_players:
        size = size // 2
    return size
```
Examples: 10→8, 15→8, 20→16, 32→16, 16→8

- Top `bracket_size` players by group stage total points advance
- Seeding: seed 1 vs seed N, seed 2 vs seed N-1, etc. (4 players per game)
- Each bracket game has exactly 4 players; top 2 advance

### Bracket Structure
- Round 1: `bracket_size // 4` games (4 players each)
- Round 2: `bracket_size // 8` games (winners from round 1, 4 per game)
- ...until the final (1 game, 4 players → top 2 = champions)

---

## URL Structure

```
/                                               # Landing / create tournament
/tournament/<viewer_token>/                     # Read-only viewer
/tournament/<admin_token>/admin/                # Organizer dashboard (group stage)
/tournament/<admin_token>/bracket/              # Organizer bracket view
/tournament/<admin_token>/game/<game_id>/results/   # Enter group stage results
/tournament/<admin_token>/game/<game_id>/vote/      # Cup voting for a game
/tournament/<admin_token>/bracket/<game_id>/results/ # Enter bracket results
```

---

## UI Requirements

### Tournament Setup Page (`/`)
- Dynamic player name inputs (add/remove rows with JS)
- Switch count input (number, default 2, min 1)
- Games per player input (number, default 2, min 1)
- On submit: save tournament, redirect to admin URL, display shareable viewer URL prominently

### Group Stage View (organizer)
- Two tabs: "Group Stage" | "Bracket"
- Grid layout: rows = rounds, columns = switches
- Each cell shows: game status, player names, assigned cup (after voting), points (after results)
- Click a cell → open results/voting modal or sub-page

### Bracket View (organizer)
- Standard left-to-right bracket tree
- Each node: 4 player names (or TBD), switch number, cup, status indicator
- Click a game node → enter results for that game

### Viewer Mode
- Same layout as organizer views
- All forms, buttons, and edit links hidden
- Status indicators and scores visible

---

## Mario Kart 8 Deluxe Cup List

**Base game (8 cups):**
Mushroom, Flower, Star, Special, Shell, Banana, Leaf, Lightning

**Booster Course Pass DLC (8 cups):**
Golden Dash, Lucky Cat, Turnip, Propeller, Rock, Moon, Fruit, Boomerang

**Additional DLC cups:**
Feather, Cherry, Acorn, Spiny, Egg, Triforce, Crossing, Bell

Store as a constant in the Django app (e.g., `tournament/constants.py`).

---

## Performance Requirements
- Page load < 2 seconds for all tournament views
- Cup selection and result entry should not require full page reload (use HTMX or fetch)
- Support up to 32 players without degradation

---

## Security Considerations
- Admin token: `secrets.token_urlsafe(24)` — minimum 24 bytes of entropy
- Viewer token: same generation method
- Validate all form inputs server-side
- Never trust client-submitted player/game IDs without verifying they belong to the tournament
- CSRF protection enabled (Django default — do not disable)
- No sensitive data in URLs beyond the tokens themselves

---

## Integration Requirements
- None (standalone app, no external APIs required)
- Optional: HTMX polling on viewer page for live score updates
