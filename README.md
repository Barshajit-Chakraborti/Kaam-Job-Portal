# Kaam - Job Portal

A full-stack job portal built with **Django** and **Tailwind CSS**. Employers post openings and review applicants; job seekers search, filter and apply. Both sides have role-based accounts and powerful filtering.

> Rename the product by changing `SITE_NAME` in `config/settings.py`.

## Features

**Home page**
- Landing screen where the visitor chooses **Employer** or **Job seeker**, which continues into the matching signup flow
- **Log in** button for existing users (navbar and home page)

**Job seekers**
- Signup collects education (level, degree, branch, college, graduation year, CGPA), experience, skills and **preferred job type (Remote / Onsite / Open to both)**; all editable later from the profile page
- Job filtering: keyword (title, skill, company), location, work mode, job type, education level, experience, minimum salary, "match my work preference", sorting
- One-click apply with an optional note, application tracker with status, withdraw before review
- PDF resume upload (type and size validated); only the owner and employers they applied to can open it
- Email notification when an employer changes an application status

**Employers**
- Company profile at signup, dashboard with stats (open jobs, applicants, new this week, shortlisted)
- Create, edit, close/reopen and delete jobs (education, experience, CGPA, salary range, deadline)
- **Applicant filtering** by highest education, degree / branch, graduation-year range, minimum CGPA, minimum experience, preferred job type, skills (all must match), status, and sorting by CGPA, experience or graduation year
- Per-job applicant list and an all-jobs list, candidate detail page, status updates (applied / shortlisted / hired / rejected)

**Engineering**
- Custom user model that logs in with **email** (no username), role-based access decorators (`employer_required`, `seeker_required`)
- Object-level permissions (an employer can only touch their own jobs and applicants)
- Query logic isolated in `jobs/filters.py`, with `select_related` to avoid N+1 queries
- Database constraint: one application per seeker per job
- 30+ automated tests, a seed command for demo data, WhiteNoise + Gunicorn config for deployment, secrets via environment variables

## Tech stack

| Layer | Tools |
|-------|-------|
| Backend | Python 3.10+, Django 5.2 |
| Database | SQLite (dev), swappable for PostgreSQL |
| Frontend | Django templates, Tailwind CSS 3, a little vanilla JS |
| Files | Pillow (company logos), protected resume downloads |

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Create the database tables
python manage.py makemigrations accounts jobs
python manage.py migrate

# 3. Run
python manage.py runserver
```

| Role | Email |
|------|-------|
| Employer | `hr@northwind.example` |
| Job seeker | `ananya.das@student.example` |

Create an admin with `python manage.py createsuperuser` and visit `/admin/`.

Run the tests: `python manage.py test`

## Tailwind

Out of the box the templates load Tailwind from its CDN, so no Node.js is needed to run the project.
For production, compile a minified stylesheet. The templates switch to it automatically when `static/css/tailwind.css` exists:

```bash
npm install
npm run build:css      # one-off build
npm run watch:css      # rebuild while developing
```

If you change colours or fonts, update both `tailwind.config.js` and the inline config in `templates/base.html`.

## Project structure

```
config/        settings, root urls, wsgi/asgi
core/          home page, shared Tailwind form mixin, template tags
accounts/      custom User, SeekerProfile, EmployerProfile, signup/login/profile
jobs/          Job, Application, filters.py, employer + seeker views, seed_demo command
templates/     base layout, partials, page templates
static/        app.css, app.js, Tailwind source
```

## Resume bullets (edit to match what you did)

- Built a two-role job portal (employers and job seekers) with Django 5 and Tailwind CSS, featuring a custom email-based user model and role-based access control.
- Implemented multi-criteria filtering: seekers filter jobs by work mode, education and salary; employers filter applicants by education, branch, graduation year, CGPA, skills and preferred job type.
- Designed relational schema with database constraints, object-level permissions and protected file downloads; wrote 30+ unit and integration tests.
- Added deployment configuration (Gunicorn, WhiteNoise, environment-based settings) and a data-seeding command for demos.
