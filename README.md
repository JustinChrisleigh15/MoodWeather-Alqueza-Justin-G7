# Mood Weather — Account Feature (Project Development 1)

IT317 – G5 | Justin Chrisleigh M. Alqueza

A personal mood-tracking app that shows your day as weather. This phase delivers the **Account Feature** that the later modules (daily entry, classification, history, forecast) will depend on.

**Stack:** Django (templates for frontend) + PostgreSQL / Supabase (no SQLite).

## Features
- **Registration** – required fields, valid email, unique username and email, password confirmation, Django password validators, hashed passwords (PBKDF2), success/error messages.
- **Login / Logout** – invalid-credential error message; logout (POST) ends the session; `@login_required` protection redirects logged-out users to the login page.
- **Role-based dashboards** – two roles: **Admin** and **Member**. Each user lands on their own dashboard after login; opening the other role's URL redirects back with an error message.
- **Profile** – view and edit own name, email, contact number, profile photo. No user id in the URL, so users can only access their own profile. Role cannot be changed from the profile or registration forms.

## Setup
```bash
git clone <your-repo-url>
cd MoodWeather-Alqueza-Justin-G5
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env           # then fill in your DB credentials
python manage.py migrate
python manage.py createadminuser admin admin@example.com "StrongPass!234"
python manage.py runserver
```
Open http://127.0.0.1:8000/. Register to create a Member; use the command above to create an Admin.

### Database (PostgreSQL or Supabase)
Put credentials in `.env` (never committed). For Supabase, copy the host/user/password/port from **Project Settings → Database** and set `DB_SSLMODE=require`.

## Tests
```bash
python manage.py test accounts
```
19 tests cover registration validation, hashing, login errors, logout, route protection, role isolation and profile access.

## Project structure
```
moodweather/   project settings and root URLs
accounts/      custom User model (role), forms, views, role decorator, tests
templates/     base layout + accounts pages
static/css/    styles
```
