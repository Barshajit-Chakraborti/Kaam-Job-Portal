from django import forms

from accounts.choices import EDUCATION_LEVELS
from core.forms import TailwindFormMixin

from .models import Application, Job

ANY = [("", "Any")]


class JobForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Job
        fields = (
            "title", "employment_type", "work_mode", "location", "min_education",
            "min_experience_years", "min_cgpa", "required_skills", "salary_min", "salary_max",
            "deadline", "description", "requirements", "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "requirements": forms.Textarea(attrs={"rows": 5}),
            "deadline": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "min_cgpa": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "10"}),
            "salary_min": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "salary_max": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
        }


class ApplicationForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ("cover_letter",)
        labels = {"cover_letter": "Note to the employer"}
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Why are you a good fit? (optional)"}
            )
        }


class StatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("status",)


class JobFilterForm(TailwindFormMixin, forms.Form):
    """Filters shown to job seekers on the job list."""

    SORT = [("newest", "Newest first"), ("salary", "Highest salary"), ("deadline", "Closing soon")]

    q = forms.CharField(label="Keyword", required=False, widget=forms.TextInput(attrs={"placeholder": "Title, skill or company"}))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "City or region"}))
    work_mode = forms.ChoiceField(label="Work mode", required=False, choices=ANY + list(Job.WorkMode.choices))
    employment_type = forms.ChoiceField(label="Job type", required=False, choices=ANY + list(Job.EmploymentType.choices))
    education = forms.ChoiceField(label="My education level", required=False, choices=ANY + EDUCATION_LEVELS,
                                  help_text="Hide jobs that ask for more than this.")
    experience = forms.IntegerField(label="My experience (years)", required=False, min_value=0, max_value=40,
                                    help_text="Hide jobs that ask for more than this.")
    min_salary = forms.DecimalField(label="Minimum salary (LPA)", required=False, min_value=0, decimal_places=2, max_digits=6)
    match_profile = forms.BooleanField(label="Match my work preference", required=False)
    sort = forms.ChoiceField(required=False, choices=SORT)


class ApplicantFilterForm(TailwindFormMixin, forms.Form):
    """Filters shown to employers on the applicant list."""

    SORT = [
        ("newest", "Newest applications"),
        ("cgpa", "Highest CGPA"),
        ("experience", "Most experience"),
        ("grad_year", "Latest graduation year"),
    ]

    q = forms.CharField(label="Search", required=False, widget=forms.TextInput(attrs={"placeholder": "Name, email, college"}))
    job = forms.ModelChoiceField(label="Job", required=False, queryset=Job.objects.none(), empty_label="All jobs")
    education_level = forms.ChoiceField(label="Highest education", required=False, choices=ANY + EDUCATION_LEVELS)
    degree = forms.CharField(label="Degree / branch", required=False, widget=forms.TextInput(attrs={"placeholder": "e.g. B.Tech, Computer Science"}))
    grad_year_from = forms.IntegerField(label="Graduated from", required=False, min_value=1990, max_value=2100)
    grad_year_to = forms.IntegerField(label="Graduated until", required=False, min_value=1990, max_value=2100)
    min_cgpa = forms.DecimalField(label="Minimum CGPA", required=False, min_value=0, max_value=10, decimal_places=2, max_digits=4)
    min_experience = forms.IntegerField(label="Minimum experience (years)", required=False, min_value=0, max_value=50)
    work_mode = forms.ChoiceField(
        label="Preferred job type", required=False,
        choices=ANY + [("remote", "Remote"), ("onsite", "Onsite")],
        help_text="Includes people who are open to both.",
    )
    skills = forms.CharField(label="Skills", required=False, widget=forms.TextInput(attrs={"placeholder": "Python, SQL"}),
                             help_text="Comma-separated. Candidates need all of them.")
    status = forms.ChoiceField(required=False, choices=ANY + list(Application.Status.choices))
    sort = forms.ChoiceField(required=False, choices=SORT)

    def __init__(self, *args, employer=None, show_job=True, **kwargs):
        super().__init__(*args, **kwargs)
        if employer is not None:
            self.fields["job"].queryset = Job.objects.filter(employer=employer).order_by("title")
        if not show_job:
            del self.fields["job"]
