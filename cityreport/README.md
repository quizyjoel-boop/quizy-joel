# CityReport — Douala

A citizen platform to report potholes, broken streetlights and uncollected
waste, then track each issue through to resolution. Built with Flask,
SQLite (zero setup), vanilla JavaScript + Leaflet.js, and a Mistral AI agent
that classifies each report, drafts a clean description, and scores its
hazard level.

## Technology constraint

This project is intentionally implemented with Python, Flask, Mistral AI,
HTML/Jinja templates, CSS, and vanilla JavaScript. SQLite is the default
local database, with optional XAMPP MySQL support.

No React, Vue, Angular, Node.js frontend, or frontend component framework is
used. The packages listed in `requirements.txt` are lightweight Python runtime
dependencies for Flask database access, password hashing, environment
configuration, HTTP requests, and optional MySQL connectivity.

## Features

- **Report on a map** — citizens drop a pin, add a description and optional
  photo. No account needed.
- **AI triage agent (Mistral)** — classifies the category, drafts a clean
  description for city staff, and scores a hazard level (low/medium/high),
  live in the report form.
- **Department routing** — each category auto-routes to the right city
  department (Roads, Public Lighting, Sanitation, etc).
- **Status tracking** — citizens get a reference code (`CR-XXXXXXX`) and can
  track received → in progress → resolved on a public page.
- **Staff dashboard** — KPIs, filterable report table, inline status updates.

## 1. Requirements

- Python 3.10+
- A Mistral AI API key (optional — the app runs a keyword-based fallback
  classifier if `MISTRAL_API_KEY` is left blank, so it's fully demoable
  without one)

No database server to install — SQLite is used by default and just creates
a `cityreport.db` file next to `app.py`.

## 2. Install and configure

```bash
cd cityreport
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your MISTRAL_API_KEY if you have one
```

## 3. Initialize the database and create your staff login

```bash
flask init-db          # creates all tables in cityreport.db
flask create-admin      # creates the first staff login from ADMIN_EMAIL / ADMIN_PASSWORD in .env
```

## 4. Run it

```bash
python app.py
```

Visit `http://localhost:5000` for the citizen map, and
`http://localhost:5000/staff/login` for the staff dashboard.

## Project structure

```
cityreport/
├── app.py                # routes, Flask app factory, CLI commands
├── config.py              # env-driven config (database, Mistral, map defaults)
├── models.py               # Report / StatusEvent / StaffUser (SQLAlchemy)
├── mistral_service.py       # Mistral AI classification agent + fallback
├── templates/
│   ├── base.html, index.html, track.html, login.html, dashboard.html, 404.html
├── static/
│   ├── css/style.css
│   ├── js/map.js           # citizen map, report modal, live AI preview
│   └── js/dashboard.js     # staff status updates
└── requirements.txt
```

## Notes on the Mistral AI agent

`mistral_service.classify_report()` sends the citizen's description (and, if
attached, the photo via a vision model like `pixtral-12b-2409`) to Mistral's
chat completions API with a strict JSON response format, asking it to return
a category, a cleaned-up summary, and a hazard level. If no API key is set,
or the request fails for any reason, it falls back to a local keyword
classifier so a citizen's report is never blocked by an AI/network issue.

## Switching to MySQL later

If you ever want MySQL (e.g. via XAMPP) instead of SQLite, create the
database (`CREATE DATABASE cityreport;` in phpMyAdmin or the MySQL CLI),
`pip install pymysql cryptography`, and set in `.env`:

```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/cityreport
```
