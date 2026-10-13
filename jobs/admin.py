from django.contrib import admin

from .models import Application, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "work_mode", "employment_type", "is_active", "deadline", "created_at")
    list_filter = ("work_mode", "employment_type", "is_active", "min_education")
    search_fields = ("title", "employer__email", "employer__employer_profile__company_name")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "job", "status", "applied_at")
    list_filter = ("status",)
    search_fields = ("applicant__email", "job__title")
