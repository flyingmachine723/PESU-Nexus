# PESU Nexus

> A student-built academic companion for PES University — mock tests, performance analytics, and study materials, all in one place.

![Django](https://img.shields.io/badge/Django-6.1-092E20?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## 📖 Overview

**PESU Nexus** is a Django web application designed by students, for students at PES University. It centralizes the academic tools that are usually scattered across WhatsApp groups, Google Drive folders, and photocopied notes.

Students can take timed mock tests, review detailed performance analytics, and browse semester-wise study materials — all through a clean, dark-themed interface built for focus.

The project was built from scratch as a learning exercise in full-stack Django development, with production-grade practices like environment-based configuration, cloud-hosted PostgreSQL, and static file optimization.

---

## ✨ Features

### 🧪 Mock Tests
- Browse tests by **semester** and **course**
- Take **timed, server-enforced** tests — attempts are recorded even if you navigate away
- Full **test analysis** page per attempt with question-by-question breakdown
- **Leaderboards** to compare performance with peers
- Support for **explanations** on individual questions for post-test review

### 📊 Performance Analytics
- **Score trend** line chart across all attempts (Chart.js)
- **Answer breakdown** stacked bar chart (correct / wrong / skipped)
- Per-attempt **donut charts** with score percentage
- Summary stats: total tests taken, average score, personal best
- Color-coded score pills (green / yellow / red) for instant readability

### 📚 Study Materials
- Semester-wise → subject-wise → resource navigation
- Slide decks and course materials in a structured hierarchy
- Course detail pages with downloadable resources

### 👤 User Accounts
- Registration, login, logout (Django's built-in auth)
- Secure POST-based logout (Django 5+ compliant)
- Per-user test history and analytics
- Admin panel for content management
- CSRF protection on all forms

### 🎨 UI/UX
- Custom dark theme with an accent-driven design system
- Cursor-follow glow effect
- Fully responsive layout (desktop, tablet, mobile)
- Zero external CSS frameworks — hand-written, optimized CSS
- Inter font from Google Fonts
- Smooth micro-interactions and transitions

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6.1 |
| **Language** | Python 3.12+ |
| **Database** | PostgreSQL |
| **DB Connector** | `psycopg2-binary`, `dj-database-url` |
| **Static Files** | WhiteNoise |
| **Config Management** | `python-dotenv` |
| **Frontend Charts** | Chart.js 4.4 |
| **Typography** | Inter (Google Fonts) |
| **Version Control** | Git + GitHub |
| **Hosting** | *TBD — Render / Railway* |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- PostgreSQL installed locally, OR a hosted PostgreSQL instance
- Git installed locally

### 1. Clone the repository

```bash
git clone https://github.com/flyingmachine723/PESU-Nexus.git
cd PESU-Nexus
```

### 2. Create a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

You can use either a **local PostgreSQL install** or a **free hosted instance**:

**Local:** Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/), create a database, and note the connection details.

**Hosted (free options):** [Neon](https://neon.tech), [Railway](https://railway.app), [Supabase](https://supabase.com) — all provide free PostgreSQL with a connection string.

You'll need a connection URI in this format:

```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

> ⚠️ **If your password contains special characters** (`@`, `#`, `!`, `$`, `%`, `&`, etc.), you must URL-encode them first, or the connection string will break. Use this one-liner:
>
> ```bash
> python -c "import urllib.parse; print(urllib.parse.quote('your-raw-password'))"
> ```
>
> Paste the output as the password portion of `DATABASE_URL`.

### 5. Create a `.env` file

In the project root (same folder as `manage.py`), create a file named exactly `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

> 🔐 **Never commit `.env` to Git.** It's already listed in `.gitignore`.

**To generate a secure `SECRET_KEY` for production:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Run migrations

```bash
python manage.py migrate
```

This creates all Django tables (auth, sessions, admin) and your app tables in PostgreSQL.

**Verify:** Open your database client (or hosted dashboard) → check that Django's tables now exist.

### 7. Create an admin user

```bash
python manage.py createsuperuser
```

Enter username, email, and a strong password.

### 8. Start the development server

```bash
python manage.py runserver
```

Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser. 🎉

Log in with the superuser you created and explore the app hello
