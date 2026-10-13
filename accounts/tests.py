from django.test import TestCase
from django.urls import reverse

from .models import EmployerProfile, SeekerProfile, User

SEEKER_FORM = {
    "first_name": "Ananya", "last_name": "Das", "email": "ananya@example.com",
    "password1": "S0me-Strong-Pass!", "password2": "S0me-Strong-Pass!",
    "education_level": "bachelors", "degree": "B.Tech", "field_of_study": "CSE",
    "institution": "NIT Manipur", "graduation_year": 2026, "cgpa": "8.50",
    "experience_years": 0, "skills": "Python, Django", "preferred_work_mode": "remote",
}
EMPLOYER_FORM = {
    "first_name": "Asha", "last_name": "Verma", "email": "hr@acme.com",
    "password1": "S0me-Strong-Pass!", "password2": "S0me-Strong-Pass!",
    "company_name": "Acme Corp", "industry": "Software", "company_size": "11-50",
    "location": "Pune", "website": "",
}


class SignupTests(TestCase):
    def test_home_page_offers_both_roles_and_login(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, reverse("accounts:signup_seeker"))
        self.assertContains(response, reverse("accounts:signup_employer"))
        self.assertContains(response, reverse("accounts:login"))

    def test_seeker_signup_creates_user_and_profile(self):
        response = self.client.post(reverse("accounts:signup_seeker"), SEEKER_FORM)
        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
        user = User.objects.get(email="ananya@example.com")
        self.assertTrue(user.is_seeker)
        self.assertEqual(user.seeker_profile.preferred_work_mode, "remote")
        self.assertEqual(user.seeker_profile.degree, "B.Tech")

    def test_employer_signup_creates_user_and_company(self):
        self.client.post(reverse("accounts:signup_employer"), EMPLOYER_FORM)
        user = User.objects.get(email="hr@acme.com")
        self.assertTrue(user.is_employer)
        self.assertEqual(user.employer_profile.company_name, "Acme Corp")

    def test_duplicate_email_rejected(self):
        self.client.post(reverse("accounts:signup_seeker"), SEEKER_FORM)
        self.client.logout()
        response = self.client.post(reverse("accounts:signup_employer"), {**EMPLOYER_FORM, "email": "ANANYA@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch_creates_nothing(self):
        response = self.client.post(reverse("accounts:signup_seeker"), {**SEEKER_FORM, "password2": "different"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertFalse(SeekerProfile.objects.exists())


class LoginAndRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seeker = User.objects.create_user("s@example.com", "pass12345!", first_name="S", last_name="K", role="seeker")
        SeekerProfile.objects.create(user=cls.seeker)
        cls.employer = User.objects.create_user("e@example.com", "pass12345!", first_name="E", last_name="M", role="employer")
        EmployerProfile.objects.create(user=cls.employer, company_name="Acme")

    def test_login_with_email_and_role_redirect(self):
        response = self.client.post(reverse("accounts:login"), {"username": "e@example.com", "password": "pass12345!"})
        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("jobs:employer_dashboard"), fetch_redirect_response=False)

    def test_seeker_cannot_open_employer_pages(self):
        self.client.force_login(self.seeker)
        self.assertEqual(self.client.get(reverse("jobs:employer_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("jobs:create")).status_code, 403)

    def test_employer_cannot_open_seeker_pages(self):
        self.client.force_login(self.employer)
        self.assertEqual(self.client.get(reverse("jobs:my_applications")).status_code, 403)

    def test_seeker_can_update_job_preference(self):
        self.client.force_login(self.seeker)
        data = {**SEEKER_FORM, "preferred_work_mode": "onsite"}
        for key in ("email", "password1", "password2"):
            data.pop(key)
        response = self.client.post(reverse("accounts:profile"), data)
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)
        self.seeker.seeker_profile.refresh_from_db()
        self.assertEqual(self.seeker.seeker_profile.preferred_work_mode, "onsite")
