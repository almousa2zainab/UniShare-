import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-text"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unishare.db")

ROLE_HOME = {
    "Student": "student_home",
    "Staff": "staff_home",
    "Admin": "admin_home",
}


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute(
        "SELECT UserID, FullName, Email, Password, Role FROM User WHERE Email = ?",
        (email,),
    ).fetchone()
    conn.close()
    return user


def start_session(user_id, name, role):
    session.clear()
    session["user_id"] = user_id
    session["name"] = name
    session["role"] = role


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = get_user_by_email(email)
        if user and user["Password"] == password:
            start_session(user["UserID"], user["FullName"], user["Role"])
            return redirect(url_for(ROLE_HOME[user["Role"]]))

        error = "Invalid email or password."

    return render_template("login.html", error=error, mode="login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("login.html", mode="signup")

    name = request.form["name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]
    confirm = request.form["confirm"]

    error = None
    if len(name) < 3:
        error = "Please enter your full name."
    elif len(password) < 6:
        error = "Password must be at least 6 characters."
    elif password != confirm:
        error = "Passwords do not match."

    if not error:
        conn = sqlite3.connect(DB_PATH)
        try:
            # New accounts are always Students. Roles are changed by the Administrator.
            cur = conn.execute(
                "INSERT INTO User (FullName, Email, Password, Role) VALUES (?, ?, ?, ?)",
                (name, email, password, "Student"),
            )
            conn.commit()
            start_session(cur.lastrowid, name, "Student")
            return redirect(url_for("student_home"))
        except sqlite3.IntegrityError:
            error = "This email is already registered."
        finally:
            conn.close()

    return render_template("login.html", error=error, mode="signup")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Temporary placeholder pages (teammates will replace these)
def role_page(role, title):
    if session.get("role") != role:
        return redirect(url_for("login"))
    return (
        f"<h1>{title}</h1>"
        f"<p>Welcome, {escape(session['name'])}</p>"
        f"<a href='{url_for('logout')}'>Logout</a>"
    )


@app.route("/student")
def student_home():
    return role_page("Student", "Student Home")


@app.route("/staff")
def staff_home():
    return role_page("Staff", "Staff Dashboard")


@app.route("/admin")
def admin_home():
    return role_page("Admin", "Administrator Portal")


if __name__ == "__main__":
    app.run(debug=True)