# Smart HRMS

Smart HRMS is a Django-based human resources site for managing employees, departments, attendance, leave requests, and reports. It provides separate Admin, HR, and Employee workflows.

## Run Locally (Windows)

Requirements: Python 3.14.4 was used to verify this project. The current environment has Django 5.2.16. This repository does not currently include a dependency file.

From the project folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "Django==5.2.16"
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The root URL redirects to the login page at `/accounts/login/`.

The application initializes its SQLite tables from `sql/schema.sql` when Django loads its settings. If the database does not contain an Admin account, it creates the development account `admin` with password `admin123`. Change this password after signing in. The project folder currently includes `db.sqlite3`; using that database preserves its existing records and accounts.

## Modules

| Module | Purpose |
| --- | --- |
| `accounts` | Login, logout, password changes, and session-based role checks. |
| `admin_module` | Admin dashboard and HR account management. |
| `hr_module` | HR dashboard and employee account/profile management. |
| `employee_module` | Employee dashboard and self-service profile updates. |
| `department_module` | Department creation, editing, searching, and deletion. |
| `attendance_module` | Employee attendance marking and HR/Admin attendance records. |
| `leave_module` | Employee leave applications/history and request review actions. |
| `reports_module` | Employee, attendance, and leave reports with filters. |

## Project Layout

- `manage.py` and `smart_hrms/`: Django command entry point, settings, URL configuration, and SQLite helpers.
- `sql/schema.sql`: application database schema.
- `templates/`: Django HTML templates grouped by feature.
- `static/`: shared CSS and JavaScript.
- `tests/` and each app's `tests.py`: Django tests.

The app `models.py` files are placeholders. Application records are currently read and written with parameterized SQL through `smart_hrms/db.py`, rather than Django ORM models. Django migrations are still used for Django-managed tables such as sessions.

## Tests

Run the test suite with:

```powershell
python manage.py test
```

The application SQL helpers use the configured `db.sqlite3` path directly, so tests may write to that file instead of an isolated Django test database. Back up the database or use a disposable project copy before running tests against data you need to keep.

## Security Notes

This is a development project, not a production-ready deployment. `DEBUG` is enabled, the application seeds a known default Admin password, and the database stores plaintext password copies that are displayed in parts of the HR and reporting interface. Role checks are also incomplete for some attendance and leave URLs. Do not expose this application or real employee data until these issues are addressed. 


