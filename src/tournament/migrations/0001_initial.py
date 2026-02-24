"""Initial migration for the tournament app."""
import tournament.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tournament",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=200)),
                ("admin_token", models.CharField(default=tournament.models.generate_token, max_length=40, unique=True)),
                ("viewer_token", models.CharField(default=tournament.models.generate_token, max_length=40, unique=True)),
                ("switch_count", models.PositiveIntegerField(default=2)),
                ("games_per_player", models.PositiveIntegerField(default=2)),
                ("stage", models.CharField(
                    choices=[("setup", "Setup"), ("group", "Group Stage"), ("bracket", "Bracket"), ("complete", "Complete")],
                    default="setup",
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Player",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("seed", models.PositiveIntegerField(blank=True, null=True)),
                ("tournament", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="players", to="tournament.tournament")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="GroupGame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("round_number", models.PositiveIntegerField()),
                ("switch_number", models.PositiveIntegerField()),
                ("cup", models.CharField(
                    blank=True,
                    choices=[
                        ("Mushroom", "Mushroom"), ("Flower", "Flower"), ("Star", "Star"), ("Special", "Special"),
                        ("Shell", "Shell"), ("Banana", "Banana"), ("Leaf", "Leaf"), ("Lightning", "Lightning"),
                        ("Golden Dash", "Golden Dash"), ("Lucky Cat", "Lucky Cat"), ("Turnip", "Turnip"),
                        ("Propeller", "Propeller"), ("Rock", "Rock"), ("Moon", "Moon"), ("Fruit", "Fruit"),
                        ("Boomerang", "Boomerang"), ("Feather", "Feather"), ("Cherry", "Cherry"),
                        ("Acorn", "Acorn"), ("Spiny", "Spiny"), ("Egg", "Egg"), ("Triforce", "Triforce"),
                        ("Crossing", "Crossing"), ("Bell", "Bell"),
                    ],
                    max_length=50,
                )),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("voting", "Voting"), ("in_progress", "In Progress"), ("complete", "Complete")],
                    default="pending",
                    max_length=20,
                )),
                ("tournament", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="group_games", to="tournament.tournament")),
            ],
            options={"ordering": ["round_number", "switch_number"]},
        ),
        migrations.CreateModel(
            name="GroupGameParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("points_earned", models.PositiveIntegerField(blank=True, null=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="tournament.groupgame")),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="groupgameparticipant_set", to="tournament.player")),
            ],
            options={"ordering": ["-points_earned"], "unique_together": {("game", "player")}},
        ),
        migrations.CreateModel(
            name="CupVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cup_name", models.CharField(max_length=50)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cupvote_set", to="tournament.groupgame")),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cup_votes", to="tournament.player")),
            ],
            options={"unique_together": {("game", "player")}},
        ),
        migrations.CreateModel(
            name="BracketGame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("round_number", models.PositiveIntegerField()),
                ("game_number", models.PositiveIntegerField()),
                ("switch_number", models.PositiveIntegerField()),
                ("cup", models.CharField(
                    blank=True,
                    choices=[
                        ("Mushroom", "Mushroom"), ("Flower", "Flower"), ("Star", "Star"), ("Special", "Special"),
                        ("Shell", "Shell"), ("Banana", "Banana"), ("Leaf", "Leaf"), ("Lightning", "Lightning"),
                        ("Golden Dash", "Golden Dash"), ("Lucky Cat", "Lucky Cat"), ("Turnip", "Turnip"),
                        ("Propeller", "Propeller"), ("Rock", "Rock"), ("Moon", "Moon"), ("Fruit", "Fruit"),
                        ("Boomerang", "Boomerang"), ("Feather", "Feather"), ("Cherry", "Cherry"),
                        ("Acorn", "Acorn"), ("Spiny", "Spiny"), ("Egg", "Egg"), ("Triforce", "Triforce"),
                        ("Crossing", "Crossing"), ("Bell", "Bell"),
                    ],
                    max_length=50,
                )),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("complete", "Complete")],
                    default="pending",
                    max_length=20,
                )),
                ("tournament", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bracket_games", to="tournament.tournament")),
                ("next_game", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="previous_games",
                    to="tournament.bracketgame",
                )),
            ],
            options={"ordering": ["round_number", "game_number"]},
        ),
        migrations.CreateModel(
            name="BracketParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("points_earned", models.PositiveIntegerField(blank=True, null=True)),
                ("advanced", models.BooleanField(default=False)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="tournament.bracketgame")),
                ("player", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="bracket_participations", to="tournament.player")),
            ],
            options={"ordering": ["-points_earned"]},
        ),
    ]
