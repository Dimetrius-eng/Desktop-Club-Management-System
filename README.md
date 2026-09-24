# Sports Club Management System

A desktop information system for managing local sports clubs and training sections. The application uses a Tkinter graphical interface and stores its data in MariaDB or MySQL.

## Features

- Role-based workspaces for administrators, managers, trainers, and clients.
- Manage sports sections, trainers, and training schedules.
- Register clients, sell memberships, enroll clients in training sessions, and track attendance.
- Show trainers their schedules and clients their memberships.
- Generate reports on revenue, trainer payroll, clients, memberships, and section activity.
- Search, filter, sort, and export reports.

## Requirements

- Windows 10 or 11
- Python 3.10 or later with Tkinter
- MariaDB 10.4 or later, or MySQL 8 or later

Tkinter is included with the standard Python installer for Windows. The application uses PyMySQL to connect to the database.

## Set Up the Database

1. Install and start MariaDB or MySQL.
2. Import `sports_club.sql`. The script creates the `sports_club` database, its tables, and demonstration records.
3. Check the connection settings near the top of `db_manager.py`: `host`, `database`, `user`, and `password`. The defaults expect a local database server with the `root` user and no password.

The SQL dump contains demonstration accounts and sample data. Replace them before using the application with real data.

## Install and Run

Open PowerShell in the project root and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

After importing the database, sign in with the demonstration administrator account: username `admin`, password `admin123`. The database dump contains accounts for the other roles as well.

## Project Files

- `main.py` — Tkinter interface and workflows for all four user roles.
- `db_manager.py` — database connection and SQL query helpers.
- `sports_club.sql` — MariaDB/MySQL schema and demonstration data.
- `requirements.txt` — external Python dependencies.
- `.gitignore` — excludes local environments and generated files.
