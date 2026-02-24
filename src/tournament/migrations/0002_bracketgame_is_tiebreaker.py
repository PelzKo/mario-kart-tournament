from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournament", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bracketgame",
            name="is_tiebreaker",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="bracketgame",
            name="tiebreaker_race",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
