from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import employer_required, seeker_required
from accounts.models import SeekerProfile

from .filters import filter_applications, filter_jobs
from .forms import ApplicantFilterForm, ApplicationForm, JobFilterForm, JobForm, StatusForm
from .models import Application, Job


def _paginate(request, queryset, per_page):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _open_jobs():
    today = timezone.localdate()
    return (
        Job.objects.filter(is_active=True)
        .filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
        .select_related("employer__employer_profile")
    )


# ------------------------------------------------------------ public/seeker --
def job_list(request):
    form = JobFilterForm(request.GET)
    jobs = _open_jobs()
    if form.is_valid():
        jobs = filter_jobs(jobs, form.cleaned_data, request.user)
    else:
        jobs = jobs.order_by("-created_at")

    applied_ids = set()
    if request.user.is_authenticated and request.user.is_seeker:
        applied_ids = set(request.user.applications.values_list("job_id", flat=True))

    page_obj = _paginate(request, jobs, 8)
    return render(request, "jobs/job_list.html", {"form": form, "page_obj": page_obj, "applied_ids": applied_ids})


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related("employer__employer_profile"), pk=pk)
    is_owner = request.user.is_authenticated and job.employer_id == request.user.id
    if not job.is_open and not is_owner:
        raise Http404("This job is no longer accepting applications.")

    application = None
    if request.user.is_authenticated and request.user.is_seeker:
        application = Application.objects.filter(job=job, applicant=request.user).first()

    return render(
        request,
        "jobs/job_detail.html",
        {"job": job, "is_owner": is_owner, "application": application, "form": ApplicationForm()},
    )


@seeker_required
@require_POST
def apply(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if not job.is_open:
        messages.error(request, "This job is no longer accepting applications.")
        return redirect("jobs:list")

    form = ApplicationForm(request.POST)
    if form.is_valid():
        application, created = Application.objects.get_or_create(
            job=job, applicant=request.user, defaults={"cover_letter": form.cleaned_data["cover_letter"]}
        )
        if created:
            messages.success(request, f"Application sent to {job.company_name}.")
        else:
            messages.info(request, "You've already applied to this job.")
    return redirect("jobs:detail", pk=job.pk)


@seeker_required
def my_applications(request):
    applications = request.user.applications.select_related("job__employer__employer_profile")
    status = request.GET.get("status")
    if status in Application.Status.values:
        applications = applications.filter(status=status)
    return render(
        request,
        "jobs/my_applications.html",
        {
            "page_obj": _paginate(request, applications, 10),
            "statuses": Application.Status.choices,
            "current_status": status,
        },
    )


@seeker_required
@require_POST
def withdraw(request, pk):
    application = get_object_or_404(Application, pk=pk, applicant=request.user)
    if application.status == Application.Status.APPLIED:
        application.delete()
        messages.success(request, "Application withdrawn.")
    else:
        messages.error(request, "Only applications that haven't been reviewed can be withdrawn.")
    return redirect("jobs:my_applications")


# ----------------------------------------------------------------- employer --
@employer_required
def employer_dashboard(request):
    jobs = Job.objects.filter(employer=request.user).annotate(applicant_count=Count("applications"))
    applications = Application.objects.filter(job__employer=request.user)
    week_ago = timezone.now() - timedelta(days=7)
    stats = {
        "active_jobs": jobs.filter(is_active=True).count(),
        "total_applicants": applications.count(),
        "new_applicants": applications.filter(applied_at__gte=week_ago).count(),
        "shortlisted": applications.filter(status=Application.Status.SHORTLISTED).count(),
    }
    return render(request, "jobs/employer_dashboard.html", {"jobs": jobs, "stats": stats})


@employer_required
def job_create(request):
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user
        job.save()
        messages.success(request, "Job posted.")
        return redirect("jobs:employer_dashboard")
    return render(request, "jobs/job_form.html", {"form": form, "job": None})


@employer_required
def job_update(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Job updated.")
        return redirect("jobs:employer_dashboard")
    return render(request, "jobs/job_form.html", {"form": form, "job": job})


@employer_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("jobs:employer_dashboard")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


@employer_required
@require_POST
def job_toggle(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    job.is_active = not job.is_active
    job.save(update_fields=["is_active", "updated_at"])
    messages.success(request, "Job is now accepting applications." if job.is_active else "Job closed to new applications.")
    return redirect("jobs:employer_dashboard")


@employer_required
def applicants(request, job_id=None):
    job = None
    base = Application.objects.filter(job__employer=request.user).select_related(
        "job", "applicant", "applicant__seeker_profile"
    )
    if job_id is not None:
        job = get_object_or_404(Job, pk=job_id, employer=request.user)
        base = base.filter(job=job)

    form = ApplicantFilterForm(request.GET, employer=request.user, show_job=job is None)
    if form.is_valid():
        results = filter_applications(base, form.cleaned_data)
    else:
        results = base.order_by("-applied_at")

    return render(
        request,
        "jobs/applicants.html",
        {
            "form": form,
            "job": job,
            "page_obj": _paginate(request, results, 10),
            "total_for_scope": base.count(),
            "statuses": Application.Status.choices,
        },
    )


@employer_required
def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant", "applicant__seeker_profile"),
        pk=pk, job__employer=request.user,
    )
    profile = getattr(application.applicant, "seeker_profile", None)
    return render(
        request,
        "jobs/application_detail.html",
        {"application": application, "profile": profile, "statuses": Application.Status.choices},
    )


def _notify_status_change(application):
    send_mail(
        subject=f"Update on your application for {application.job.title}",
        message=(
            f"Hi {application.applicant.first_name or 'there'},\n\n"
            f"{application.job.company_name} updated your application for \"{application.job.title}\".\n"
            f"New status: {application.get_status_display()}.\n\n"
            "Log in to Kaam to see all your applications."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[application.applicant.email],
        fail_silently=True,
    )


@employer_required
@require_POST
def application_status(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"), pk=pk, job__employer=request.user
    )
    old_status = application.status
    form = StatusForm(request.POST, instance=application)
    if form.is_valid():
        form.save()
        if application.status != old_status:
            _notify_status_change(application)
            messages.success(
                request,
                f"{application.applicant.display_name} marked as {application.get_status_display().lower()}.",
            )
    else:
        messages.error(request, "Choose a valid status.")

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("jobs:applicants")


# ------------------------------------------------------------------ resumes --
@login_required
def resume_download(request, profile_id):
    """Serve a resume only to its owner, to employers they applied to, or to staff."""
    profile = get_object_or_404(SeekerProfile, pk=profile_id)
    user = request.user
    allowed = (
        user.is_staff
        or profile.user_id == user.id
        or (
            user.is_employer
            and Application.objects.filter(applicant_id=profile.user_id, job__employer=user).exists()
        )
    )
    if not allowed:
        raise PermissionDenied
    if not profile.resume:
        raise Http404("No resume uploaded.")
    return FileResponse(profile.resume.open("rb"), content_type="application/pdf")
