from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmployerProfile, SeekerProfile, User

from .models import Application, Job


def make_seeker(email, **profile):
    user = User.objects.create_user(email, "pass12345!", first_name=email.split("@")[0].title(), last_name="Test", role="seeker")
    defaults = dict(education_level="bachelors", degree="B.Tech", field_of_study="Computer Science",
                    institution="NIT", graduation_year=2025, cgpa="8.00", experience_years=0,
                    skills="Python", preferred_work_mode="both")
    defaults.update(profile)
    SeekerProfile.objects.create(user=user, **defaults)
    return user


class JobFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employer = User.objects.create_user("e@example.com", "pass12345!", first_name="E", last_name="M", role="employer")
        EmployerProfile.objects.create(user=cls.employer, company_name="Acme")
        mk = lambda **kw: Job.objects.create(employer=cls.employer, description="desc", **kw)
        cls.remote_job = mk(title="Remote Python Dev", work_mode="remote", required_skills="Python", min_education="bachelors")
        cls.onsite_job = mk(title="Onsite Tester", work_mode="onsite", location="Pune", min_education="diploma", employment_type="internship")
        cls.phd_job = mk(title="Research Scientist", work_mode="remote", min_education="phd", min_experience_years=3, salary_max="25")
        cls.closed_job = mk(title="Closed Role", is_active=False)
        cls.expired_job = mk(title="Expired Role", deadline=timezone.localdate() - timedelta(days=1))

    def titles(self, **params):
        response = self.client.get(reverse("jobs:list"), params)
        self.assertEqual(response.status_code, 200)
        return {job.title for job in response.context["page_obj"]}

    def test_closed_and_expired_jobs_hidden(self):
        titles = self.titles()
        self.assertNotIn("Closed Role", titles)
        self.assertNotIn("Expired Role", titles)
        self.assertEqual(len(titles), 3)

    def test_filter_by_work_mode(self):
        self.assertEqual(self.titles(work_mode="onsite"), {"Onsite Tester"})

    def test_filter_by_job_type_and_location(self):
        self.assertEqual(self.titles(employment_type="internship"), {"Onsite Tester"})
        self.assertEqual(self.titles(location="pun"), {"Onsite Tester"})

    def test_education_filter_hides_jobs_needing_more(self):
        self.assertEqual(self.titles(education="bachelors"), {"Remote Python Dev", "Onsite Tester"})

    def test_experience_filter(self):
        self.assertNotIn("Research Scientist", self.titles(experience="1"))

    def test_keyword_matches_company_and_skills(self):
        self.assertIn("Remote Python Dev", self.titles(q="acme python"))

    def test_min_salary(self):
        self.assertEqual(self.titles(min_salary="20"), {"Research Scientist"})

    def test_match_my_preference(self):
        seeker = make_seeker("remote@example.com", preferred_work_mode="remote")
        self.client.force_login(seeker)
        self.assertEqual(self.titles(match_profile="on"), {"Remote Python Dev", "Research Scientist"})


class ApplicationFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employer = User.objects.create_user("e@example.com", "pass12345!", first_name="E", last_name="M", role="employer")
        EmployerProfile.objects.create(user=cls.employer, company_name="Acme")
        cls.other_employer = User.objects.create_user("o@example.com", "pass12345!", first_name="O", last_name="M", role="employer")
        EmployerProfile.objects.create(user=cls.other_employer, company_name="Other")
        cls.job = Job.objects.create(employer=cls.employer, title="Dev", description="d")

    def test_seeker_applies_once(self):
        seeker = make_seeker("a@example.com")
        self.client.force_login(seeker)
        url = reverse("jobs:apply", args=[self.job.pk])
        self.client.post(url, {"cover_letter": "hi"})
        self.client.post(url, {"cover_letter": "again"})
        self.assertEqual(Application.objects.filter(applicant=seeker).count(), 1)

    def test_employer_cannot_apply(self):
        self.client.force_login(self.employer)
        self.assertEqual(self.client.post(reverse("jobs:apply", args=[self.job.pk])).status_code, 403)

    def test_anonymous_apply_redirects_to_login(self):
        response = self.client.post(reverse("jobs:apply", args=[self.job.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_employer_post_job(self):
        self.client.force_login(self.employer)
        response = self.client.post(reverse("jobs:create"), {
            "title": "New role", "employment_type": "full_time", "work_mode": "remote",
            "min_education": "bachelors", "min_experience_years": 0, "description": "Do things",
            "is_active": "on",
        })
        self.assertRedirects(response, reverse("jobs:employer_dashboard"), fetch_redirect_response=False)
        self.assertTrue(Job.objects.filter(title="New role", employer=self.employer).exists())

    def test_employer_cannot_edit_someone_elses_job(self):
        self.client.force_login(self.other_employer)
        self.assertEqual(self.client.get(reverse("jobs:update", args=[self.job.pk])).status_code, 404)

    def test_status_update(self):
        seeker = make_seeker("a@example.com")
        application = Application.objects.create(job=self.job, applicant=seeker)
        self.client.force_login(self.employer)
        self.client.post(reverse("jobs:application_status", args=[application.pk]), {"status": "shortlisted"})
        application.refresh_from_db()
        self.assertEqual(application.status, "shortlisted")


class ApplicantFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employer = User.objects.create_user("e@example.com", "pass12345!", first_name="E", last_name="M", role="employer")
        EmployerProfile.objects.create(user=cls.employer, company_name="Acme")
        cls.job = Job.objects.create(employer=cls.employer, title="Dev", description="d")
        profiles = {
            "ananya": dict(education_level="bachelors", field_of_study="Computer Science", graduation_year=2026, cgpa="8.60", preferred_work_mode="remote", skills="Python, Django"),
            "rohan": dict(education_level="bachelors", degree="B.E.", field_of_study="Mechanical", graduation_year=2022, cgpa="6.90", preferred_work_mode="onsite", skills="CAD"),
            "meera": dict(education_level="masters", degree="M.Tech", field_of_study="Data Science", graduation_year=2025, cgpa="9.10", experience_years=2, preferred_work_mode="both", skills="Python, SQL"),
        }
        for name, extra in profiles.items():
            user = make_seeker(f"{name}@example.com", **extra)
            Application.objects.create(job=cls.job, applicant=user)

    def names(self, **params):
        self.client.force_login(self.employer)
        response = self.client.get(reverse("jobs:job_applicants", args=[self.job.pk]), params)
        self.assertEqual(response.status_code, 200)
        return {a.applicant.first_name.lower() for a in response.context["page_obj"]}

    def test_no_filters_returns_everyone(self):
        self.assertEqual(self.names(), {"ananya", "rohan", "meera"})

    def test_filter_by_education_level(self):
        self.assertEqual(self.names(education_level="masters"), {"meera"})

    def test_filter_by_branch_text(self):
        self.assertEqual(self.names(degree="computer science"), {"ananya"})

    def test_filter_by_graduation_year_range(self):
        self.assertEqual(self.names(grad_year_from="2025"), {"ananya", "meera"})
        self.assertEqual(self.names(grad_year_to="2022"), {"rohan"})

    def test_filter_by_min_cgpa(self):
        self.assertEqual(self.names(min_cgpa="8.5"), {"ananya", "meera"})

    def test_preferred_job_type_includes_open_to_both(self):
        self.assertEqual(self.names(work_mode="remote"), {"ananya", "meera"})
        self.assertEqual(self.names(work_mode="onsite"), {"rohan", "meera"})

    def test_skills_must_all_match(self):
        self.assertEqual(self.names(skills="python, sql"), {"meera"})

    def test_combined_filters(self):
        self.assertEqual(self.names(work_mode="remote", min_cgpa="9", education_level="masters"), {"meera"})

    def test_other_employers_cannot_see_resume_or_applicants(self):
        other = User.objects.create_user("x@example.com", "pass12345!", first_name="X", last_name="Y", role="employer")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("jobs:job_applicants", args=[self.job.pk])).status_code, 404)
        profile = SeekerProfile.objects.first()
        self.assertEqual(self.client.get(reverse("jobs:resume", args=[profile.pk])).status_code, 403)
