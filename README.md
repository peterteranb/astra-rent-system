# astra-rent-system

Equipment loan management for SergioCorp, a simulated company that rents party sound equipment. Software Engineering course project P01 (equipment loans).

Current phase: plain Python and pytest, with in-memory data. There is no database or user interface yet.

## Requirements

- Python 3.10 or newer
- Git

## Setup

Clone the repository and enter it:

````bash
git clone https://github.com/peterteranb/astra-rent-system.git
cd astra-rent-system
````

Create and activate a virtual environment.

Linux or macOS:

````bash
python3 -m venv .venv
source .venv/bin/activate
````

Windows (PowerShell or Command Prompt):

````bat
python -m venv .venv
.venv\Scripts\activate
````

If `python` is not found on Windows, use `py` instead. If PowerShell refuses to run the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

Install the dependencies:

````bash
python -m pip install -r requirements.txt
````

## Running the tests

From the repository root, with the virtual environment active:

````bash
python -m pytest -q
````

Use `python -m pytest -v` to see each test by name.

## Database setup

The project uses PostgreSQL. Each developer runs their own local copy.

1. Install PostgreSQL (keep port 5432) and remember the `postgres` password.
2. Create the user and the database. On Windows (adjust the version folder if needed):
```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -v db_password=YOUR_PASSWORD -f scripts/create_db.sql
```
   On Linux:
```bash
   psql -U postgres -h localhost -v db_password=YOUR_PASSWORD -f scripts/create_db.sql
```
3. Copy `.env.example` to `.env` and set `DB_PASSWORD` to the password from step 2.
4. Create the tables:
```bash
   python manage.py migrate
```
5. Run `python manage.py migrate` again after every `git pull`.

If port 8000 is blocked on Windows, run the server on another port: `python manage.py runserver 8080`.

## Team

- Uriel ([@peterteranb](https://github.com/peterteranb))
- Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew))
- Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang))