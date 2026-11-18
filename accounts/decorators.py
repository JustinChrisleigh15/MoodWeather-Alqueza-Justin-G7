from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    """Require login AND a specific role. Wrong role -> redirected to own dashboard."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, "You do not have permission to open that page.")
                return redirect("accounts:dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
