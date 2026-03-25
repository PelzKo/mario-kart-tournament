from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournament", "0003_tournament_password_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="blacklisted_cups",
            field=models.JSONField(default=list),
        ),
    ]
