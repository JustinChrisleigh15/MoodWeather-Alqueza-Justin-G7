# Mood Weather

IT317 – G7 | Justin Chrisleigh M. Alqueza

A personal mood-tracking app that shows your day as weather. Built with Django (templates) and PostgreSQL / Supabase.

## Standard features (Project Development 1)
Registration, login/logout, role-based dashboards (Member, Admin) and user profile.

## Core feature (Project Development 2): Daily Mood Entry and Mood Weather Card
Members record one entry per day with four ratings (1–5): **mood, stress, energy, sleep quality**, plus an optional note. The system converts the ratings into a weather category and shows it as a **Mood Weather Card**.

| Operation | Page | Who |
|---|---|---|
| Create | `/moods/new/` | Member |
| Read (list) | `/moods/` | Member (own entries only) |
| Read (card) | `/moods/<id>/` | Member (own), Admin (any, read-only) |
| Update | `/moods/<id>/edit/` | Member (own entries only) |
| Delete | `/moods/<id>/delete/` | Member (own entries only) |
| Overview | `/moods/all/` | Admin (read-only, search and weather filter) |

### Classification rule
```
score = 2*mood + energy + sleep_quality + (6 - stress)     # 5 to 25
>= 21 Sunny | 17-20 Partly Cloudy | 13-16 Cloudy | 9-12 Rainy | <= 8 Stormy
```
The weather is computed on the server every time an entry is saved. Users cannot set it directly.

### Business rules and validation
- Ratings must be whole numbers from 1 to 5; all four ratings and the date are required.
- One entry per user per day (database unique constraint plus form check).
- No entries for future dates.
- Every entry has a ForeignKey to its owner. Members can only see and change their own entries; other members' entries return 404.
- Admins can view every entry but cannot create, edit or delete them.
- Success and error messages are shown for every action.

### Data model
`User (1) ── (many) MoodEntry`: `user`, `entry_date`, `mood`, `stress`, `energy`, `sleep_quality`, `note`, `weather`, `created_at`, `updated_at`.

## Setup
```bash
git clone <repo-url>
cd MoodWeather-Alqueza-Justin-G7
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # then fill in your PostgreSQL / Supabase credentials
python manage.py migrate
python manage.py createadminuser admin admin@example.com "YourPassword123!"
python manage.py runserver
```
Open http://127.0.0.1:8000/. Register to create a Member; the command above creates an Admin.
For Supabase use the Session pooler host and `DB_SSLMODE=require` in `.env`.

## Tests
```bash
python manage.py test
```
44 tests cover registration, login, role access, profile, mood-entry CRUD, validation, ownership, classification and the admin overview.

## Branching
`main` (stable) ← `develop` (integration) ← `feature/mood-entry`, `feature/mood-weather-card`. See `docs/` for the PD2 report.

## Not yet built (later sprints)
Mood history and statistics, monthly pattern analysis, forecast, daily reminders.
