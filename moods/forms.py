from django import forms
from django.utils import timezone

from .models import MoodEntry


class MoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ("entry_date", "mood", "stress", "energy", "sleep_quality", "note")
        widgets = {
            "entry_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }
        labels = {"sleep_quality": "Sleep quality", "entry_date": "Date"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["entry_date"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_entry_date(self):
        entry_date = self.cleaned_data["entry_date"]
        if entry_date > timezone.localdate():
            raise forms.ValidationError("You cannot record an entry for a future date.")
        return entry_date

    def clean(self):
        cleaned = super().clean()
        entry_date = cleaned.get("entry_date")
        if self.user and entry_date:
            duplicate = MoodEntry.objects.filter(user=self.user, entry_date=entry_date)
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error("entry_date", "You already have an entry for this date. Edit it instead.")
        return cleaned
