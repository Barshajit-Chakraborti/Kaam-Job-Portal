from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    # Seekers / public
    path("", views.job_list, name="list"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/apply/", views.apply, name="apply"),
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:pk>/withdraw/", views.withdraw, name="withdraw"),
    # Employers
    path("manage/", views.employer_dashboard, name="employer_dashboard"),
    path("manage/new/", views.job_create, name="create"),
    path("manage/<int:pk>/edit/", views.job_update, name="update"),
    path("manage/<int:pk>/delete/", views.job_delete, name="delete"),
    path("manage/<int:pk>/toggle/", views.job_toggle, name="toggle"),
    path("manage/applicants/", views.applicants, name="applicants"),
    path("manage/<int:job_id>/applicants/", views.applicants, name="job_applicants"),
    path("manage/applicant/<int:pk>/", views.application_detail, name="application_detail"),
    path("manage/applicant/<int:pk>/status/", views.application_status, name="application_status"),
    # Files
    path("resume/<int:profile_id>/", views.resume_download, name="resume"),
]
