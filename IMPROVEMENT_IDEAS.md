# Improvement Ideas for Mario Kart Tournament

Ideas from the perspective of a daily user running tournaments with friends.

---

## 1. Password Protection for Admin Pages
**What:** When creating a tournament, the organizer sets a password. The viewer URL is always public, but the admin URL requires entering the password on first visit (stored in the session).

**Why valuable:** Right now anyone who guesses or finds the admin token URL can enter results. A password makes it safe to share the viewer link widely without worrying about sabotage.

**Difficulty:** Easy (2–3 hours). Add a `password_hash` field to Tournament, a simple login view that writes to the session, and a decorator that checks the session before allowing admin actions.

---

## 2. Statistics Tab After Tournament Completion
**What:** A third tab that appears once the tournament is complete, showing:
- Most popular cups (voted for or selected most often)
- Which players raced together most frequently
- Biggest point swing (highest single-game score)
- Head-to-head records between players
- Average points per game per player

**Why valuable:** After the excitement dies down, people love reliving the tournament. Stats give lasting talking points ("you and Alex always ended up racing together") and make the app feel polished.

**Difficulty:** Medium (4–6 hours). Pure read-only Django view that aggregates existing data; no new models needed.

---

## 3. Visual Bracket Tree Lines
**What:** SVG or CSS lines connecting bracket game boxes to show which game feeds into which. Each game box has curved lines going to the parent game on the right.

**Why valuable:** The current bracket is readable but not visually intuitive. Traditional tournament brackets have lines — without them it takes mental effort to trace the path.

**Difficulty:** Medium (3–5 hours). Can be done with CSS flexbox + pseudo-elements (borders as lines) or inline SVG generated in the template. No JS required.

---

## 4. QR Code for Viewer Link
**What:** On the tournament created/admin page, display a QR code next to the viewer URL that players can scan immediately with their phones.

**Why valuable:** In a LAN/couch tournament setting, nobody wants to type a long URL. A QR code on a laptop or tablet lets everyone join the live view in under 5 seconds.

**Difficulty:** Easy (1–2 hours). Use the `qrcode` Python library to generate a base64-encoded PNG and embed it inline in the template. No new routes needed.

---

## 5. Per-Game Chat / Commentary Log
**What:** A simple append-only log on the bracket and dashboard pages where the organizer can type a short message (e.g., "Epic race on Rainbow Road!", "Alice wins 1st by 1 point"). Messages are shown in a scrollable sidebar feed visible in both admin and viewer mode.

**Why valuable:** Gives spectators context during live viewing. Makes the tournament feel like a sports broadcast rather than a spreadsheet.

**Difficulty:** Medium (4–6 hours). New `TournamentMessage` model (tournament FK, text, timestamp), a POST endpoint, displayed in templates. Viewer auto-refresh will pick up new messages automatically.

---

## 6. Group Stage Schedule Export / Print View
**What:** A printable, printer-friendly version of the group stage schedule (no CSS background colors, larger text, black-and-white friendly). Accessible at a `/print/` URL variant or via a "Print" button that applies a `@media print` stylesheet.

**Why valuable:** Many organizers print the schedule to hand to players or post on a wall. The current dark-themed UI wastes ink and is hard to read on paper.

**Difficulty:** Easy (1–2 hours). Add a `@media print` CSS block in base.html that overrides background colors, hides navigation/buttons, and sets font colors to black.

---

## 7. Player Profiles with Win History
**What:** Each player gets a persistent profile (name + optional avatar emoji). When a player name is entered at tournament creation, it's matched against existing profiles. After tournament completion, their placement is recorded. A profile page shows their tournament history, win/loss record, and total points across all tournaments.

**Why valuable:** Regular players (friend groups who run weekly tournaments) love seeing their long-term record. Creates a meta-game of "who's the best overall."

**Difficulty:** Hard (8–12 hours). Requires new `PlayerProfile` model, fuzzy name matching at tournament creation, and a profile page. Careful UX needed for matching existing vs. new players.

---

## 8. Cup/Track Blacklist
**What:** When setting up a tournament, the organizer can check off cups they don't want included (e.g., "we don't have the DLC" or "we're sick of Rainbow Road"). Voting only shows available cups; cup selection only picks from the allowed set.

**Why valuable:** Not every group owns all DLC. Also, after playing a specific cup many times, groups often want to ban it for variety. This is a frequent real-world request.

**Difficulty:** Easy (2–3 hours). Add a many-to-many or JSON field on Tournament for excluded cups; filter the `CUPS` list in voting and random selection views.

---

## 9. Live Score Animations (HTMX)
**What:** Replace the 30-second meta-refresh on viewer pages with HTMX polling. Only the score grid/bracket section reloads (not the full page), and new scores fade in with a CSS transition. Show a "Last updated X seconds ago" indicator.

**Why valuable:** The current full-page refresh is jarring and loses scroll position. Partial updates feel professional and keep viewers engaged without distraction.

**Difficulty:** Medium (3–5 hours). Add HTMX to the project (CDN link), replace the meta refresh with `hx-get` + `hx-trigger="every 15s"` on the bracket/grid container, add a partial-render view that returns just that fragment.

---

## 10. Rematch / New Tournament from Template
**What:** A "Run again with the same players" button on the tournament completion page. It pre-fills the create form with all the same player names, switch count, and games-per-player, so the organizer only has to click "Create" to start a rematch.

**Why valuable:** After a tournament, "okay one more!" is the most common request. Re-entering 8–16 names is tedious. One click to rematch removes all friction.

**Difficulty:** Easy (1–2 hours). Pass the current tournament's data as query parameters to the `/new/` URL, and pre-populate the form fields using those values.

---

## 11. Result Undo / Admin History Log
**What:** After entering bracket results, the organizer can click "Undo last result" (within a 5-minute window) to revert a game back to pending and re-open the score entry form. All result changes are logged with a timestamp.

**Why valuable:** Typos in score entry happen constantly ("I entered 60 instead of 16"). Currently there's no way to fix bracket results once submitted, which can derail a tournament.

**Difficulty:** Hard (6–10 hours). Requires storing result history, logic to cascade-undo bracket advancement (clearing the next game's TBD slots), and UI for the undo action.

---

## 12. Multi-language Support (i18n)
**What:** Full Django i18n support for the UI, starting with German and English (the two most likely languages for the target user base based on server location).

**Why valuable:** If the tournament is shared with non-English-speaking friends, a localized UI removes confusion. Most template strings are short and easy to translate.

**Difficulty:** Medium (4–6 hours). Django has built-in i18n tooling. Wrap all template strings with `{% trans %}`, create `.po` files for German, add a language selector in the navbar.
