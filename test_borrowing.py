
# TEST FILE ONLY
# Used to test borrowing, returning, and permissions.
# Not required for the production application.
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import borrowing


def test_borrow_and_return():

    # Create a temporary database copy.
    with tempfile.TemporaryDirectory() as folder:
        test_db = os.path.join(folder, "test_unishare.db")

        with sqlite3.connect(borrowing.DB_PATH) as source:
            with sqlite3.connect(test_db) as target:
                source.backup(target)

        with patch.object(borrowing, "DB_PATH", test_db):

            conn = sqlite3.connect(test_db)
            conn.row_factory = sqlite3.Row

            try:
                student = conn.execute(
                    """
                    SELECT UserID
                    FROM User
                    WHERE Role = 'Student'
                    LIMIT 1
                    """
                ).fetchone()

                employee = conn.execute(
                    """
                    SELECT UserID, Role
                    FROM User
                    WHERE Role IN ('Staff', 'Admin')
                    LIMIT 1
                    """
                ).fetchone()

                equipment = conn.execute(
                    """
                    SELECT EquipmentID, EquipmentRFID
                    FROM Equipment
                    WHERE Status = 'Available'
                    LIMIT 1
                    """
                ).fetchone()

                # Add a test RFID if the equipment has none.
                if equipment and not (
                    equipment["EquipmentRFID"] or ""
                ).strip():

                    conn.execute(
                        """
                        UPDATE Equipment
                        SET EquipmentRFID = ?
                        WHERE EquipmentID = ?
                        """,
                        (
                            "TEST-RFID-001",
                            equipment["EquipmentID"]
                        )
                    )

                    conn.commit()

                    equipment = conn.execute(
                        """
                        SELECT EquipmentID, EquipmentRFID
                        FROM Equipment
                        WHERE EquipmentID = ?
                        """,
                        (equipment["EquipmentID"],)
                    ).fetchone()

                if not student or not employee or not equipment:
                    print(
                        "Missing test data: Student, "
                        "Staff/Admin, or available equipment."
                    )
                    return

                student_id = student["UserID"]
                employee_id = employee["UserID"]
                equipment_id = equipment["EquipmentID"]
                rfid = equipment["EquipmentRFID"]

            finally:
                conn.close()

            return_date = (
                datetime.now().date() + timedelta(days=7)
            ).isoformat()

            # TEST 1: Borrow equipment.
            success, message = borrowing.borrow_equipment(
                student_id,
                equipment_id,
                rfid,
                return_date
            )

            print("Borrowing:", success, "-", message)
            assert success, message

            conn = sqlite3.connect(test_db)

            try:
                record = conn.execute(
                    """
                    SELECT RecordID
                    FROM BorrowingRecord
                    WHERE UserID = ?
                      AND EquipmentID = ?
                      AND BorrowStatus = 'Borrowed'
                    ORDER BY RecordID DESC
                    LIMIT 1
                    """,
                    (student_id, equipment_id)
                ).fetchone()

                assert record is not None
                record_id = record[0]

            finally:
                conn.close()

            # TEST 2: Reject incorrect RFID.
            success, message = borrowing.return_equipment(
                employee_id,
                record_id,
                "WRONG_RFID_FOR_TEST"
            )

            print("Wrong RFID:", success, "-", message)
            assert not success

            # TEST 3: Return with correct RFID.
            success, message = borrowing.return_equipment(
                employee_id,
                record_id,
                rfid
            )

            print("Returning:", success, "-", message)
            assert success, message

            # TEST 4: Verify database updates.
            conn = sqlite3.connect(test_db)

            try:
                record = conn.execute(
                    """
                    SELECT BorrowStatus, ActualReturnDate
                    FROM BorrowingRecord
                    WHERE RecordID = ?
                    """,
                    (record_id,)
                ).fetchone()

                equipment_status = conn.execute(
                    """
                    SELECT Status
                    FROM Equipment
                    WHERE EquipmentID = ?
                    """,
                    (equipment_id,)
                ).fetchone()

                assert record[0] == "Returned"
                assert record[1] is not None
                assert equipment_status[0] == "Available"

            finally:
                conn.close()

            print("ALL TESTS PASSED!")


def test_return_permissions():
    with tempfile.TemporaryDirectory() as folder:
        test_db = os.path.join(folder, "permissions_test.db")

        with sqlite3.connect(borrowing.DB_PATH) as source:
            with sqlite3.connect(test_db) as target:
                source.backup(target)

        with patch.object(borrowing, "DB_PATH", test_db):
            conn = sqlite3.connect(test_db)

            try:
                users = conn.execute(
                    """
                    SELECT UserID, Role
                    FROM User
                    WHERE Role IN ('Student', 'Staff', 'Admin')
                    """
                ).fetchall()

                roles = {
                    role: user_id
                    for user_id, role in users
                }

                for role in ("Student", "Staff", "Admin"):
                    assert role in roles, f"Missing {role} account"

                # An invalid record ID is enough to test
                # whether each role passes authorization.
                for role in ("Student", "Staff", "Admin"):
                    success, message = borrowing.return_equipment(
                        roles[role],
                        -1,
                        "TEST-RFID"
                    )

                    print(f"{role}: {message}")

                    if role == "Student":
                        assert not success
                        assert "Only staff or admin" in message
                    else:
                        assert not success
                        assert message == "Borrowing record not found."

                print("ALL PERMISSION TESTS PASSED!")

            finally:
                conn.close()

def test_additional_cases():
    with tempfile.TemporaryDirectory() as folder:
        test_db = os.path.join(folder, "extra_tests.db")

        with sqlite3.connect(borrowing.DB_PATH) as source:
            with sqlite3.connect(test_db) as target:
                source.backup(target)

        with patch.object(borrowing, "DB_PATH", test_db):
            conn = sqlite3.connect(test_db)
            conn.row_factory = sqlite3.Row

            try:
                student = conn.execute(
                    "SELECT UserID FROM User WHERE Role = 'Student' LIMIT 1"
                ).fetchone()

                employee = conn.execute(
                    """
                    SELECT UserID FROM User
                    WHERE Role IN ('Staff', 'Admin')
                    LIMIT 1
                    """
                ).fetchone()

                equipment = conn.execute(
                    """
                    SELECT EquipmentID, EquipmentRFID
                    FROM Equipment
                    WHERE Status = 'Available'
                    LIMIT 1
                    """
                ).fetchone()

                assert student, "No Student account found."
                assert employee, "No Staff/Admin account found."
                assert equipment, "No available equipment found."

                student_id = student["UserID"]
                employee_id = employee["UserID"]
                equipment_id = equipment["EquipmentID"]

                rfid = (equipment["EquipmentRFID"] or "").strip()

                if not rfid:
                    rfid = "TEST-RFID-EXTRA-001"
                    conn.execute(
                        """
                        UPDATE Equipment
                        SET EquipmentRFID = ?
                        WHERE EquipmentID = ?
                        """,
                        (rfid, equipment_id)
                    )
                    conn.commit()

            finally:
                conn.close()

            valid_date = (
                datetime.now().date() + timedelta(days=7)
            ).isoformat()

            invalid_date = (
                datetime.now().date() + timedelta(days=15)
            ).isoformat()

            # TEST 1: Reject invalid return date.
            success, message = borrowing.borrow_equipment(
                student_id, equipment_id, rfid, invalid_date
            )
            assert not success, "Invalid date was accepted."
            print("PASS: Return date over 14 days rejected.")

            # TEST 2: Reject incorrect borrowing RFID.
            success, message = borrowing.borrow_equipment(
                student_id,
                equipment_id,
                "WRONG-RFID-EXTRA-TEST",
                valid_date
            )
            assert not success, "Incorrect RFID was accepted."
            print("PASS: Incorrect borrowing RFID rejected.")

            # TEST 3: Borrow successfully.
            success, message = borrowing.borrow_equipment(
                student_id, equipment_id, rfid, valid_date
            )
            assert success, message
            print("PASS: Equipment borrowed successfully.")

            # TEST 4: Reject duplicate borrowing.
            success, message = borrowing.borrow_equipment(
                student_id, equipment_id, rfid, valid_date
            )
            assert not success, "Duplicate borrowing was accepted."
            print("PASS: Duplicate borrowing rejected.")

            # TEST 5: Verify My Borrowings data.
            conn = sqlite3.connect(test_db)
            conn.row_factory = sqlite3.Row

            try:
                record = conn.execute(
                    """
                    SELECT br.RecordID,
                           e.EquipmentName,
                           br.BorrowDate,
                           br.ExpectedReturnDate,
                           br.BorrowStatus
                    FROM BorrowingRecord AS br
                    JOIN Equipment AS e
                        ON br.EquipmentID = e.EquipmentID
                    WHERE br.UserID = ?
                      AND br.EquipmentID = ?
                      AND br.BorrowStatus = 'Borrowed'
                    ORDER BY br.RecordID DESC
                    LIMIT 1
                    """,
                    (student_id, equipment_id)
                ).fetchone()

                assert record, "Borrowing record not found."
                assert record["ExpectedReturnDate"] == valid_date
                assert record["BorrowStatus"] == "Borrowed"
                assert record["EquipmentName"]
                assert record["BorrowDate"]

                record_id = record["RecordID"]

            finally:
                conn.close()

            print("PASS: My Borrowings data verified.")

            # TEST 6: Return successfully.
            success, message = borrowing.return_equipment(
                employee_id, record_id, rfid
            )
            assert success, message
            print("PASS: Equipment returned successfully.")

            # TEST 7: Reject duplicate return.
            success, message = borrowing.return_equipment(
                employee_id, record_id, rfid
            )
            assert not success, "Duplicate return was accepted."
            print("PASS: Duplicate return rejected.")

            # TEST 8: Verify returned record.
            conn = sqlite3.connect(test_db)

            try:
                result = conn.execute(
                    """
                    SELECT BorrowStatus, ActualReturnDate
                    FROM BorrowingRecord
                    WHERE RecordID = ?
                    """,
                    (record_id,)
                ).fetchone()

                assert result[0] == "Returned"
                assert result[1] is not None

            finally:
                conn.close()

            print("PASS: Returned record updated.")
            print("ALL ADDITIONAL TESTS PASSED!")

if __name__ == "__main__":
    test_borrow_and_return()
    test_return_permissions()
    test_additional_cases()