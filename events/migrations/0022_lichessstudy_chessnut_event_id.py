from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0021_alter_event_chessnut_handler"),
    ]

    operations = [
        migrations.AddField(
            model_name="lichessstudy",
            name="chessnut_event_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
