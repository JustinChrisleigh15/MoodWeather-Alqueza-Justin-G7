from django.contrib import admin

from .models import MoodEntry


@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "entry_date", "mood", "stress", "energy", "sleep_quality", "weather")
    list_filter = ("weather", "entry_date")
    search_fields = ("user__username",)
