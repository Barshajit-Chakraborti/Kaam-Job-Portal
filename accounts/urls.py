from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/employer/", views.signup_employer, name="signup_employer"),
    path("signup/seeker/", views.signup_seeker, name="signup_seeker"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile_edit, name="profile"),
    path("password/", views.PasswordChangeView.as_view(), name="password_change"),
]
