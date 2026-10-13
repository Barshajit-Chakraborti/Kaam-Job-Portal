from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.choices import EDUCATION_LEVELS


class Job(models.Model):
    class WorkMode(models.TextChoices):
        REMOTE = "remote", "Remote"
        ONSITE = "onsite", "Onsite"
        HYBRID = "hybrid", "Hybrid"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=140)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True, help_text="City or region. Leave blank for fully remote roles.")
    work_mode = models.CharField(max_length=6, choices=WorkMode.choices, default=WorkMode.ONSITE)
    employment_type = models.CharField(max_length=12, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    required_skills = models.CharField(max_length=255, blank=True, help_text="Comma-separated, e.g. Python, Django, SQL")
    min_education = models.CharField("Minimum education", max_length=12, choices=EDUCATION_LEVELS, default="bachelors")
    min_experience_years = models.PositiveSmallIntegerField("Minimum experience (years)", default=0, validators=[MaxValueValidator(40)])
    min_cgpa = models.DecimalField(
        "Minimum CGPA", max_digits=4, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    salary_min = models.DecimalField("Salary from (LPA)", max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    salary_max = models.DecimalField("Salary up to (LPA)", max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    deadline = models.DateField("Apply by", null=True, blank=True)
    is_active = models.BooleanField("Accepting applications", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["work_mode"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.company_name})"

    def clean(self):
        if self.salary_min is not None and self.salary_max is not None and self.salary_max < self.salary_min:
            raise ValidationError({"salary_max": "Maximum salary can't be lower than the minimum."})

    def get_absolute_url(self):
        return reverse("jobs:detail", args=[self.pk])

    @property
    def company_name(self):
        profile = getattr(self.employer, "employer_profile", None)
        return profile.company_name if profile else self.employer.display_name

    @property
    def is_open(self):
        if not self.is_active:
            return False
        return self.deadline is None or self.deadline >= timezone.localdate()

    @property
    def salary_display(self):
        lo, hi = self.salary_min, self.salary_max
        if lo is not None and hi is not None:
            return f"{lo.normalize():f} - {hi.normalize():f} LPA"
        if lo is not None:
            return f"From {lo.normalize():f} LPA"
        if hi is not None:
            return f"Up to {hi.normalize():f} LPA"
        return ""


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="one_application_per_job"),
        ]

    def __str__(self):
        return f"{self.applicant} -> {self.job.title}"
