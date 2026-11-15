from django.db import migrations, models


def default_chessnut_events():
    return {"events": []}


def normalize_chessnut_events(apps, schema_editor):
    Event = apps.get_model("events", "Event")

    for event in Event.objects.all().iterator():
        chessnut_events = event.chessnut_events

        if chessnut_events is None:
            normalized = {"events": []}
        elif isinstance(chessnut_events, list):
            normalized = {"events": chessnut_events}
        elif isinstance(chessnut_events, dict):
            normalized = chessnut_events.copy()
            if not isinstance(normalized.get("events"), list):
                normalized["events"] = []
        else:
            normalized = {"events": []}

        if normalized != chessnut_events:
            Event.objects.filter(pk=event.pk).update(chessnut_events=normalized)


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0022_lichessstudy_chessnut_event_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="chessnut_events",
            field=models.JSONField(
                blank=True,
                default=default_chessnut_events,
                null=True,
            ),
        ),
        migrations.RunPython(
            normalize_chessnut_events,
            migrations.RunPython.noop,
        ),
    ]
