# Secure Job Search and Professional Networking Platform

This repository contains the backend and frontend components for a highly secure job search and candidate management platform built with Django.

## 🚀 Key Features
*   **Role-Based Access Control (RBAC)**: Distinct workflows for Candidates, Employers, and Platform Admins.
*   **Dual-Layer Authentication**: Traditional Email/Password combined with integrated **Time-based One-Time Password (TOTP)** via Google Authenticator.
*   **Secure Resume Vault**: Uploaded resumes (.pdf, .docx) are encrypted at rest using military-grade `AES-256`.
*   **Moderation Console**: A stealth admin portal for managing, suspending, and deleting user accounts.

---

## 🛠️ How to Run the Project Locally

Follow these steps to set up the development environment from scratch:

### 1. Prerequisites
*   Python 3.10+
*   PostgreSQL installed and running locally.

### 2. Database Setup (PostgreSQL)
You must create a local database and a dedicated user before running the Django app. Open your `psql` terminal and execute:

```sql
CREATE DATABASE securejob_db;
CREATE USER secureuser WITH PASSWORD 'your_secure_password';
ALTER ROLE secureuser SET client_encoding TO 'utf8';
ALTER ROLE secureuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE secureuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE securejob_db TO secureuser;
```

*Note: Make sure to update your `backend/settings.py` `DATABASES` configuration with the password you chose above.*

### 3. Application Setup
Open a terminal in the root folder of this project and run the following commands:

```bash
# 1. Create a Python Virtual Environment
python -m venv venv

# 2. Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install the required Python packages
pip install -r requirements.txt

# 4. Apply Database Migrations
python manage.py makemigrations
python manage.py migrate

# 5. Start the Development Server
python manage.py runserver 8000
```
Your application will now be running at `http://localhost:8000/`.

---

## 🛡️ Admin & Superuser Credentials

The application uses a hidden, stealth gateway for administrators. This prevents automated bots from discovering the admin login page.

**Admin Login URL:** `http://localhost:8000/secure-hq/login/`

### Default Admin Credentials
If you have run the migration scripts or the setup script, the default master admin credentials are:
*   **Email:** `fcs24@gmail.com`
*   **Password:** `ksvs@987`

*(Note: Upon first login, you will be forced to scan a QR code with Google Authenticator to bind a TOTP token to this admin account).*

### Creating Additional Superusers
If you need to create another administrative account (or if the default one is deleted), run this command in your active terminal:
```bash
python manage.py createsuperuser
```
The terminal will prompt you to enter an Email and a Password. Once created, that user must log in through the `/secure-hq/login/` gateway, where they will also be assigned a mandatory TOTP QR Code on their first attempt.

---

## 📡 API / Route Endpoints Summary

Here is the directory of all web routes and API endpoints for the core features:

### General & Authentication
| Route/Endpoint | Description | Access Level |
| :--- | :--- | :--- |
| `/` | The public Landing Page. | Public |
| `/role-selection/<action>/` | The generic screen asking if you are a Candidate or Employer for Registration. | Public |
| `/register/<role>/` | Registration form for the specific role selected. | Public |
| `/login/` | The **Unified Login Gateway**. Automatically routes to the correct dashboard. | Public |
| `/totp/setup/` | Renders the TOTP QR Code for new accounts registering 2FA. | Mid-Auth Only |
| `/totp/verify/` | Prompts for the 6-digit code for existing accounts logging in. | Mid-Auth Only |
| `/logout/` | Terminates the active session. | Authenticated |

### Dashboards
| Route/Endpoint | Description | Access Level |
| :--- | :--- | :--- |
| `/dashboard/candidate/` | The main view for job seekers (View jobs, upload resume). | **Candidate** Only |
| `/dashboard/employer/` | The main view for recruiters (Post jobs, view resumes). | **Employer** Only |

### Secure Resume Vault
| Route/Endpoint | Description | Access Level |
| :--- | :--- | :--- |
| `/resume/upload/` | Submit a PDF/DOCX to be AES-256 encrypted. | **Candidate** Only |
| `/resume/success/` | Confirmation of successful encryption and DB storage. | **Candidate** Only |
| `/resume/list/` | Decrypts and lists resumes. (Candidates see their own; Employers see all). | Authenticated |

### Stealth Admin Portal
| Route/Endpoint | Description | Access Level |
| :--- | :--- | :--- |
| `/secure-hq/login/` | The isolated, high-security login portal for moderators. | Admin Credentials |
| `/secure-hq/dashboard/` | Data table listing all users and their status. | **Admin** Only |
| `/secure-hq/moderate/<user_id>/<action>/` | POST endpoint to trigger user `suspend` or `delete`. | **Admin** Only |
