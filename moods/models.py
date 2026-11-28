from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .classifier import WEATHER_CHOICES, WEATHER_ICONS, WEATHER_MESSAGES, classify, mood_score

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


def rating_field(help_text):
    return models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=help_text,
    )


class MoodEntry(models.Model):
    """One daily mood entry. Each entry belongs to the user who created it (ForeignKey)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mood_entries"
    )
    entry_date = models.DateField(default=timezone.localdate)
    mood = rating_field("1 = very low, 5 = very good")
    stress = rating_field("1 = very calm, 5 = very stressed")
    energy = rating_field("1 = exhausted, 5 = full of energy")
    sleep_quality = rating_field("1 = very poor, 5 = excellent")
    note = models.TextField(max_length=500, blank=True)
    weather = models.CharField(max_length=20, choices=WEATHER_CHOICES, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        verbose_name_plural = "mood entries"
        constraints = [
            models.UniqueConstraint(fields=["user", "entry_date"], name="one_entry_per_user_per_day")
        ]

    def save(self, *args, **kwargs):
        # The weather is always computed from the four ratings, never typed in by the user.
        self.weather = classify(self.mood, self.stress, self.energy, self.sleep_quality)
        super().save(*args, **kwargs)

    @property
    def score(self):
        return mood_score(self.mood, self.stress, self.energy, self.sleep_quality)

    @property
    def weather_icon(self):
        return WEATHER_ICONS.get(self.weather, "")

    @property
    def weather_message(self):
        return WEATHER_MESSAGES.get(self.weather, "")

    def __str__(self):
        return f"{self.user} - {self.entry_date}"
