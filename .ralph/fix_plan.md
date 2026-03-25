# Ralph Fix Plan

## High Priority
- [x] **Django project scaffold** — create Django project + `tournament` app, configure settings, install dependencies (requirements.txt)
- [x] **Data models** — implement `Tournament`, `Player`, `GroupGame`, `GroupGameParticipant`, `CupVote`, `BracketGame`, `BracketParticipant` models with migrations
- [x] **Tournament creation view** — form for player names, switch count, games-per-player; generate admin token + viewer token on save; display both URLs
- [x] **Group stage scheduler** — algorithm to distribute players across rounds/switches fairly (equal group sizes, each player plays N games, max 4 per game)
- [x] **Group stage grid UI** — display grid (rows = rounds, columns = switches) with player names, status, and cup per cell
- [x] **Cups and races** - Added `CUP_TRACKS` dict (24 cups × 4 tracks = 96 total) and `ALL_TRACKS` flat list to constants.py
- [x] **Docker** - Added Dockerfile (gunicorn + whitenoise), docker-compose.yml (volume for SQLite), .dockerignore; settings updated for DATA_DIR
- [x] **Remove lines in bracket** - The lines in the bracket stage that should look like a tree are not looking good, so remove them again so it is just a list of the games without the dashes representing the branches to the next game
- [x] **QR-Code** - Create a QR code linking to the viewer page and display it in a corner both on the admin page and the viewer page
- [x] **Blacklist** - Allow a user to blacklist cups or tracks
- [x] **Rematch** - After a tournament have a button so you can do a rematch with the same people and parameters
- [x] **HTMX** - Use htmx for smoother and better updating the viewer live page
- [x] **Edit bracket games** - Make it possible for an admin to edit a bracket game result, maybe changing who advances. Only make it possible if the next game has not added points yet


## Medium Priority
- [x] **Cup voting system** — per-game vote form; weighted-random cup selection (votes + 1 per cup); save selected cup to GroupGame
- [x] **Group stage results entry** — click a game cell → enter points per player; save results; update cumulative standings
- [x] **Group stage standings** — leaderboard showing total group stage points per player, sorted descending
- [x] **Bracket generation** — after group stage complete, seed top-N players (N = largest power of 2 strictly < total) into bracket; assign switches
- [x] **Bracket tree UI** — visual bracket display; show 4 players per node, switch number, cup, status
- [x] **Bracket results entry** — click a bracket game → enter points; top 2 auto-advance; repeat until final
- [x] **Tie breaker** - if there is a tie at the end of a game in the bracket, choose the person that had the most points in the group stage and write a small text in cursive under the names explaining this (but only in the event of a tie)
- [x] **Finale** - If only one game remains, change text in point input form (no more people advance), and afterward show some kind of podium with the top three
- [x] **Improvements** - IMPROVEMENT_IDEAS.md written with 12 concrete suggestions (password, stats, bracket lines, QR code, chat, print view, player profiles, cup blacklist, HTMX, rematch, undo, i18n)
- [x] **Tie breaker finale** - After finale, if top scorers are tied, a tiebreaker BracketGame is auto-created (random cup+race from ALL_TRACKS, no voting). Podium shows tied players alphabetically per position.
- [x] **Only warning for duplicate name** - When creating a tournament, check whether there are duplicate names before allowing the user to submit, because otherwise all the data the user inputted is gone and they need to reenter everything if a name is there twice
- [x] **Bracket naming** - fix the bracket naming so the last one is finale, the one before that semi-finale, the one before that semi-semi-finale and so on (so adding a "semi-" for every level


## Low Priority
- [x] **Viewer mode** — read-only tournament view via shareable URL; no forms or action buttons rendered
- [x] **Fix viewer mode buttons** - fix "Group Stage" and "Bracket" buttons in viewer mode so they show the right things
- [x] **Auto-refresh / HTMX polling** — viewer page refreshes automatically (meta refresh every 30s; stops when tournament is complete)
- [x] **Responsive styling** — media query @720px: sidebar stacks, form grids collapse, grid gets horizontal scroll, tabs/buttons shrink
- [x] **Result correction** — group stage: "Edit" button pre-populates form with existing scores; bracket correction skipped (cascade complexity)
- [x] **Tournament list page** — landing page listing recent tournaments with admin/viewer links; "/" shows list, "/new/" creates
- [x] **Password protection** - password_hash on Tournament; admin_login view + session auth; all admin views protected; creator auto-authenticated on creation
- [x] **Statistics** - Third tab (after completion): cup usage frequency, player pairings, best single score, avg pts/game. Accessible via admin + viewer token.
- [x] **Visual Brackets** - CSS bracket-pair connectors with horizontal stubs + vertical bar connecting game pairs to next round
- [x] **Add points stop** - Warning banner shown in bracket_results when any participant is still TBD; form still submittable but clearly flagged
- [x] **no submit without points** - When warning banner is shown in bracket results that any participant is still TBD, make form not submittable

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
