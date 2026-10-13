from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from accounts.models import EmployerProfile
from jobs.models import Job


def home(request):
    today = timezone.localdate()
    open_jobs = Job.objects.filter(is_active=True).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).count()
    return render(
        request,
        "core/home.html",
        {"open_jobs": open_jobs, "company_count": EmployerProfile.objects.count()},
    )
