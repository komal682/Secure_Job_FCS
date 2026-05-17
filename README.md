# Secure Job Search Platform

A highly secure job search and candidate management platform built with Django and PostgreSQL.

## 🚀 Key Features

* **Role-Based Access Control (RBAC)**: Distinct workflows for Candidates, Employers, and Admins.
* **Dual-Layer Authentication**: Traditional Email/Password combined with **TOTP (Google Authenticator)**.
* **Secure Resume Vault**: Resumes are encrypted at rest using `AES-256`.
* **Moderation Console**: A stealth admin portal for managing user accounts.

## 🛠️ Quick Start (Local Setup)

1. **Clone & Environment**:
   ```bash
   python -m venv venv
   # Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
   pip install -r requirements.txt
   ```

2. **Database**: 
   Create a PostgreSQL database named `job_portal` with user `postgres` and password `komal123` (or update your `settings.py` to match your local credentials).

3. **Migrate & Seed**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python seed_db.py # Generates test users & jobs
   ```

4. **Run Server**:
   ```bash
   python manage.py runserver
   ```
   The application will be running at `http://127.0.0.1:8000/`.

## 🛡️ Default Credentials (from seed_db.py)

If you ran `seed_db.py`, use these accounts to test the platform:
* **Admin**: `admin@fcs.com` / `ksvs@987`
* **Employer**: `employer@fcs.com` / `pass123`
* **Candidate**: `candidate1@fcs.com` / `pass123`

## ☁️ Deployment (Render)

This project is configured for easy deployment on [Render](https://render.com/).
1. Connect this repository to a new Render **Web Service**.
2. Connect a Render **PostgreSQL** database.
3. Set the following Environment Variables in your Web Service:
   - `DATABASE_URL` (From your Render Postgres instance)
   - `SECRET_KEY` (Generate a secure random string)
   - `DEBUG` (Set to `False`)
   - `ALLOWED_HOSTS` (Set to `*` or your Render URL)
   - `PYTHON_VERSION` (Set to `3.10.12`)
4. The `build.sh` script will automatically handle installation and migrations.
