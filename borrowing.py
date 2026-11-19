
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "unishare.db"
)


def borrow_equipment(user_id, equipment_id, scanned_rfid, expected_return_date):
    """Borrow equipment after a trusted RFID reader verifies its tag."""

    if not scanned_rfid or not scanned_rfid.strip():
        return False, "RFID scan is required."

    scanned_rfid = scanned_rfid.strip().upper()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Lock writes while checking availability.
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute(
            "SELECT Role FROM User WHERE UserID = ?",
            (user_id,)
        ).fetchone()

        if not user or user["Role"] != "Student":
            return False, "Invalid student account."

        equipment = conn.execute(
            """SELECT EquipmentRFID, Status
               FROM Equipment WHERE EquipmentID = ?""",
            (equipment_id,)
        ).fetchone()

        if not equipment:
            return False, "Equipment not found."

        if equipment["Status"] != "Available":
            return False, "Equipment is not available."

        registered_rfid = equipment["EquipmentRFID"]

        if not registered_rfid:
            return False, "Equipment has no registered RFID tag."

        if registered_rfid.strip().upper() != scanned_rfid:
            return False, "RFID does not match the selected equipment."

        active_record = conn.execute(
            """SELECT RecordID FROM BorrowingRecord
               WHERE EquipmentID = ?
               AND BorrowStatus = 'Borrowed'""",
            (equipment_id,)
        ).fetchone()

        if active_record:
            return False, "Equipment is already borrowed."

        
        now = datetime.now()
        borrow_date = now.date().isoformat()

        try:
            selected_date = datetime.strptime(
                expected_return_date, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return False, "Invalid return date."

        min_date = now.date() + timedelta(days=1)
        max_date = now.date() + timedelta(days=14)

        if not min_date <= selected_date <= max_date:
            return False, (
                "Expected return date must be between "
                "1 and 14 days from today."
            )

        expected_return = selected_date.isoformat()
        

        conn.execute(
            """INSERT INTO BorrowingRecord
               (UserID, EquipmentID, RequestDate, BorrowDate,
                ExpectedReturnDate, ActualReturnDate, BorrowStatus)
               VALUES (?, ?, ?, ?, ?, NULL, 'Borrowed')""",
            (user_id, equipment_id, borrow_date,
             borrow_date, expected_return)
        )

        # Existing database triggers update Equipment.Status.
        conn.commit()
        return True, "Equipment borrowed successfully."

    except sqlite3.Error as error:
        conn.rollback()
        return False, f"Database error: {error}"

    finally:
        conn.close()


# RETURN LOGIC - Student 3
# Handles equipment returns for Staff and Admin.
# Validates the RFID against the borrowed equipment.
# Updates the borrowing record and equipment status.
#
# TODO: Student 3 - Connect Staff/Admin return buttons
# to the return verification workflow.
#
# TODO: Student 7 - Connect the physical RFID reader.
# RFID must come from a trusted source, not browser input.
def return_equipment(staff_id, record_id, scanned_rfid):
    """Confirm a return after trusted RFID verification."""

    if not isinstance(scanned_rfid, str) or not scanned_rfid.strip():
        return False, "RFID scan is required."

    scanned_rfid = scanned_rfid.strip().upper()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("BEGIN IMMEDIATE")

        staff = conn.execute(
            "SELECT Role FROM User WHERE UserID = ?",
            (staff_id,)
        ).fetchone()

        if not staff or staff["Role"] not in ("Staff", "Admin"):
            return False, "Only staff or admin can confirm returns."

        record = conn.execute(
            """
            SELECT br.RecordID, br.BorrowStatus,
                   e.EquipmentRFID, e.Status
            FROM BorrowingRecord AS br
            JOIN Equipment AS e
                ON br.EquipmentID = e.EquipmentID
            WHERE br.RecordID = ?
            """,
            (record_id,)
        ).fetchone()

        if record is None:
            return False, "Borrowing record not found."

        if record["BorrowStatus"] != "Borrowed":
            return False, "This equipment is not currently borrowed."

        if record["EquipmentRFID"] is None:
            return False, "Equipment has no registered RFID tag."

        registered_rfid = record["EquipmentRFID"].strip().upper()

        if scanned_rfid != registered_rfid:
            return False, "RFID does not match the borrowed equipment."

        if record["Status"] != "Borrowed":
            return False, "Equipment status is inconsistent."

        today = datetime.now().date().isoformat()

        conn.execute(
            """
            UPDATE BorrowingRecord
            SET ActualReturnDate = ?,
                BorrowStatus = 'Returned'
            WHERE RecordID = ?
              AND BorrowStatus = 'Borrowed'
            """,
            (today, record_id)
        )

        # Database trigger updates Equipment.Status.
        conn.commit()

        return True, "Equipment returned successfully."

    except sqlite3.Error as error:
        conn.rollback()
        return False, f"Database error: {error}"

    finally:
        conn.close()


