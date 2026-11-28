from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import MoodEntryForm
from .classifier import WEATHER_CHOICES
from .models import MoodEntry

MEMBER = User.Role.MEMBER


@role_required(MEMBER)
def entry_list(request):
    """Read: a member sees only their own entries."""
    entries = MoodEntry.objects.filter(user=request.user)
    page = Paginator(entries, 10).get_page(request.GET.get("page"))
    return render(request, "moods/entry_list.html", {"page": page})


@role_required(MEMBER)
def entry_create(request):
    """Create: the entry is always linked to the logged-in user."""
    if request.method == "POST":
        form = MoodEntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, "Your mood entry was saved.")
            return redirect("moods:entry_detail", pk=entry.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = MoodEntryForm(user=request.user)
    return render(request, "moods/entry_form.html", {"form": form, "mode": "new"})


@login_required
def entry_detail(request, pk):
    """Read one entry. Members: own entries only. Admins: any entry, read-only."""
    if request.user.role == User.Role.ADMIN:
        entry = get_object_or_404(MoodEntry.objects.select_related("user"), pk=pk)
    else:
        entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    return render(request, "moods/entry_detail.html", {"entry": entry})


@role_required(MEMBER)
def entry_update(request, pk):
    entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    if request.method == "POST":
        form = MoodEntryForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your mood entry was updated.")
            return redirect("moods:entry_detail", pk=entry.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = MoodEntryForm(instance=entry, user=request.user)
    return render(request, "moods/entry_form.html", {"form": form, "mode": "edit", "entry": entry})


@role_required(MEMBER)
def entry_delete(request, pk):
    entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Your mood entry was deleted.")
        return redirect("moods:entry_list")
    return render(request, "moods/entry_confirm_delete.html", {"entry": entry})


@role_required(User.Role.ADMIN)
def admin_entries(request):
    """Admin: read-only overview of every member's entries, with search and weather filter."""
    entries = MoodEntry.objects.select_related("user")
    q = request.GET.get("q", "").strip()
    weather = request.GET.get("weather", "")
    if q:
        entries = entries.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))
    if weather in dict(WEATHER_CHOICES):
        entries = entries.filter(weather=weather)
    page = Paginator(entries, 15).get_page(request.GET.get("page"))
    context = {"page": page, "q": q, "weather": weather, "weather_choices": WEATHER_CHOICES}
    return render(request, "moods/admin_entries.html", context)
