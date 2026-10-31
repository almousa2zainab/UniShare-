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
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)

    # Number of available resources
    available_resources = conn.execute(
        "SELECT COUNT(*) FROM Equipment WHERE Status = 'Available'"
    ).fetchone()[0]

    # Number of currently borrowed resources
    currently_borrowed = conn.execute(
        "SELECT COUNT(*) FROM BorrowingRecord WHERE BorrowStatus = 'Borrowed'"
    ).fetchone()[0]

    # Number of printed graduation reports
    printed_reports = conn.execute(
        """SELECT COUNT(*) FROM Equipment
           WHERE Category = 'Printed AI / CS graduation reports'"""
    ).fetchone()[0]

    # Number of different resource categories
    resource_types = conn.execute(
        "SELECT COUNT(DISTINCT Category) FROM Equipment"
    ).fetchone()[0]
    # Get 3 resources for the dashboard snapshot 
    resources = conn.execute(
    """SELECT EquipmentName, Category, Status
       FROM Equipment
       ORDER BY EquipmentID
       LIMIT 3"""
    ).fetchall()
    recent_activity = conn.execute(
    """
    SELECT User.FullName,
           Equipment.EquipmentName,
           BorrowingRecord.RequestDate,
           BorrowingRecord.BorrowStatus
    FROM BorrowingRecord
    JOIN User
        ON BorrowingRecord.UserID = User.UserID
    JOIN Equipment
        ON BorrowingRecord.EquipmentID = Equipment.EquipmentID
    ORDER BY BorrowingRecord.RequestDate DESC
    LIMIT 3
    """
).fetchall()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        available_resources=available_resources,
        currently_borrowed=currently_borrowed,
        printed_reports=printed_reports,
        resource_types=resource_types,
        resources=resources,
        recent_activity=recent_activity,
        admin_name=session["name"]
    )
@app.route("/admin/resources")
def admin_resources():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    resources = conn.execute(
        """SELECT EquipmentID, EquipmentName, Category, Description,
                  AcademicYear, EquipmentRFID, Status, UploadedBy
           FROM Equipment
           ORDER BY EquipmentID"""
    ).fetchall()

    conn.close()

    return render_template(
        "admin/resources.html",
        resources=resources,
        admin_name=session["name"]
    )
@app.route("/admin/resources/add", methods=["GET", "POST"])
def add_resource():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        academic_year = request.form["academic_year"].strip()
        rfid = request.form["rfid"].strip()

        conn = sqlite3.connect(DB_PATH)

        conn.execute(
            """INSERT INTO Equipment
               (EquipmentName, Category, Description, AcademicYear,
                EquipmentRFID, Status, UploadedBy)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                name,
                category,
                description,
                academic_year or None,
                rfid or None,
                "Available",
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin_resources"))

    return render_template(
        "admin/add_resource.html",
        admin_name=session["name"]
    )
@app.route("/admin/resources/delete/<int:equipment_id>", methods=["POST"])
def delete_resource(equipment_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "DELETE FROM Equipment WHERE EquipmentID = ?",
        (equipment_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_resources"))
@app.route("/admin/resources/edit/<int:equipment_id>", methods=["GET", "POST"])
def edit_resource(equipment_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        academic_year = request.form["academic_year"].strip()
        rfid = request.form["rfid"].strip()
        status = request.form["status"]

        conn.execute(
            """UPDATE Equipment
               SET EquipmentName = ?,
                   Category = ?,
                   Description = ?,
                   AcademicYear = ?,
                   EquipmentRFID = ?,
                   Status = ?
               WHERE EquipmentID = ?""",
            (
                name,
                category,
                description,
                academic_year or None,
                rfid or None,
                status,
                equipment_id
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin_resources"))

    resource = conn.execute(
        "SELECT * FROM Equipment WHERE EquipmentID = ?",
        (equipment_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "admin/edit_resource.html",
        resource=resource,
        admin_name=session["name"]
    )
@app.route("/admin/transactions")
def admin_transactions():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    transactions = conn.execute(
        """
        SELECT BorrowingRecord.RecordID,
               User.FullName,
               Equipment.EquipmentName,
               BorrowingRecord.RequestDate,
               BorrowingRecord.BorrowDate,
               BorrowingRecord.ExpectedReturnDate,
               BorrowingRecord.ActualReturnDate,
               BorrowingRecord.BorrowStatus
        FROM BorrowingRecord
        JOIN User
            ON BorrowingRecord.UserID = User.UserID
        JOIN Equipment
            ON BorrowingRecord.EquipmentID = Equipment.EquipmentID
        ORDER BY BorrowingRecord.RecordID DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/transactions.html",
        transactions=transactions,
        admin_name=session["name"]
    )
@app.route("/admin/users")
def admin_users():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    users = conn.execute(
        """
        SELECT UserID, FullName, Email, Role
        FROM User
        ORDER BY UserID
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/users.html",
        users=users,
        admin_name=session["name"]
    )
@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    new_role = request.form["role"]

    if new_role not in ["Student", "Staff", "Admin"]:
        return redirect(url_for("admin_users"))

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "UPDATE User SET Role = ? WHERE UserID = ?",
        (new_role, user_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_users"))
if __name__ == "__main__":
    app.run(debug=True)