from django.db import migrations, models

from moods.classifier import classify


def fill_weather(apps, schema_editor):
    MoodEntry = apps.get_model("moods", "MoodEntry")
    for e in MoodEntry.objects.all():
        e.weather = classify(e.mood, e.stress, e.energy, e.sleep_quality)
        e.save(update_fields=["weather"])


class Migration(migrations.Migration):

    dependencies = [("moods", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="moodentry",
            name="weather",
            field=models.CharField(
                blank=True, editable=False, max_length=20,
                choices=[("sunny", "Sunny"), ("partly_cloudy", "Partly Cloudy"), ("cloudy", "Cloudy"),
                         ("rainy", "Rainy"), ("stormy", "Stormy")],
            ),
        ),
        migrations.RunPython(fill_weather, migrations.RunPython.noop),
    ]
