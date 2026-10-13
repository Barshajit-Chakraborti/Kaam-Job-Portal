"""Fill the database with realistic demo data:  python manage.py seed_demo"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import EmployerProfile, SeekerProfile, User
from jobs.models import Application, Job

PASSWORD = "demo12345"

EMPLOYERS = [
    ("hr@northwind.example", "Asha", "Verma", "Northwind Software", "Software", "51-200", "Bengaluru"),
    ("talent@brightmill.example", "Rahul", "Nair", "BrightMill Analytics", "Data & AI", "11-50", "Hyderabad"),
    ("jobs@shillong-tech.example", "Lalit", "Singh", "Shillong Tech Labs", "Software", "11-50", "Shillong"),
]

JOBS = [
    ("Junior Django Developer", "full_time", "onsite", "Bengaluru", "bachelors", 0, "7.00", "Python, Django, SQL", 4, 6),
    ("Python Backend Intern", "internship", "remote", "", "bachelors", 0, "6.50", "Python, REST, Git", 1, 2),
    ("Data Analyst", "full_time", "hybrid", "Hyderabad", "bachelors", 1, "7.50", "SQL, Excel, Power BI", 5, 8),
    ("Machine Learning Engineer", "full_time", "remote", "", "masters", 2, "8.00", "Python, PyTorch, MLOps", 12, 20),
    ("Frontend Developer (Tailwind)", "full_time", "remote", "", "bachelors", 1, "7.00", "HTML, Tailwind, JavaScript", 5, 9),
    ("QA Automation Engineer", "full_time", "onsite", "Shillong", "diploma", 1, "", "Selenium, Python, Testing", 3, 5),
    ("DevOps Trainee", "internship", "onsite", "Bengaluru", "bachelors", 0, "6.00", "Linux, Docker, Git", 2, 3),
    ("Full Stack Developer", "full_time", "hybrid", "Bengaluru", "bachelors", 2, "7.00", "Django, React, PostgreSQL", 8, 14),
    ("Technical Content Writer", "part_time", "remote", "", "12th", 0, "", "Writing, Research", 1, 2),
    ("Cloud Engineer", "full_time", "onsite", "Hyderabad", "bachelors", 3, "7.50", "AWS, Terraform, Linux", 10, 18),
    ("Research Associate (NLP)", "contract", "remote", "", "phd", 0, "", "NLP, Python, Research", 15, 25),
    ("Support Engineer", "full_time", "onsite", "Shillong", "diploma", 0, "", "Linux, Networking, Communication", 2, 4),
]

SEEKERS = [
    ("Ananya", "Das", "bachelors", "B.Tech", "Computer Science", "NIT Manipur", 2026, "8.6", 0, "Python, Django, SQL, Git", "remote"),
    ("Rohan", "Sharma", "bachelors", "B.Tech", "Information Technology", "NIT Silchar", 2025, "7.4", 1, "Java, Spring, SQL", "onsite"),
    ("Meera", "Iyer", "masters", "M.Tech", "Data Science", "IIT Guwahati", 2025, "9.1", 2, "Python, PyTorch, MLOps, SQL", "remote"),
    ("Kabir", "Khan", "bachelors", "BCA", "Computer Applications", "Manipur University", 2024, "7.9", 2, "HTML, Tailwind, JavaScript, React", "both"),
    ("Priya", "Singh", "diploma", "Diploma", "Electronics", "Govt Polytechnic Imphal", 2024, "8.0", 1, "Linux, Networking, Testing", "onsite"),
    ("Arjun", "Reddy", "bachelors", "B.E.", "Computer Science", "BMS College", 2023, "7.1", 3, "AWS, Terraform, Linux, Docker", "both"),
    ("Neha", "Gupta", "bachelors", "B.Sc", "Statistics", "Delhi University", 2025, "8.2", 1, "SQL, Excel, Power BI, Python", "remote"),
    ("Imran", "Ali", "masters", "MCA", "Computer Applications", "Jadavpur University", 2024, "8.4", 2, "Django, React, PostgreSQL", "both"),
    ("Sneha", "Pillai", "bachelors", "B.Tech", "Electronics", "NIT Calicut", 2026, "6.8", 0, "Python, Selenium, Testing", "onsite"),
    ("Dev", "Malhotra", "phd", "PhD", "Computational Linguistics", "IISc Bangalore", 2023, "9.3", 0, "NLP, Python, Research", "remote"),
    ("Tashi", "Wangchuk", "12th", "", "Science", "St. Joseph's School", 2025, None, 0, "Writing, Research", "remote"),
    ("Lakshmi", "Rao", "bachelors", "B.Tech", "Computer Science", "NIT Manipur", 2026, "9.0", 0, "Python, Django, Docker, Git", "both"),
]


class Command(BaseCommand):
    help = "Create demo employers, job seekers, jobs and applications."

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)
        today = timezone.localdate()

        employers = []
        for email, first, last, company, industry, size, city in EMPLOYERS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"first_name": first, "last_name": last, "role": User.Role.EMPLOYER}
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            EmployerProfile.objects.get_or_create(
                user=user,
                defaults={"company_name": company, "industry": industry, "company_size": size, "location": city},
            )
            employers.append(user)

        seekers = []
        for first, last, level, degree, field, college, year, cgpa, exp, skills, pref in SEEKERS:
            email = f"{first.lower()}.{last.lower()}@student.example"
            user, created = User.objects.get_or_create(
                email=email, defaults={"first_name": first, "last_name": last, "role": User.Role.SEEKER}
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            SeekerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "education_level": level, "degree": degree, "field_of_study": field, "institution": college,
                    "graduation_year": year, "cgpa": cgpa, "experience_years": exp, "skills": skills,
                    "preferred_work_mode": pref, "city": "Imphal" if "Manipur" in college else "",
                },
            )
            seekers.append(user)

        jobs = []
        for i, (title, etype, mode, loc, edu, exp, cgpa, skills, lo, hi) in enumerate(JOBS):
            job, _ = Job.objects.get_or_create(
                employer=employers[i % len(employers)],
                title=title,
                defaults={
                    "description": (
                        f"We're hiring a {title} to join our team.\n\n"
                        "You will ship features end to end, review code with teammates and learn from "
                        "experienced engineers. We value curiosity and clear communication."
                    ),
                    "requirements": "Strong fundamentals in your area.\nGood communication skills.\nProjects or internships are a plus.",
                    "employment_type": etype, "work_mode": mode, "location": loc,
                    "min_education": edu, "min_experience_years": exp,
                    "min_cgpa": cgpa or None, "required_skills": skills,
                    "salary_min": lo, "salary_max": hi,
                    "deadline": today + timedelta(days=rng.randint(10, 45)),
                },
            )
            jobs.append(job)

        statuses = [s for s, _ in Application.Status.choices]
        created_apps = 0
        for seeker in seekers:
            for job in rng.sample(jobs, k=rng.randint(2, 5)):
                _, created = Application.objects.get_or_create(
                    job=job, applicant=seeker,
                    defaults={
                        "status": rng.choices(statuses, weights=[6, 2, 2, 1])[0],
                        "cover_letter": "I'm excited about this role and would love to contribute.",
                    },
                )
                created_apps += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(employers)} employers, {len(seekers)} job seekers, {len(jobs)} jobs, {created_apps} new applications."
        ))
        self.stdout.write(f"Employer login:   {EMPLOYERS[0][0]} / {PASSWORD}")
        self.stdout.write(f"Job seeker login: ananya.das@student.example / {PASSWORD}")
