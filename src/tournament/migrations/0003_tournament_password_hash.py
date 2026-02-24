from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournament", "0002_bracketgame_is_tiebreaker"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="password_hash",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
