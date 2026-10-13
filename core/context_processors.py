from django.conf import settings


def site(request):
    return {"SITE_NAME": settings.SITE_NAME, "TAILWIND_BUILT": settings.TAILWIND_BUILT}
