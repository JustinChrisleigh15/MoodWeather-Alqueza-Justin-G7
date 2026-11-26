from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return redirect("accounts:login")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class MoodLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().first_name or form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

    def get_success_url(self):
        # Honour ?next= only if present; otherwise send each role to its own dashboard.
        return self.get_redirect_url() or redirect_url_for(self.request.user)


def redirect_url_for(user):
    from django.urls import reverse

    return reverse("accounts:admin_dashboard" if user.role == User.Role.ADMIN else "accounts:member_dashboard")


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def dashboard(request):
    """Role router: sends each user to the dashboard for their role."""
    return redirect(redirect_url_for(request.user))


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        "total_members": User.objects.filter(role=User.Role.MEMBER).count(),
        "total_admins": User.objects.filter(role=User.Role.ADMIN).count(),
        "recent_users": User.objects.order_by("-date_joined")[:10],
    }
    return render(request, "accounts/admin_dashboard.html", context)


@role_required(User.Role.MEMBER)
def member_dashboard(request):
    from moods.models import MoodEntry

    entries = MoodEntry.objects.filter(user=request.user)
    context = {
        "today_entry": entries.filter(entry_date=timezone.localdate()).first(),
        "recent_entries": entries[:5],
        "entry_count": entries.count(),
    }
    return render(request, "accounts/member_dashboard.html", context)


@login_required
def profile(request):
    # Always the logged-in user's own record: no user id in the URL.
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})
