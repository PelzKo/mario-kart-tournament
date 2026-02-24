# Ralph Fix Plan

## High Priority
- [x] **Django project scaffold** — create Django project + `tournament` app, configure settings, install dependencies (requirements.txt)
- [x] **Data models** — implement `Tournament`, `Player`, `GroupGame`, `GroupGameParticipant`, `CupVote`, `BracketGame`, `BracketParticipant` models with migrations
- [x] **Tournament creation view** — form for player names, switch count, games-per-player; generate admin token + viewer token on save; display both URLs
- [x] **Group stage scheduler** — algorithm to distribute players across rounds/switches fairly (equal group sizes, each player plays N games, max 4 per game)
- [x] **Group stage grid UI** — display grid (rows = rounds, columns = switches) with player names, status, and cup per cell

## Medium Priority
- [x] **Cup voting system** — per-game vote form; weighted-random cup selection (votes + 1 per cup); save selected cup to GroupGame
- [x] **Group stage results entry** — click a game cell → enter points per player; save results; update cumulative standings
- [x] **Group stage standings** — leaderboard showing total group stage points per player, sorted descending
- [x] **Bracket generation** — after group stage complete, seed top-N players (N = largest power of 2 strictly < total) into bracket; assign switches
- [x] **Bracket tree UI** — visual bracket display; show 4 players per node, switch number, cup, status
- [x] **Bracket results entry** — click a bracket game → enter points; top 2 auto-advance; repeat until final

## Low Priority
- [x] **Viewer mode** — read-only tournament view via shareable URL; no forms or action buttons rendered
- [ ] **Auto-refresh / HTMX polling** — viewer page refreshes automatically to show live standings
- [ ] **Responsive styling** — CSS for usable display on phones/tablets at the venue
- [ ] **Result correction** — allow organizer to edit mistaken results
- [ ] **Tournament list page** — landing page listing recent tournaments with admin/viewer links

## Completed
- [x] Project initialization
- [x] Django project scaffold + data models + migrations (manual)
- [x] Tournament creation form + URL display
- [x] Group stage scheduler algorithm (tested)
- [x] Group stage grid + standings UI
- [x] Cup voting + weighted random cup selection
- [x] Group stage results entry
- [x] Bracket generation (power-of-2 seeding)
- [x] Bracket tree UI + results entry
- [x] Viewer (read-only) mode

## Notes
- Nintendo Switch hardware limit: max 4 players per game
- Bracket size rule: `2 ** floor(log2(total_players))`, but if that equals total_players use `// 2` — verify edge cases
- Cup weighted random: each cup gets `(votes + 1)` tickets — even zero-vote cups are selectable
- Group scheduler: minimize variance between game sizes (prefer 3+3 over 4+2 for 6 players)
- See `.ralph/specs/requirements.md` for full data model, URL structure, and cup list
- Django must be installed: `pip install -r src/requirements.txt`
- Run: `cd src && python manage.py migrate && python manage.py runserver`
