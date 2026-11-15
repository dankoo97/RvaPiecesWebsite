from django.db import migrations, models


def default_chessnut_handler():
    return {
        "enabled": False,
        "title_regex": "",
        "days_before_start": 0,
        "days_after_end": 0,
        "ignored_event_ids": [],
    }


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0019_alter_event_chessnut_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="chessnut_handler",
            field=models.JSONField(
                blank=True,
                default=default_chessnut_handler,
            ),
        ),
    ]
