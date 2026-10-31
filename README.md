# UniShare

A smart management system for laboratory equipment and AI graduation projects. It uses RFID technology to track equipment and manage borrowing and returns, while enabling staff to manage resources, users, records, and reports efficiently.

## To view the tables more clearly in Visual Studio Code:

1. Open the Extensions panel.
2. Search for **SQLite Viewer** and install it.
3. Open the database in Visual Studio Code.
4. Select a table to view its columns and records.

The SQLite Viewer extension is optional.

## How to run the project

1. Install Python 3.14 (tick **Add Python to PATH**), Git, and VS Code.
2. Clone and set up:

```
git clone https://github.com/almousa2zainab/UniShare-.git
cd UniShare-
py -3.14 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

3. Open http://127.0.0.1:5000

## Test accounts

| Role | Email | Password |
|---|---|---|
| Student | z.almousa@gmail.com | Z1234 |
| Staff | m.alotibi@gmail.com | M1234 |
| Admin | s.alqahtani@gmail.com | S1234 |

## Rules for the team

- Work on your own branch (`git checkout -b your-name-feature`) and merge through pull requests.
- Keep the route function names `student_home`, `staff_home`, and `admin_home` in `app.py`.
- Start each page with a role check: if `session.get("role")` is not the right role, redirect to `login`.
- Do not edit `login.html` or `style.css`. Use your own CSS file.
- Do not run `database.py` once real data exists. It deletes and recreates all tables.

## Colors

- Navy `#0f2557`, Purple `#6c5ce7`, Lavender `#8b7bff`, Mid blue `#2a2f8f`
- Text `#1c1f33`, Muted `#6b7280`, Backgrounds `#f6f4fd` and `#ebe7fb`
- Font: Segoe UI, Arial, sans-serif
