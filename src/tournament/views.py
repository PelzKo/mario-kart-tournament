"""Views for the Mario Kart Tournament app."""
import math
import random

from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .constants import (
    CUPS,
    GAME_STATUS_COMPLETE,
    GAME_STATUS_PENDING,
    GAME_STATUS_VOTING,
    STAGE_BRACKET,
    STAGE_GROUP,
)
from .forms import BracketResultsForm, CupVoteForm, GroupResultsForm, TournamentCreateForm
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


def create_tournament(request):
    """Landing page: create a new tournament."""
    if request.method == "POST":
        form = TournamentCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                tournament = Tournament.objects.create(
                    name=form.cleaned_data["name"],
                    switch_count=form.cleaned_data["switch_count"],
                    games_per_player=form.cleaned_data["games_per_player"],
                    stage=STAGE_GROUP,
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

    if tournament.stage == STAGE_BRACKET:
        bracket_data = _build_bracket(tournament)
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
                "bracket": bracket_data,
                "is_admin": False,
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
        },
    )


# ---------------------------------------------------------------------------
# Cup voting
# ---------------------------------------------------------------------------


def vote_cup(request, admin_token, game_id):
    """Cup voting page for a group game."""
    tournament = _get_tournament_by_admin(admin_token)
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
    """Enter results for a group stage game."""
    tournament = _get_tournament_by_admin(admin_token)
    game = get_object_or_404(GroupGame, id=game_id, tournament=tournament)

    if game.status == GAME_STATUS_COMPLETE:
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    participants = list(game.participants.select_related("player").all())

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
        form = GroupResultsForm(participants)

    return render(
        request,
        "tournament/group_results.html",
        {
            "tournament": tournament,
            "game": game,
            "participants": participants,
            "form": form,
        },
    )


# ---------------------------------------------------------------------------
# Bracket generation and views
# ---------------------------------------------------------------------------


def generate_bracket(request, admin_token):
    """Generate the bracket from group stage standings."""
    tournament = _get_tournament_by_admin(admin_token)

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
            game_data.append(
                {
                    "game": game,
                    "participants": list(game.participants.all()),
                }
            )
        rounds.append({"round_number": r, "games": game_data})
    return rounds


def bracket_view(request, admin_token):
    """Organizer bracket view."""
    tournament = _get_tournament_by_admin(admin_token)

    if tournament.stage not in (STAGE_BRACKET, "complete"):
        return redirect("tournament:admin_dashboard", admin_token=admin_token)

    bracket_data = _build_bracket(tournament)
    standings = _get_standings(tournament)

    return render(
        request,
        "tournament/bracket.html",
        {
            "tournament": tournament,
            "bracket": bracket_data,
            "standings": standings,
            "is_admin": True,
        },
    )


def bracket_results(request, admin_token, game_id):
    """Enter results for a bracket game."""
    tournament = _get_tournament_by_admin(admin_token)
    game = get_object_or_404(BracketGame, id=game_id, tournament=tournament)

    if game.status == GAME_STATUS_COMPLETE:
        return redirect("tournament:bracket_view", admin_token=admin_token)

    participants = list(game.participants.select_related("player").all())

    if request.method == "POST":
        form = BracketResultsForm(participants, request.POST)
        if form.is_valid():
            with transaction.atomic():
                for participant in participants:
                    points = form.cleaned_data[f"points_{participant.id}"]
                    participant.points_earned = points
                    participant.save()

                game.status = GAME_STATUS_COMPLETE
                game.save()

                # Advance top 2 players to next game
                sorted_participants = sorted(
                    participants,
                    key=lambda p: -(p.points_earned or 0),
                )
                advancers = sorted_participants[:2]
                for p in advancers:
                    p.advanced = True
                    p.save()

                if game.next_game:
                    # Fill TBD slots in next game with advancers
                    next_tbd = game.next_game.participants.filter(player__isnull=True)
                    for slot, adv in zip(next_tbd, advancers):
                        slot.player = adv.player
                        slot.save()

            return redirect("tournament:bracket_view", admin_token=admin_token)
    else:
        form = BracketResultsForm(participants)

    return render(
        request,
        "tournament/bracket_results.html",
        {
            "tournament": tournament,
            "game": game,
            "participants": participants,
            "form": form,
        },
    )
