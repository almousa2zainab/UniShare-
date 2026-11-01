import os
import sqlite3

# Database path
DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "unishare.db"
)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Delete the old GraduationReport table
cursor.execute("DROP TABLE IF EXISTS GraduationReport")

try:
    # CREATE TABLES

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS User (
        UserID INTEGER PRIMARY KEY,
        FullName TEXT NOT NULL,
        Email TEXT NOT NULL UNIQUE,
        Password TEXT NOT NULL,
        Role TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Equipment (
        EquipmentID INTEGER PRIMARY KEY,
        EquipmentName TEXT NOT NULL,
        Category TEXT NOT NULL,
        Description TEXT,
        AcademicYear TEXT,
        EquipmentRFID TEXT UNIQUE,
        Status TEXT NOT NULL,
        UploadedBy INTEGER,
        FOREIGN KEY (UploadedBy) REFERENCES User(UserID)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BorrowingRecord (
        RecordID INTEGER PRIMARY KEY,
        UserID INTEGER NOT NULL,
        EquipmentID INTEGER NOT NULL,
        RequestDate TEXT NOT NULL,
        BorrowDate TEXT,
        ExpectedReturnDate TEXT,
        ActualReturnDate TEXT,
        BorrowStatus TEXT NOT NULL,
        FOREIGN KEY (UserID) REFERENCES User(UserID),
        FOREIGN KEY (EquipmentID) REFERENCES Equipment(EquipmentID)
    )
    """)

    
    #INSERT INITIAL DATA ONLY IF TABLE IS EMPTY

    cursor.execute("SELECT COUNT(*) FROM User")
    if cursor.fetchone()[0] == 0:

        users = [
            (1, "Lara Hashem Alalmaei", "l.alalmaei@gmail.com", "L1234", "Student"),
            (2, "Refah Abdulaziz Alsubiey", "r.alsubiey@gmail.com", "R1234", "Student"),
            (3, "Shoug Bandar AlMaymuni", "s.almaymuni@gmail.com", "S1234", "Student"),
            (4, "Zainab Mohammed Almousa", "z.almousa@gmail.com", "Z1234", "Student"),
            (5, "Heba Saleh Albenmousa", "h.albenmousa@gmail.com", "H1234", "Student"),
            (6, "Layan Mubarak Alotaibi", "l.alotaibi@gmail.com", "L1234", "Student"),
            (7, "Moneerh Naif Alhaydhal", "m.alhaydhal@gmail.com", "M1234", "Student"),
            (8, "Sarah Fahad Alqahtani", "s.alqahtani@gmail.com", "S1234", "Admin"),
            (9, "Noura Hamad Alsultan", "n.alsultan@gmail.com", "N1234", "Admin"),
            (10, "Reem Khalid Aldosari", "r.aldosari@gmail.com", "R1234", "Admin"),
            (11, "Maha Sultan Alotibi", "m.alotibi@gmail.com", "M1234", "Staff"),
            (12, "Ghala Ali Abuthiba", "g.abuthiba@gmail.com", "G1234", "Staff"),
            (13, "Jawahir Saud Alharbi", "j.alharbi@gmail.com", "J1234", "Staff")
        ]

        cursor.executemany("""
        INSERT INTO User
        (UserID, FullName, Email, Password, Role)
        VALUES (?, ?, ?, ?, ?)
        """, users)

    cursor.execute("SELECT COUNT(*) FROM Equipment")
    if cursor.fetchone()[0] == 0:

        equipment = [
            (1, "Arduino Uno R3 Board", "Microcontrollers",
             "Microcontroller board with RFID tag mounting.",
             None, None, "Available", 11),

            (2, "Breadboard (400 Tie Points)", "Prototyping",
             "Prototyping breadboard with RFID side clip.",
             None, None, "Available", 11),

            (3, "HC-SR04 Ultrasonic Sensor", "Sensors",
             "Distance measurement sensor module.",
             None, None, "Available", 12),

            (4, "DHT11 Temperature Sensor", "Sensors",
             "Temperature and humidity sensor module.",
             None, None, "Borrowed", 12),

            (5, "SG90 Micro Servo Motor", "Motors",
             "Lightweight servo motor on plastic arm.",
             None, None, "Available", 13),

            (6, "PR001", "Candidate printed research papers",
             "Explainable AI framework for Alzheimer's disease diagnosis.",
             "2024", None, "Available", 11),

            (7, "PR002", "Candidate printed research papers",
             "Real-time crop row detection in agricultural robotics.",
             "2024", None, "Available", 11),

            (8, "PR003", "Candidate printed research papers",
             "Abstractive LSTM for automatic text summarization.",
             "2024", None, "Available", 12),

            (9, "GP001", "Printed AI / CS graduation reports",
             "Supervised and unsupervised models for disease extraction.",
             "2024", None, "Available", 11),

            (10, "GP002", "Printed AI / CS graduation reports",
             "Ground-truth neural cavity using IMU on bicycles.",
             "2024", None, "Available", 12),

            (11, "GP003", "Printed AI / CS graduation reports",
             "Generative AI study on academic performance.",
             "2024", None, "Available", 13)
        ]

        cursor.executemany("""
        INSERT INTO Equipment
        (EquipmentID, EquipmentName, Category, Description,
         AcademicYear, EquipmentRFID, Status, UploadedBy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, equipment)

    cursor.execute("SELECT COUNT(*) FROM BorrowingRecord")
    if cursor.fetchone()[0] == 0:

        borrowings = [
            (1, 1, 3, "2026-10-05", "2026-10-05", "2026-10-12", "2026-10-10", "Returned"),
            (2, 2, 1, "2026-10-06", "2026-10-06", "2026-10-13", "2026-10-11", "Returned"),
            (3, 3, 4, "2026-10-08", "2026-10-09", "2026-10-16", None, "Borrowed"),
            (4, 4, 5, "2026-10-09", "2026-10-10", "2026-10-17", "2026-10-14", "Returned"),
            (5, 5, 6, "2026-10-10", "2026-10-10", "2026-10-17", None, "Borrowed"),
            (6, 6, 2, "2026-10-11", "2026-10-12", "2026-10-19", "2026-10-14", "Returned"),
            (7, 7, 7, "2026-10-12", "2026-10-12", "2026-10-19", None, "Borrowed")
        ]

        cursor.executemany("""
        INSERT INTO BorrowingRecord
        (RecordID, UserID, EquipmentID, RequestDate, BorrowDate,
         ExpectedReturnDate, ActualReturnDate, BorrowStatus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, borrowings)


    # FIX EXISTING EQUIPMENT STATUSES

    cursor.execute("""
    UPDATE Equipment
    SET Status = 'Borrowed'
    WHERE EquipmentID IN (
        SELECT DISTINCT EquipmentID
        FROM BorrowingRecord
        WHERE BorrowStatus = 'Borrowed'
    )
    """)

    cursor.execute("""
    UPDATE Equipment
    SET Status = 'Available'
    WHERE Status != 'Maintenance'
    AND EquipmentID NOT IN (
        SELECT DISTINCT EquipmentID
        FROM BorrowingRecord
        WHERE BorrowStatus = 'Borrowed'
    )
    """)

    # PREVENT DUPLICATE ACTIVE BORROWINGS

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS one_active_borrow_per_equipment
    ON BorrowingRecord(EquipmentID)
    WHERE BorrowStatus = 'Borrowed'
    """)


    # STATUS VALIDATION TRIGGERS

    trigger_names = [
        "validate_equipment_status_insert",
        "validate_equipment_status_update",
        "validate_borrow_status_insert",
        "validate_borrow_status_update",
        "prevent_borrow_on_maintenance_insert",
        "prevent_borrow_on_maintenance_update",
        "prevent_equipment_unavailable_if_active",
        "sync_equipment_after_borrow_insert",
        "sync_equipment_after_borrow_update",
        "sync_equipment_after_borrow_delete"
    ]

    for name in trigger_names:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name}")

    cursor.execute("""
    CREATE TRIGGER validate_equipment_status_insert
    BEFORE INSERT ON Equipment
    WHEN NEW.Status NOT IN ('Available', 'Borrowed', 'Maintenance')
    BEGIN
        SELECT RAISE(ABORT, 'Invalid Equipment Status');
    END
    """)

    cursor.execute("""
    CREATE TRIGGER validate_equipment_status_update
    BEFORE UPDATE OF Status ON Equipment
    WHEN NEW.Status NOT IN ('Available', 'Borrowed', 'Maintenance')
    BEGIN
        SELECT RAISE(ABORT, 'Invalid Equipment Status');
    END
    """)

    cursor.execute("""
    CREATE TRIGGER validate_borrow_status_insert
    BEFORE INSERT ON BorrowingRecord
    WHEN NEW.BorrowStatus NOT IN ('Borrowed', 'Returned')
    BEGIN
        SELECT RAISE(ABORT, 'Invalid Borrowing Status');
    END
    """)

    cursor.execute("""
    CREATE TRIGGER validate_borrow_status_update
    BEFORE UPDATE OF BorrowStatus ON BorrowingRecord
    WHEN NEW.BorrowStatus NOT IN ('Borrowed', 'Returned')
    BEGIN
        SELECT RAISE(ABORT, 'Invalid Borrowing Status');
    END
    """)


    # PREVENT BORROWING MAINTENANCE EQUIPMENT

    cursor.execute("""
    CREATE TRIGGER prevent_borrow_on_maintenance_insert
    BEFORE INSERT ON BorrowingRecord
    WHEN NEW.BorrowStatus = 'Borrowed'
    AND (
        SELECT Status FROM Equipment
        WHERE EquipmentID = NEW.EquipmentID
    ) = 'Maintenance'
    BEGIN
        SELECT RAISE(ABORT, 'Equipment is under maintenance');
    END
    """)

    cursor.execute("""
    CREATE TRIGGER prevent_borrow_on_maintenance_update
    BEFORE UPDATE OF BorrowStatus, EquipmentID ON BorrowingRecord
    WHEN NEW.BorrowStatus = 'Borrowed'
    AND (
        SELECT Status FROM Equipment
        WHERE EquipmentID = NEW.EquipmentID
    ) = 'Maintenance'
    BEGIN
        SELECT RAISE(ABORT, 'Equipment is under maintenance');
    END
    """)


    # PREVENT INVALID EQUIPMENT STATUS CHANGES

    cursor.execute("""
    CREATE TRIGGER prevent_equipment_unavailable_if_active
    BEFORE UPDATE OF Status ON Equipment
    WHEN NEW.Status IN ('Available', 'Maintenance')
    AND EXISTS (
        SELECT 1
        FROM BorrowingRecord
        WHERE EquipmentID = OLD.EquipmentID
        AND BorrowStatus = 'Borrowed'
    )
    BEGIN
        SELECT RAISE(ABORT, 'Equipment has an active borrowing record');
    END
    """)

    # AUTOMATIC STATUS SYNCHRONIZATION

    # When a new borrowing record is inserted
    cursor.execute("""
    CREATE TRIGGER sync_equipment_after_borrow_insert
    AFTER INSERT ON BorrowingRecord
    WHEN NEW.BorrowStatus = 'Borrowed'
    BEGIN
        UPDATE Equipment
        SET Status = 'Borrowed'
        WHERE EquipmentID = NEW.EquipmentID;
    END
    """)

    # When a borrowing record is updated
    cursor.execute("""
    CREATE TRIGGER sync_equipment_after_borrow_update
    AFTER UPDATE OF BorrowStatus, EquipmentID ON BorrowingRecord
    BEGIN

        UPDATE Equipment
        SET Status = 'Available'
        WHERE EquipmentID = OLD.EquipmentID
        AND Status != 'Maintenance'
        AND NOT EXISTS (
            SELECT 1
            FROM BorrowingRecord
            WHERE EquipmentID = OLD.EquipmentID
            AND BorrowStatus = 'Borrowed'
        );

        UPDATE Equipment
        SET Status = 'Borrowed'
        WHERE EquipmentID = NEW.EquipmentID
        AND NEW.BorrowStatus = 'Borrowed';

        UPDATE Equipment
        SET Status = 'Available'
        WHERE EquipmentID = NEW.EquipmentID
        AND NEW.BorrowStatus = 'Returned'
        AND Status != 'Maintenance'
        AND NOT EXISTS (
            SELECT 1
            FROM BorrowingRecord
            WHERE EquipmentID = NEW.EquipmentID
            AND BorrowStatus = 'Borrowed'
        );

    END
    """)

    # When a borrowing record is deleted
    cursor.execute("""
    CREATE TRIGGER sync_equipment_after_borrow_delete
    AFTER DELETE ON BorrowingRecord
    WHEN OLD.BorrowStatus = 'Borrowed'
    BEGIN
        UPDATE Equipment
        SET Status = 'Available'
        WHERE EquipmentID = OLD.EquipmentID
        AND Status != 'Maintenance'
        AND NOT EXISTS (
            SELECT 1
            FROM BorrowingRecord
            WHERE EquipmentID = OLD.EquipmentID
            AND BorrowStatus = 'Borrowed'
        );
    END
    """)

    conn.commit()

    tables = ["User", "Equipment", "BorrowingRecord"]

    for table in tables:
        print(f"\nTABLE: {table}")

        cursor.execute(f"SELECT * FROM {table}")

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        print(" | ".join(columns))

        for row in rows:
            print(" | ".join(str(value) if value is not None else "NULL" for value in row))

        print(f"Total Records: {len(rows)}")

except Exception as error:
    conn.rollback()
    print("Database error:", error)
    raise

finally:
    conn.close()