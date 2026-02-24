"""Forms for the Mario Kart Tournament app."""
from django import forms
from django.core.exceptions import ValidationError

from .constants import CUPS_CHOICES, MAX_PLAYERS_PER_GAME


class TournamentCreateForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        required=False,
        label="Tournament name (optional)",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Mario Kart Night #3"}),
    )
    switch_count = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=2,
        label="Number of Nintendo Switches",
    )
    games_per_player = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=2,
        label="Group stage games per player",
    )
    player_names = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        help_text="Comma-separated player names (filled by JS)",
    )
    password = forms.CharField(
        max_length=100,
        required=True,
        label="Admin password",
        widget=forms.PasswordInput(attrs={"placeholder": "Set a password to protect the admin pages"}),
        help_text="Required to access the organizer view. The viewer link is always public.",
    )

    def clean_player_names(self):
        raw = self.cleaned_data.get("player_names", "")
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if len(names) < 2:
            raise ValidationError("Please enter at least 2 player names.")
        if len(names) > 64:
            raise ValidationError("Maximum 64 players supported.")
        # Check for duplicates
        seen = set()
        for name in names:
            lower = name.lower()
            if lower in seen:
                raise ValidationError(f"Duplicate player name: {name}")
            seen.add(lower)
        return names


class AdminLoginForm(forms.Form):
    password = forms.CharField(
        max_length=100,
        required=True,
        label="Admin password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter admin password"}),
    )


class CupVoteForm(forms.Form):
    cup_name = forms.ChoiceField(
        choices=CUPS_CHOICES,
        label="Vote for a cup",
        widget=forms.Select(attrs={"class": "cup-select"}),
    )


class GroupResultsForm(forms.Form):
    """Dynamically built form for entering points per player in a group game."""

    def __init__(self, participants, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for participant in participants:
            self.fields[f"points_{participant.id}"] = forms.IntegerField(
                min_value=0,
                max_value=999,
                label=participant.player.name,
                required=True,
            )


class BracketResultsForm(forms.Form):
    """Dynamically built form for entering points in a bracket game."""

    def __init__(self, participants, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for participant in participants:
            player_name = participant.player.name if participant.player else "TBD"
            self.fields[f"points_{participant.id}"] = forms.IntegerField(
                min_value=0,
                max_value=999,
                label=player_name,
                required=True,
            )
