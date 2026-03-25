"""
Data models for the Mario Kart Tournament app.
"""
import secrets
import uuid

from django.db import models

from .constants import (
    BRACKET_GAME_STATUS_CHOICES,
    CUPS_CHOICES,
    GAME_STATUS_CHOICES,
    GAME_STATUS_PENDING,
    STAGE_CHOICES,
    STAGE_SETUP,
)


def generate_token():
    return secrets.token_urlsafe(24)


class Tournament(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True)
    admin_token = models.CharField(max_length=40, unique=True, default=generate_token)
    viewer_token = models.CharField(max_length=40, unique=True, default=generate_token)
    switch_count = models.PositiveIntegerField(default=2)
    games_per_player = models.PositiveIntegerField(default=2)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_SETUP)
    created_at = models.DateTimeField(auto_now_add=True)
    # Hashed password for protecting admin pages (blank = no password set)
    password_hash = models.CharField(max_length=128, blank=True)
    # List of cup names excluded from cup voting/selection for this tournament
    blacklisted_cups = models.JSONField(default=list)

    def __str__(self):
        return self.name or f"Tournament {self.id}"

    def get_admin_url(self):
        from django.urls import reverse
        return reverse("tournament:admin_dashboard", args=[self.admin_token])

    def get_viewer_url(self):
        from django.urls import reverse
        return reverse("tournament:viewer", args=[self.viewer_token])


class Player(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="players"
    )
    name = models.CharField(max_length=100)
    seed = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.tournament})"

    def group_stage_points(self):
        """Total points earned across all group stage games."""
        return (
            self.groupgameparticipant_set.filter(points_earned__isnull=False)
            .aggregate(total=models.Sum("points_earned"))["total"]
            or 0
        )


class GroupGame(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="group_games"
    )
    round_number = models.PositiveIntegerField()
    switch_number = models.PositiveIntegerField()
    cup = models.CharField(max_length=50, choices=CUPS_CHOICES, blank=True)
    status = models.CharField(
        max_length=20, choices=GAME_STATUS_CHOICES, default=GAME_STATUS_PENDING
    )

    class Meta:
        ordering = ["round_number", "switch_number"]

    def __str__(self):
        return (
            f"Round {self.round_number} / Switch {self.switch_number} "
            f"({self.tournament})"
        )

    def is_complete(self):
        return self.status == "complete"

    def get_vote_counts(self):
        """Return {cup_name: vote_count} for this game."""
        votes = {}
        for vote in self.cupvote_set.all():
            votes[vote.cup_name] = votes.get(vote.cup_name, 0) + 1
        return votes


class GroupGameParticipant(models.Model):
    game = models.ForeignKey(
        GroupGame, on_delete=models.CASCADE, related_name="participants"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="groupgameparticipant_set"
    )
    points_earned = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-points_earned"]
        unique_together = [("game", "player")]

    def __str__(self):
        return f"{self.player.name} in {self.game}"


class CupVote(models.Model):
    game = models.ForeignKey(
        GroupGame, on_delete=models.CASCADE, related_name="cupvote_set"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="cup_votes"
    )
    cup_name = models.CharField(max_length=50)

    class Meta:
        unique_together = [("game", "player")]

    def __str__(self):
        return f"{self.player.name} voted {self.cup_name} in {self.game}"


class BracketGame(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="bracket_games"
    )
    round_number = models.PositiveIntegerField()
    game_number = models.PositiveIntegerField()
    switch_number = models.PositiveIntegerField()
    cup = models.CharField(max_length=50, choices=CUPS_CHOICES, blank=True)
    status = models.CharField(
        max_length=20,
        choices=BRACKET_GAME_STATUS_CHOICES,
        default=GAME_STATUS_PENDING,
    )
    next_game = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_games",
    )
    is_tiebreaker = models.BooleanField(default=False)
    tiebreaker_race = models.CharField(max_length=100, blank=True)  # specific track for tiebreaker

    class Meta:
        ordering = ["round_number", "game_number"]

    def __str__(self):
        return (
            f"Bracket R{self.round_number}G{self.game_number} ({self.tournament})"
        )


class BracketParticipant(models.Model):
    game = models.ForeignKey(
        BracketGame, on_delete=models.CASCADE, related_name="participants"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="bracket_participations"
    )
    points_earned = models.PositiveIntegerField(null=True, blank=True)
    advanced = models.BooleanField(default=False)

    class Meta:
        ordering = ["-points_earned"]

    def __str__(self):
        name = self.player.name if self.player else "TBD"
        return f"{name} in {self.game}"
