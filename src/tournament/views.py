"""Views for the Mario Kart Tournament app."""
import math
import random

from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .constants import (
    ALL_TRACKS,
    CUPS,
    GAME_STATUS_COMPLETE,
    GAME_STATUS_PENDING,
    GAME_STATUS_VOTING,
    STAGE_BRACKET,
    STAGE_COMPLETE,
    STAGE_GROUP,
)
from django.contrib.auth.hashers import check_password, make_password

from .forms import (
    AdminLoginForm,
    BracketResultsForm,
    CupVoteForm,
    GroupResultsForm,
    TournamentCreateForm,
)
from .models import (
    BracketGame,
    BracketParticipant,
    CupVote,
    GroupGame,
    GroupGameParticipant,
    Player,
    Tournament,
)
from .scheduling import (
    assign_rounds_and_switches,
    bracket_size,
    schedule_group_stage,
    seed_bracket,
    select_cup,
)


# ---------------------------------------------------------------------------
# Tournament creation
# ---------------------------------------------------------------------------


def tournament_list(request):
    """Landing page — list all tournaments."""
    tournaments = list(
        Tournament.objects.prefetch_related("players").order_by("-created_at")[:30]
    )
    return render(request, "tournament/list.html", {"tournaments": tournaments})


def create_tournament(request):
    """Create a new tournament."""
    if request.method == "POST":
        form = TournamentCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                tournament = Tournament.objects.create(
                    name=form.cleaned_data["name"],
                    switch_count=form.cleaned_data["switch_count"],
                    games_per_player=form.cleaned_data["games_per_player"],
                    stage=STAGE_GROUP,
                    password_hash=make_password(form.cleaned_data["password"]),
                )
                player_names = form.cleaned_data["player_names"]
                players = [
                    Player(tournament=tournament, name=name) for name in player_names
                ]
                Player.objects.bulk_create(players)
                players = list(tournament.players.all())

                # Generate group stage schedule
                game_assignments = schedule_group_stage(
                    len(players),
                    tournament.games_per_player,
                    tournament.switch_count,
                )
                scheduled = assign_rounds_and_switches(
                    game_assignments, tournament.switch_count
                )

                for slot in scheduled:
                    game = GroupGame.objects.create(
                        tournament=tournament,
                        round_number=slot["round_number"],
                        switch_number=slot["switch_number"],
                    )
                    for player_idx in slot["players"]:
                        GroupGameParticipant.objects.create(
                            game=game,
                            player=players[player_idx],
                        )

            # Auto-authenticate the creator in their session
            request.session[f"admin_auth_{tournament.admin_token}"] = True
            return redirect("tournament:created", admin_token=tournament.admin_token)
    else:
        form = TournamentCreateForm()

    return render(request, "tournament/create.html", {"form": form})


def tournament_created(request, admin_token):
    """Show admin and viewer URLs after tournament creation."""
    tournament = get_object_or_404(Tournament, admin_token=admin_token)
    admin_url = request.build_absolute_uri(tournament.get_admin_url())
    viewer_url = request.build_absolute_uri(tournament.get_viewer_url())
    return render(
        request,
        "tournament/created.html",
        {
            "tournament": tournament,
            "admin_url": admin_url,
            "viewer_url": viewer_url,
        },
    )


# ---------------------------------------------------------------------------
# Admin dashboard (group stage)
# ---------------------------------------------------------------------------


def _get_tournament_by_admin(admin_token):
    return get_object_or_404(Tournament, admin_token=admin_token)


def _get_tournament_by_viewer(viewer_token):
    return get_object_or_404(Tournament, viewer_token=viewer_token)


def _is_admin_authenticated(request, admin_token):
    """Return True if the current session has authenticated for this admin token."""
    return request.session.get(f"admin_auth_{admin_token}", False)


def _require_admin_auth(request, tournament):
    """
    Check that the user is authenticated for this tournament's admin area.
    Returns None if authenticated, or a redirect response to the login page if not.
    """
    if not _is_admin_authenticated(request, tournament.admin_token):
        return redirect("tournament:admin_login", admin_token=tournament.admin_token)
    return None


# ---------------------------------------------------------------------------
# Admin login
# ---------------------------------------------------------------------------


def admin_login(request, admin_token):
    """Password gate for the admin/organizer area."""
    tournament = _get_tournament_by_admin(admin_token)

    if _is_admin_authenticated(request, admin_token):
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            if check_password(form.cleaned_data["password"], tournament.password_hash):
                request.session[f"admin_auth_{admin_token}"] = True
                # Redirect to next page if specified, otherwise dashboard
                next_url = request.GET.get("next", "")
                if next_url:
                    return redirect(next_url)
                return redirect("tournament:admin_dashboard", admin_token=admin_token)
            else:
                form.add_error("password", "Incorrect password.")
    else:
        form = AdminLoginForm()

    return render(
        request,
        "tournament/admin_login.html",
        {"tournament": tournament, "form": form},
    )


def _build_grid(tournament):
    """
    Build the group stage grid data.

    Returns:
        rounds: list of round dicts, each has:
            round_number: int
            games: list of game dicts (one per switch slot, possibly None)

    Games are indexed by switch_number so the grid is aligned.
    """
    games = list(
        tournament.group_games.prefetch_related("participants__player", "cupvote_set").all()
    )
    if not games:
        return []

    max_round = max(g.round_number for g in games)
    switch_count = tournament.switch_count

    grid = []
    for r in range(1, max_round + 1):
        row = {"round_number": r, "games": []}
        for s in range(1, switch_count + 1):
            game = next(
                (g for g in games if g.round_number == r and g.switch_number == s),
                None,
            )
            if game:
                row["games"].append(
                    {
                        "game": game,
                        "players": [p.player for p in game.participants.all()],
                        "participants": list(game.participants.all()),
                    }
                )
            else:
                row["games"].append(None)
        grid.append(row)
    return grid


def _get_standings(tournament):
    """Return players sorted by total group stage points (descending)."""
    players = list(tournament.players.all())
    for player in players:
        player.total_points = player.group_stage_points()
    players.sort(key=lambda p: -p.total_points)
    return players


def admin_dashboard(request, admin_token):
    """Organizer group stage view."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect
    grid = _build_grid(tournament)
    standings = _get_standings(tournament)
    all_complete = bool(grid) and all(
        cell["game"].status == GAME_STATUS_COMPLETE
        for row in grid
        for cell in row["games"]
        if cell is not None
    )
    return render(
        request,
        "tournament/dashboard.html",
        {
            "tournament": tournament,
            "grid": grid,
            "standings": standings,
            "switch_headers": list(range(1, tournament.switch_count + 1)),
            "is_admin": True,
            "all_group_complete": all_complete,
        },
    )


def viewer(request, viewer_token):
    """Read-only viewer mode."""
    tournament = _get_tournament_by_viewer(viewer_token)

    if tournament.stage in (STAGE_BRACKET, STAGE_COMPLETE):
        bracket_data = _build_bracket(tournament)
        standings = _get_standings(tournament)
        podium = _build_podium(tournament)
        return render(
            request,
            "tournament/bracket.html",
            {
                "tournament": tournament,
                "bracket": bracket_data,
                "standings": standings,
                "is_admin": False,
                "podium": podium,
                "auto_refresh": tournament.stage != STAGE_COMPLETE,
            },
        )

    grid = _build_grid(tournament)
    standings = _get_standings(tournament)
    return render(
        request,
        "tournament/dashboard.html",
        {
            "tournament": tournament,
            "grid": grid,
            "standings": standings,
            "switch_headers": list(range(1, tournament.switch_count + 1)),
            "is_admin": False,
            "auto_refresh": True,
        },
    )


# ---------------------------------------------------------------------------
# Cup voting
# ---------------------------------------------------------------------------


def vote_cup(request, admin_token, game_id):
    """Cup voting page for a group game."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect
    game = get_object_or_404(GroupGame, id=game_id, tournament=tournament)

    if game.status not in (GAME_STATUS_PENDING, GAME_STATUS_VOTING):
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    participants = list(game.participants.select_related("player").all())
    existing_votes = {v.player_id: v.cup_name for v in game.cupvote_set.all()}

    if request.method == "POST":
        # Expect votes: player_id -> cup_name for each player in the game
        votes_submitted = {}
        for p in participants:
            key = f"vote_{p.player_id}"
            cup_name = request.POST.get(key, "").strip()
            if cup_name in CUPS:
                votes_submitted[p.player_id] = cup_name

        with transaction.atomic():
            for player_id, cup_name in votes_submitted.items():
                CupVote.objects.update_or_create(
                    game=game,
                    player_id=player_id,
                    defaults={"cup_name": cup_name},
                )

            # Once all players have voted (or organizer explicitly submits), select cup
            vote_counts = game.get_vote_counts()
            selected = select_cup(vote_counts)
            game.cup = selected
            game.status = GAME_STATUS_VOTING  # voting done, awaiting results
            game.save()

        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    return render(
        request,
        "tournament/vote.html",
        {
            "tournament": tournament,
            "game": game,
            "participants": participants,
            "existing_votes": existing_votes,
            "cups": CUPS,
        },
    )


# ---------------------------------------------------------------------------
# Group stage results
# ---------------------------------------------------------------------------


def group_results(request, admin_token, game_id):
    """Enter (or correct) results for a group stage game."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect
    game = get_object_or_404(GroupGame, id=game_id, tournament=tournament)

    participants = list(game.participants.select_related("player").all())
    is_edit = game.status == GAME_STATUS_COMPLETE

    if request.method == "POST":
        form = GroupResultsForm(participants, request.POST)
        if form.is_valid():
            with transaction.atomic():
                for participant in participants:
                    points = form.cleaned_data[f"points_{participant.id}"]
                    participant.points_earned = points
                    participant.save()
                game.status = GAME_STATUS_COMPLETE
                game.save()
            return redirect("tournament:admin_dashboard", admin_token=admin_token)
    else:
        # Pre-populate with existing values when correcting a completed game
        initial = {
            f"points_{p.id}": p.points_earned
            for p in participants
            if p.points_earned is not None
        }
        form = GroupResultsForm(participants, initial=initial)

    return render(
        request,
        "tournament/group_results.html",
        {
            "tournament": tournament,
            "game": game,
            "participants": participants,
            "form": form,
            "is_edit": is_edit,
        },
    )


# ---------------------------------------------------------------------------
# Bracket generation and views
# ---------------------------------------------------------------------------


def generate_bracket(request, admin_token):
    """Generate the bracket from group stage standings."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect

    if tournament.stage != STAGE_GROUP:
        return redirect("tournament:bracket_view", admin_token=admin_token)

    # Check all group games complete
    incomplete = tournament.group_games.exclude(status=GAME_STATUS_COMPLETE).count()
    if incomplete > 0:
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    standings = _get_standings(tournament)
    total = len(standings)
    try:
        bsize = bracket_size(total)
    except ValueError:
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    seeded_games = seed_bracket(standings, bsize)
    num_rounds = int(math.log2(bsize // 4)) + 1 if bsize >= 4 else 1

    with transaction.atomic():
        tournament.stage = STAGE_BRACKET
        tournament.save()

        # Create bracket games for all rounds
        # Round 1 has bsize//4 games, each subsequent round halves
        # We create all games first so we can link next_game pointers

        round_games = {}
        switch_counter = 1

        for rnd in range(1, num_rounds + 1):
            games_in_round = bsize // (4 * (2 ** (rnd - 1)))
            if games_in_round == 0:
                games_in_round = 1
            round_games[rnd] = []
            for gnum in range(1, games_in_round + 1):
                bg = BracketGame.objects.create(
                    tournament=tournament,
                    round_number=rnd,
                    game_number=gnum,
                    switch_number=switch_counter,
                )
                switch_counter = switch_counter % tournament.switch_count + 1
                round_games[rnd].append(bg)

        # Link next_game pointers: game i in round r feeds into game ceil(i/2) in round r+1
        for rnd in range(1, num_rounds):
            for i, game in enumerate(round_games[rnd]):
                next_game = round_games[rnd + 1][i // 2]
                game.next_game = next_game
                game.save()

        # Seed first round with players
        for game_idx, player_list in enumerate(seeded_games):
            bg = round_games[1][game_idx]
            for player in player_list:
                BracketParticipant.objects.create(game=bg, player=player)

        # Fill later rounds with TBD slots (4 per game)
        for rnd in range(2, num_rounds + 1):
            for bg in round_games[rnd]:
                for _ in range(4):
                    BracketParticipant.objects.create(game=bg, player=None)

    return redirect("tournament:bracket_view", admin_token=admin_token)


def _build_bracket(tournament):
    """
    Build bracket display data.
    Returns list of rounds, each round is a list of game dicts.
    """
    games = list(
        tournament.bracket_games.prefetch_related("participants__player").all()
    )
    if not games:
        return []

    max_round = max(g.round_number for g in games)
    rounds = []
    for r in range(1, max_round + 1):
        round_games = [g for g in games if g.round_number == r]
        game_data = []
        for game in sorted(round_games, key=lambda g: g.game_number):
            participants = list(game.participants.all())

            # Detect if a tiebreaker was used: lowest-scoring advancer tied
            # bracket points with the highest-scoring eliminated player.
            tie_note = None
            if game.status == GAME_STATUS_COMPLETE:
                advanced = [p for p in participants if p.advanced]
                eliminated = [
                    p for p in participants if not p.advanced and p.player is not None
                ]
                if advanced and eliminated:
                    min_adv_pts = min((p.points_earned or 0) for p in advanced)
                    max_elim_pts = max((p.points_earned or 0) for p in eliminated)
                    if min_adv_pts == max_elim_pts:
                        tie_note = "Tie broken by group stage points"

            game_data.append(
                {
                    "game": game,
                    "participants": participants,
                    "tie_note": tie_note,
                }
            )
        is_tiebreaker_round = any(g["game"].is_tiebreaker for g in game_data)
        # Group games into pairs for visual bracket connectors (every 2 games share a connector)
        pairs = [game_data[i:i + 2] for i in range(0, len(game_data), 2)]
        rounds.append({
            "round_number": r,
            "games": game_data,
            "pairs": pairs,
            "is_tiebreaker_round": is_tiebreaker_round,
        })
    return rounds


def _group_participants_by_score(participants):
    """
    Group participants by score (descending). Within each score group, sort alphabetically.
    Returns a list of lists: [[tied_1st_place...], [tied_2nd_place...], ...]
    """
    if not participants:
        return []
    sorted_pts = sorted(
        participants,
        key=lambda p: (-(p.points_earned or 0), (p.player.name.lower() if p.player else "")),
    )
    groups = []
    current_score = None
    current_group = []
    for p in sorted_pts:
        score = p.points_earned or 0
        if score != current_score:
            if current_group:
                groups.append(current_group)
            current_group = [p]
            current_score = score
        else:
            current_group.append(p)
    if current_group:
        groups.append(current_group)
    return groups


def _build_podium(tournament):
    """
    Build podium data for a completed tournament.

    Returns a dict with 'first', 'second', 'third' keys.
    Each value is a list of BracketParticipants (multiple = tied, sorted alphabetically).
    Returns None if the tournament is not complete or data is unavailable.
    """
    all_bracket_games = list(tournament.bracket_games.all())
    if not all_bracket_games:
        return None
    if not all(g.status == GAME_STATUS_COMPLETE for g in all_bracket_games):
        return None

    # Check if there is a tiebreaker game
    tiebreaker_game = next(
        (g for g in all_bracket_games if g.is_tiebreaker), None
    )

    # The original final game is the non-tiebreaker game with no next_game
    final_game = next(
        (g for g in all_bracket_games if g.next_game is None and not g.is_tiebreaker),
        None,
    )
    if not final_game:
        return None

    final_participants = list(final_game.participants.select_related("player").all())
    final_participants = [p for p in final_participants if p.player is not None]

    if tiebreaker_game:
        # Tiebreaker resolves 1st place: use tiebreaker scores for those players
        tb_participants = list(
            tiebreaker_game.participants.select_related("player").all()
        )
        tb_player_ids = {p.player_id for p in tb_participants if p.player}

        # Sort tiebreaker players by their tiebreaker score (alphabetical on tie)
        tb_groups = _group_participants_by_score(tb_participants)

        # Remaining finale players (not in the tiebreaker) sorted by finale score
        other_finale = [p for p in final_participants if p.player_id not in tb_player_ids]
        other_groups = _group_participants_by_score(other_finale)

        # Merge: tiebreaker groups come first (1st/2nd from tiebreaker), then others
        all_groups = tb_groups + other_groups
    else:
        all_groups = _group_participants_by_score(final_participants)

    return {
        "first": all_groups[0] if len(all_groups) > 0 else [],
        "second": all_groups[1] if len(all_groups) > 1 else [],
        "third": all_groups[2] if len(all_groups) > 2 else [],
    }


def bracket_view(request, admin_token):
    """Organizer bracket view."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect

    if tournament.stage not in (STAGE_BRACKET, STAGE_COMPLETE):
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    bracket_data = _build_bracket(tournament)
    standings = _get_standings(tournament)
    podium = _build_podium(tournament)

    return render(
        request,
        "tournament/bracket.html",
        {
            "tournament": tournament,
            "bracket": bracket_data,
            "standings": standings,
            "is_admin": True,
            "podium": podium,
        },
    )


def bracket_results(request, admin_token, game_id):
    """Enter results for a bracket game."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect
    game = get_object_or_404(BracketGame, id=game_id, tournament=tournament)

    if game.status == GAME_STATUS_COMPLETE:
        return redirect("tournament:bracket_view", admin_token=admin_token)

    is_final = game.next_game is None and not game.is_tiebreaker
    is_tiebreaker = game.is_tiebreaker
    participants = list(game.participants.select_related("player").all())
    # Filter out TBD (null player) slots for display and scoring
    real_participants = [p for p in participants if p.player is not None]
    has_tbd = any(p.player is None for p in participants)

    if request.method == "POST":
        form = BracketResultsForm(real_participants, request.POST)
        if form.is_valid():
            with transaction.atomic():
                for participant in real_participants:
                    points = form.cleaned_data[f"points_{participant.id}"]
                    participant.points_earned = points
                    participant.save()

                game.status = GAME_STATUS_COMPLETE
                game.save()

                if is_tiebreaker:
                    # Tiebreaker finale: just mark tournament complete
                    tournament.stage = STAGE_COMPLETE
                    tournament.save()

                elif game.next_game:
                    # Non-final: advance top 2 to next game
                    sorted_participants = sorted(
                        real_participants,
                        key=lambda p: (
                            -(p.points_earned or 0),
                            -(p.player.group_stage_points() if p.player else 0),
                        ),
                    )
                    advancers = sorted_participants[:2]
                    for p in advancers:
                        p.advanced = True
                        p.save()

                    # Fill TBD slots in next game with advancers
                    next_tbd = game.next_game.participants.filter(player__isnull=True)
                    for slot, adv in zip(next_tbd, advancers):
                        slot.player = adv.player
                        slot.save()

                else:
                    # Final game (no next_game, not tiebreaker): check for tie
                    sorted_participants = sorted(
                        real_participants,
                        key=lambda p: -(p.points_earned or 0),
                    )
                    max_pts = sorted_participants[0].points_earned or 0
                    tied_top = [
                        p for p in sorted_participants
                        if (p.points_earned or 0) == max_pts
                    ]

                    if len(tied_top) > 1:
                        # Create a tiebreaker game with the tied players
                        chosen_track = random.choice(ALL_TRACKS)
                        tiebreaker_game = BracketGame.objects.create(
                            tournament=tournament,
                            round_number=game.round_number + 1,
                            game_number=1,
                            switch_number=1,
                            cup=chosen_track["cup"],
                            tiebreaker_race=chosen_track["track"],
                            is_tiebreaker=True,
                        )
                        for tied_p in tied_top:
                            BracketParticipant.objects.create(
                                game=tiebreaker_game,
                                player=tied_p.player,
                            )
                        # Tournament stays in STAGE_BRACKET until tiebreaker resolved
                    else:
                        # No tie — tournament complete
                        tournament.stage = STAGE_COMPLETE
                        tournament.save()

            return redirect("tournament:bracket_view", admin_token=admin_token)
    else:
        form = BracketResultsForm(real_participants)

    return render(
        request,
        "tournament/bracket_results.html",
        {
            "tournament": tournament,
            "game": game,
            "participants": real_participants,
            "form": form,
            "is_final": is_final,
            "is_tiebreaker": is_tiebreaker,
            "has_tbd": has_tbd,
        },
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def _build_stats(tournament):
    """
    Compute tournament statistics for a completed tournament.
    Returns a dict with cup usage, player pairings, and score highlights.
    """
    from collections import Counter, defaultdict

    # Cup frequency — all completed games (group + bracket)
    cup_counts = Counter()
    for game in tournament.group_games.filter(status=GAME_STATUS_COMPLETE):
        if game.cup:
            cup_counts[game.cup] += 1
    for game in tournament.bracket_games.filter(status=GAME_STATUS_COMPLETE):
        if game.cup:
            cup_counts[game.cup] += 1
    cup_ranking = cup_counts.most_common()

    # Player pairing frequency — which players raced together most
    pair_counts = Counter()
    for game in tournament.group_games.filter(status=GAME_STATUS_COMPLETE):
        players_in_game = [
            p.player for p in game.participants.select_related("player").all()
            if p.player
        ]
        for i in range(len(players_in_game)):
            for j in range(i + 1, len(players_in_game)):
                pair = tuple(sorted([players_in_game[i].name, players_in_game[j].name]))
                pair_counts[pair] += 1
    for game in tournament.bracket_games.filter(status=GAME_STATUS_COMPLETE):
        players_in_game = [
            p.player for p in game.participants.select_related("player").all()
            if p.player
        ]
        for i in range(len(players_in_game)):
            for j in range(i + 1, len(players_in_game)):
                pair = tuple(sorted([players_in_game[i].name, players_in_game[j].name]))
                pair_counts[pair] += 1
    pair_ranking = [
        {"players": list(pair), "count": count}
        for pair, count in pair_counts.most_common(10)
    ]

    # Highest single-game score
    best_score = None
    for p in GroupGameParticipant.objects.filter(
        game__tournament=tournament, points_earned__isnull=False
    ).select_related("player", "game").order_by("-points_earned")[:1]:
        best_score = {
            "player": p.player.name,
            "points": p.points_earned,
            "game": f"Group R{p.game.round_number}/S{p.game.switch_number}",
        }

    # Total races played per player
    races_per_player = []
    for player in tournament.players.all():
        group_games = player.groupgameparticipant_set.filter(
            game__tournament=tournament, points_earned__isnull=False
        ).count()
        bracket_games = player.bracket_participations.filter(
            game__tournament=tournament, points_earned__isnull=False
        ).count()
        total = group_games + bracket_games
        avg = (
            player.group_stage_points() / group_games if group_games else 0
        )
        races_per_player.append({
            "name": player.name,
            "races": total,
            "avg_pts": round(avg, 1),
        })
    races_per_player.sort(key=lambda x: -x["avg_pts"])

    return {
        "cup_ranking": cup_ranking,
        "pair_ranking": pair_ranking,
        "best_score": best_score,
        "races_per_player": races_per_player,
        "total_games": len(cup_counts),
    }


def tournament_stats(request, admin_token):
    """Statistics tab — accessible via admin token."""
    tournament = _get_tournament_by_admin(admin_token)
    if auth_redirect := _require_admin_auth(request, tournament):
        return auth_redirect
    if tournament.stage != STAGE_COMPLETE:
        return redirect("tournament:admin_dashboard", admin_token=admin_token)
    stats = _build_stats(tournament)
    standings = _get_standings(tournament)
    return render(
        request,
        "tournament/stats.html",
        {
            "tournament": tournament,
            "stats": stats,
            "standings": standings,
            "is_admin": True,
            "admin_token": admin_token,
        },
    )


def tournament_stats_viewer(request, viewer_token):
    """Statistics tab — accessible via viewer token."""
    tournament = _get_tournament_by_viewer(viewer_token)
    if tournament.stage != STAGE_COMPLETE:
        return redirect("tournament:viewer", viewer_token=viewer_token)
    stats = _build_stats(tournament)
    standings = _get_standings(tournament)
    return render(
        request,
        "tournament/stats.html",
        {
            "tournament": tournament,
            "stats": stats,
            "standings": standings,
            "is_admin": False,
        },
    )
