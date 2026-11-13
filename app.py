import os
import re
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, abort
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

# ============ STUDENT PAGES (Refah) - replace the old student_home with this block ============
# Category name -> resource type (must match database.py exactly).
# Any other category (Microcontrollers, Sensors, Motors, ...) counts as equipment.
CATEGORY_TYPE = {
    "Candidate printed research papers": ("paper", "Research paper"),
    "Printed AI / CS graduation reports": ("report", "Graduation report"),
}


@app.route("/student")
def student_home():
    if session.get("role") != "Student":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT EquipmentID, EquipmentName, Category, Description, "
        "AcademicYear, Status FROM Equipment ORDER BY EquipmentID"
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        item["type"], item["type_label"] = CATEGORY_TYPE.get(
            item["Category"], ("equipment", "Lab equipment")
        )
        items.append(item)

    counts = {
        "total": len(items),
        "available": sum(1 for i in items if i["Status"] == "Available"),
        "borrowed": sum(1 for i in items if i["Status"] == "Borrowed"),
        "equipment": sum(1 for i in items if i["type"] == "equipment"),
        "paper": sum(1 for i in items if i["type"] == "paper"),
        "report": sum(1 for i in items if i["type"] == "report"),
    }
    categories = sorted({i["Category"] for i in items})

    return render_template(
        "student.html",
        name=session["name"],
        items=items,
        counts=counts,
        categories=categories,
    )
# ============ END STUDENT PAGES ============



# ========== STAFF RESOURCE MANAGEMENT(Shoug) ==========

PAPER_CAT = "Candidate printed research papers"
REPORT_CAT = "Printed AI / CS graduation reports"

STAFF_CATEGORIES = [
    "Microcontrollers",
    "Prototyping",
    "Sensors",
    "Motors",
    PAPER_CAT,
    REPORT_CAT,
]

ALL_STATUSES = ("Available", "Borrowed", "Maintenance")


def clean_resource_form(form):
    return {
        "name": form.get("name", "").strip(),
        "category": form.get("category", ""),
        "description": form.get("description", "").strip(),
        "academic_year": form.get("academic_year", "").strip(),
        "rfid": form.get("rfid", "").strip().upper(),
        "status": form.get("status", "Available"),
    }


def validate_resource(data):
    if not data["name"]:
        return "Resource name is required."
    if data["category"] not in STAFF_CATEGORIES:
        return "Please choose a valid category."
    if data["academic_year"] and not re.fullmatch(r"\d{4}", data["academic_year"]):
        return "Academic year must be 4 digits, for example 2026."
    return None


def friendly_db_error(e):
    if "EquipmentRFID" in str(e):
        return "This RFID UID is already assigned to another resource."
    return str(e)


@app.route("/staff")
def staff_home():

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)

    total_resources = conn.execute(
        "SELECT COUNT(*) FROM Equipment"
    ).fetchone()[0]

    available_resources = conn.execute(
        "SELECT COUNT(*) FROM Equipment WHERE Status = 'Available'"
    ).fetchone()[0]

    borrowed_resources = conn.execute(
        "SELECT COUNT(*) FROM Equipment WHERE Status = 'Borrowed'"
    ).fetchone()[0]

    printed_reports = conn.execute(
        "SELECT COUNT(*) FROM Equipment WHERE Category IN (?, ?)",
        (PAPER_CAT, REPORT_CAT)
    ).fetchone()[0]

    recent_resources = conn.execute(
        """SELECT EquipmentName, Category, Status
           FROM Equipment
           ORDER BY EquipmentID DESC
           LIMIT 5"""
    ).fetchall()

    conn.close()

    return render_template(
        "staff/dashboard.html",
        staff_name=session["name"],
        total_resources=total_resources,
        available_resources=available_resources,
        borrowed_resources=borrowed_resources,
        printed_reports=printed_reports,
        recent_resources=recent_resources
    )


# VIEW ALL RESOURCES

@app.route("/staff/resources")
def staff_resources():

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    resources = conn.execute(
        "SELECT * FROM Equipment ORDER BY EquipmentID"
    ).fetchall()

    conn.close()

    return render_template(
        "staff/resources.html",
        resources=resources,
        staff_name=session["name"]
    )


# ADD RESOURCE

@app.route("/staff/resources/add", methods=["GET", "POST"])
def staff_add_resource():

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    error = None
    form = {}

    if request.method == "POST":
        form = clean_resource_form(request.form)
        error = validate_resource(form)

        if not error:
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute(
                    """INSERT INTO Equipment
                       (EquipmentName, Category, Description,
                        AcademicYear, EquipmentRFID, Status, UploadedBy)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        form["name"],
                        form["category"],
                        form["description"],
                        form["academic_year"] or None,
                        form["rfid"] or None,
                        "Available",
                        session["user_id"]
                    )
                )
                conn.commit()
                return redirect(url_for("staff_resources"))

            except sqlite3.IntegrityError as e:
                error = friendly_db_error(e)

            finally:
                conn.close()

    return render_template(
        "staff/add_resource.html",
        staff_name=session["name"],
        categories=STAFF_CATEGORIES,
        form=form,
        error=error
    )


# EDIT RESOURCE

@app.route("/staff/resources/edit/<int:equipment_id>",
           methods=["GET", "POST"])
def staff_edit_resource(equipment_id):

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        resource = conn.execute(
            "SELECT * FROM Equipment WHERE EquipmentID = ?",
            (equipment_id,)
        ).fetchone()

        if resource is None:
            abort(404)

        error = None

        if request.method == "POST":
            data = clean_resource_form(request.form)
            error = validate_resource(data)

            if not error and data["status"] not in ALL_STATUSES:
                error = "Invalid status."

            if not error and data["status"] == "Borrowed":
                active = conn.execute(
                    """SELECT 1 FROM BorrowingRecord
                       WHERE EquipmentID = ? AND BorrowStatus = 'Borrowed'""",
                    (equipment_id,)
                ).fetchone()
                if not active:
                    error = ("Borrowed is set automatically when a "
                             "student borrows the item.")

            if not error:
                try:
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
                            data["name"],
                            data["category"],
                            data["description"],
                            data["academic_year"] or None,
                            data["rfid"] or None,
                            data["status"],
                            equipment_id
                        )
                    )
                    conn.commit()
                    return redirect(url_for("staff_resources"))

                except sqlite3.IntegrityError as e:
                    error = friendly_db_error(e)

            # keep what the user typed so the form is not reset
            resource = {
                "EquipmentID": equipment_id,
                "EquipmentName": data["name"],
                "Category": data["category"],
                "Description": data["description"],
                "AcademicYear": data["academic_year"],
                "EquipmentRFID": data["rfid"],
                "Status": data["status"],
            }

        return render_template(
            "staff/edit_resource.html",
            resource=resource,
            staff_name=session["name"],
            categories=STAFF_CATEGORIES,
            error=error
        )

    finally:
        conn.close()


# PRINTED PROJECT REPORTS

@app.route("/staff/reports")
def staff_reports():

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    reports = conn.execute(
        """SELECT *
           FROM Equipment
           WHERE Category IN (?, ?)
           ORDER BY EquipmentID""",
        (PAPER_CAT, REPORT_CAT)
    ).fetchall()

    conn.close()

    return render_template(
        "staff/printed_reports.html",
        reports=reports,
        staff_name=session["name"]
    )

# ========== END STAFF RESOURCE MANAGEMENT(Shoug) ==========

# ========== ADMIN PAGES (Lara) ==========
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
# ========== END ADMIN PAGES ==========
if __name__ == "__main__":
    app.run(debug=True)