from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.forms import TailwindFormMixin

from .models import EmployerProfile, SeekerProfile, User


# ---------------------------------------------------------------- auth ----
class StyledAuthenticationForm(TailwindFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update({"autocomplete": "email", "placeholder": "you@example.com"})


class StyledPasswordChangeForm(TailwindFormMixin, PasswordChangeForm):
    pass


class BaseSignupForm(TailwindFormMixin, forms.ModelForm):
    role = None  # set by subclasses

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].widget.attrs.update({"autocomplete": "email"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists. Log in instead.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords don't match.")
        elif p1:
            try:
                validate_password(p1)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmployerSignupForm(BaseSignupForm):
    role = User.Role.EMPLOYER


class SeekerSignupForm(BaseSignupForm):
    role = User.Role.SEEKER


class NameForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


# ------------------------------------------------------------ profiles ----
class EmployerSignupProfileForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ("company_name", "industry", "company_size", "location", "website")
        widgets = {"website": forms.URLInput(attrs={"placeholder": "https://"})}


class EmployerProfileForm(EmployerSignupProfileForm):
    class Meta(EmployerSignupProfileForm.Meta):
        fields = EmployerSignupProfileForm.Meta.fields + ("about", "logo")
        widgets = {
            "website": forms.URLInput(attrs={"placeholder": "https://"}),
            "about": forms.Textarea(attrs={"rows": 4}),
        }


class SeekerSignupProfileForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = SeekerProfile
        fields = (
            "education_level", "degree", "field_of_study", "institution", "graduation_year", "cgpa",
            "experience_years", "skills", "preferred_work_mode",
        )
        widgets = {
            "preferred_work_mode": forms.RadioSelect,
            "cgpa": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "10"}),
            "graduation_year": forms.NumberInput(attrs={"placeholder": "e.g. 2026"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["degree"].required = True
        self.fields["field_of_study"].required = True
        self.fields["institution"].required = True
        self.fields["graduation_year"].required = True


class SeekerProfileForm(SeekerSignupProfileForm):
    class Meta(SeekerSignupProfileForm.Meta):
        fields = SeekerSignupProfileForm.Meta.fields + (
            "headline", "phone", "city", "about", "linkedin_url", "github_url", "resume",
        )
        widgets = {
            **SeekerSignupProfileForm.Meta.widgets,
            "about": forms.Textarea(attrs={"rows": 4}),
        }
