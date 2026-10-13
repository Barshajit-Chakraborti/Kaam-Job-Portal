from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models

from .choices import EDUCATION_LEVELS, WORK_PREFERENCES


class UserManager(BaseUserManager):
    """Users log in with their email address, so there is no username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYER = "employer", "Employer"
        SEEKER = "seeker", "Job seeker"

    username = None
    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_employer(self):
        return self.role == self.Role.EMPLOYER

    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    @property
    def display_name(self):
        return self.get_full_name().strip() or self.email


def validate_resume_size(file):
    limit = settings.RESUME_MAX_MB * 1024 * 1024
    if file.size > limit:
        raise ValidationError(f"Resume must be smaller than {settings.RESUME_MAX_MB} MB.")


def resume_upload_path(instance, filename):
    return f"resumes/user_{instance.user_id}/{filename}"


class SeekerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seeker_profile")

    # Education (used by employers to filter applicants)
    education_level = models.CharField("Highest education", max_length=12, choices=EDUCATION_LEVELS, default="bachelors")
    degree = models.CharField(max_length=80, blank=True, help_text="e.g. B.Tech, MCA, Diploma")
    field_of_study = models.CharField("Branch / field of study", max_length=80, blank=True, help_text="e.g. Computer Science")
    institution = models.CharField("College / university", max_length=120, blank=True)
    graduation_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1990), MaxValueValidator(2100)]
    )
    cgpa = models.DecimalField(
        "CGPA", max_digits=4, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)], help_text="Out of 10",
    )

    # Work details
    experience_years = models.PositiveSmallIntegerField("Experience (years)", default=0, validators=[MaxValueValidator(50)])
    skills = models.CharField(max_length=255, blank=True, help_text="Comma-separated, e.g. Python, Django, SQL")
    preferred_work_mode = models.CharField("Preferred job type", max_length=6, choices=WORK_PREFERENCES, default="both")

    # Extras
    headline = models.CharField(max_length=120, blank=True, help_text="e.g. Final-year CSE student")
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=80, blank=True)
    about = models.TextField(blank=True)
    linkedin_url = models.URLField("LinkedIn URL", blank=True)
    github_url = models.URLField("GitHub URL", blank=True)
    resume = models.FileField(
        upload_to=resume_upload_path, blank=True,
        validators=[FileExtensionValidator(["pdf"]), validate_resume_size],
        help_text="PDF only",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Seeker: {self.user.display_name}"

    @property
    def education_summary(self):
        parts = [p for p in (self.degree, self.field_of_study) if p]
        return " in ".join(parts) if parts else self.get_education_level_display()


class EmployerProfile(models.Model):
    SIZES = [
        ("1-10", "1-10 employees"),
        ("11-50", "11-50 employees"),
        ("51-200", "51-200 employees"),
        ("201-1000", "201-1000 employees"),
        ("1000+", "1000+ employees"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=120)
    industry = models.CharField(max_length=80, blank=True, help_text="e.g. Software, Manufacturing")
    company_size = models.CharField(max_length=10, choices=SIZES, blank=True)
    location = models.CharField("Head office", max_length=120, blank=True)
    website = models.URLField(blank=True)
    about = models.TextField("About the company", blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True)

    def __str__(self):
        return self.company_name
