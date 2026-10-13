"""Query-building helpers. Kept out of the views so they are easy to unit test."""
from django.db.models import F, Q

from accounts.choices import EDUCATION_RANK


def filter_jobs(queryset, data, user=None):
    """Apply cleaned JobFilterForm data to a Job queryset."""
    for term in (data.get("q") or "").split():
        queryset = queryset.filter(
            Q(title__icontains=term)
            | Q(description__icontains=term)
            | Q(required_skills__icontains=term)
            | Q(employer__employer_profile__company_name__icontains=term)
        )

    if data.get("location"):
        queryset = queryset.filter(location__icontains=data["location"])
    if data.get("work_mode"):
        queryset = queryset.filter(work_mode=data["work_mode"])
    if data.get("employment_type"):
        queryset = queryset.filter(employment_type=data["employment_type"])

    education = data.get("education")
    if education:
        allowed = [level for level, rank in EDUCATION_RANK.items() if rank <= EDUCATION_RANK[education]]
        queryset = queryset.filter(min_education__in=allowed)

    if data.get("experience") is not None:
        queryset = queryset.filter(min_experience_years__lte=data["experience"])

    if data.get("min_salary") is not None:
        queryset = queryset.filter(salary_max__gte=data["min_salary"])

    if data.get("match_profile") and user is not None and user.is_authenticated and user.is_seeker:
        profile = getattr(user, "seeker_profile", None)
        if profile and profile.preferred_work_mode in ("remote", "onsite"):
            queryset = queryset.filter(work_mode=profile.preferred_work_mode)

    sort = data.get("sort") or "newest"
    if sort == "salary":
        return queryset.order_by(F("salary_max").desc(nulls_last=True), "-created_at")
    if sort == "deadline":
        return queryset.order_by(F("deadline").asc(nulls_last=True), "-created_at")
    return queryset.order_by("-created_at")


def filter_applications(queryset, data):
    """Apply cleaned ApplicantFilterForm data to an Application queryset."""
    prefix = "applicant__seeker_profile__"

    if data.get("job"):
        queryset = queryset.filter(job=data["job"])

    for term in (data.get("q") or "").split():
        queryset = queryset.filter(
            Q(applicant__first_name__icontains=term)
            | Q(applicant__last_name__icontains=term)
            | Q(applicant__email__icontains=term)
            | Q(**{f"{prefix}institution__icontains": term})
        )

    if data.get("education_level"):
        queryset = queryset.filter(**{f"{prefix}education_level": data["education_level"]})

    for term in (data.get("degree") or "").replace(",", " ").split():
        queryset = queryset.filter(
            Q(**{f"{prefix}degree__icontains": term}) | Q(**{f"{prefix}field_of_study__icontains": term})
        )

    if data.get("grad_year_from"):
        queryset = queryset.filter(**{f"{prefix}graduation_year__gte": data["grad_year_from"]})
    if data.get("grad_year_to"):
        queryset = queryset.filter(**{f"{prefix}graduation_year__lte": data["grad_year_to"]})
    if data.get("min_cgpa") is not None:
        queryset = queryset.filter(**{f"{prefix}cgpa__gte": data["min_cgpa"]})
    if data.get("min_experience") is not None:
        queryset = queryset.filter(**{f"{prefix}experience_years__gte": data["min_experience"]})

    mode = data.get("work_mode")
    if mode in ("remote", "onsite"):
        queryset = queryset.filter(**{f"{prefix}preferred_work_mode__in": [mode, "both"]})

    for skill in (s.strip() for s in (data.get("skills") or "").split(",")):
        if skill:
            queryset = queryset.filter(**{f"{prefix}skills__icontains": skill})

    if data.get("status"):
        queryset = queryset.filter(status=data["status"])

    sort = data.get("sort") or "newest"
    if sort == "cgpa":
        return queryset.order_by(F(f"{prefix}cgpa").desc(nulls_last=True), "-applied_at")
    if sort == "experience":
        return queryset.order_by(F(f"{prefix}experience_years").desc(nulls_last=True), "-applied_at")
    if sort == "grad_year":
        return queryset.order_by(F(f"{prefix}graduation_year").desc(nulls_last=True), "-applied_at")
    return queryset.order_by("-applied_at")
