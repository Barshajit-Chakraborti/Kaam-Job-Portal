from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    EmployerProfileForm, EmployerSignupForm, EmployerSignupProfileForm, NameForm,
    SeekerProfileForm, SeekerSignupForm, SeekerSignupProfileForm,
    StyledAuthenticationForm, StyledPasswordChangeForm,
)
from .models import EmployerProfile, SeekerProfile


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password was updated."


def _signup(request, *, user_form_class, profile_form_class, template, welcome):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    user_form = user_form_class(request.POST or None)
    profile_form = profile_form_class(request.POST or None)

    if request.method == "POST":
        # Evaluate both so every error is shown at once.
        valid = [user_form.is_valid(), profile_form.is_valid()]
        if all(valid):
            with transaction.atomic():
                user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, welcome)
            return redirect("accounts:dashboard")

    return render(request, template, {"user_form": user_form, "profile_form": profile_form})


def signup_employer(request):
    return _signup(
        request,
        user_form_class=EmployerSignupForm,
        profile_form_class=EmployerSignupProfileForm,
        template="accounts/signup_employer.html",
        welcome="Your employer account is ready. Post your first job to start receiving applications.",
    )


def signup_seeker(request):
    return _signup(
        request,
        user_form_class=SeekerSignupForm,
        profile_form_class=SeekerSignupProfileForm,
        template="accounts/signup_seeker.html",
        welcome="Your account is ready. Browse openings and apply in one click.",
    )


@login_required
def dashboard(request):
    """Send each user to the right home screen for their role."""
    user = request.user
    if user.is_employer:
        return redirect("jobs:employer_dashboard")
    if user.is_seeker:
        return redirect("jobs:list")
    return redirect("admin:index")


@login_required
def profile_edit(request):
    user = request.user
    if user.is_seeker:
        profile, _ = SeekerProfile.objects.get_or_create(user=user)
        profile_form_class = SeekerProfileForm
    elif user.is_employer:
        profile, _ = EmployerProfile.objects.get_or_create(user=user, defaults={"company_name": user.display_name})
        profile_form_class = EmployerProfileForm
    else:
        return redirect("admin:index")

    name_form = NameForm(request.POST or None, instance=user)
    profile_form = profile_form_class(request.POST or None, request.FILES or None, instance=profile)

    if request.method == "POST":
        valid = [name_form.is_valid(), profile_form.is_valid()]
        if all(valid):
            name_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile_edit.html",
        {"name_form": name_form, "profile_form": profile_form, "profile": profile},
    )
