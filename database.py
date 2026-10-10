import sqlite3

def create_database():
    conn = sqlite3.connect("unishare.db")
    cursor = conn.cursor()

    # foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")

# Table 1: User
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            FullName TEXT NOT NULL,
            Email TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Role TEXT NOT NULL,
            UserRFID TEXT UNIQUE
        )
    """)

# Table 2: Equipment
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Equipment (
            EquipmentID INTEGER PRIMARY KEY AUTOINCREMENT,
            EquipmentName TEXT NOT NULL,
            Category TEXT NOT NULL,
            Description TEXT,
            EquipmentRFID TEXT UNIQUE,
            Status TEXT NOT NULL DEFAULT 'Available'
        )
    """)

# Table 3: BorrowingRecord
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS BorrowingRecord (
            RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER NOT NULL,
            EquipmentID INTEGER NOT NULL,
            RequestDate TEXT NOT NULL,
            BorrowDate TEXT,
            ExpectedReturnDate TEXT,
            ActualReturnDate TEXT,
            BorrowStatus TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (UserID) REFERENCES User(UserID),
            FOREIGN KEY (EquipmentID) REFERENCES Equipment(EquipmentID)
        )
    """)

# Table 4: GraduationReport
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GraduationReport (
            ReportID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectTitle TEXT NOT NULL,
            AcademicYear TEXT NOT NULL,
            FilePath TEXT NOT NULL,
            UploadedBy INTEGER NOT NULL,
            FOREIGN KEY (UploadedBy) REFERENCES User(UserID)
        )
    """)

# User Data
    users = [
        (1, "Lara Hashem Alalmaei", "l_alalmaei@gmail.com", "L1234", "Student", None),
        (2, "Refah Abdulaziz Alsubiey", "r_alsubiey@gmail.com", "R1234", "Student", None),
        (3, "Shoug Bandar AlMaymuni", "s_almaymuni@gmail.com", "S1234", "Student", None),
        (4, "Zainab Mohammed Almousa", "z_almousa@gmail.com", "Z1234", "Student", None),
        (5, "Heba Saleh Albenmousa", "h_albenmousa@gmail.com", "H1234", "Student", None),
        (6, "Layan Mubarak Alotaibi", "l_alotaibi@gmail.com", "L1234", "Student", None),
        (7, "Moneerh Naif Alhaydhal", "m_alhaydhal@gmail.com", "M1234", "Student", None),
        (8, "Sarah Fahad Alqahtani", "s_alqahtani@gmail.com", "S1234", "Admin", None),
        (9, "Noura Hamad Alsultan", "n_alsultan@gmail.com", "N1234", "Admin", None),
        (10, "Reem Khalid Aldosari", "r_aldosari@gmail.com", "R1234", "Admin", None),
        (11, "Maha Sultan Alotibi", "m_alotibi@gmail.com", "M1234", "Staff", None),
        (12, "Ghala Ali Abuthiba", "g_abuthiba@gmail.com", "G1234", "Staff", None),
        (13, "Jawahir Saud Alharbi", "j_alharbi@gmail.com", "J1234", "Staff", None)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO User
        (UserID, FullName, Email, Password, Role, UserRFID)
        VALUES (?, ?, ?, ?, ?, ?)
    """, users)

# Equipment Data
    equipment = [
        (1, "Arduino Uno R3 Board", "Microcontrollers",
     "Main microcontroller board with mounting holes for RFID tag.",
     "EQ-RFID-101", "Available"),

        (2, "Breadboard (400 Tie Points)", "Prototyping",
     "Standard prototyping breadboard with side clip for RFID tag.",
     "EQ-RFID-102", "Available"),

        (3, "HC-SR04 Ultrasonic Sensor", "Sensors",
     "Distance measurement sensor module with eyelet hole.",
     "EQ-RFID-103", "Available"),

        (4, "DHT11 Temperature Sensor", "Sensors",
     "Basic digital temperature and humidity sensor module.",
     "EQ-RFID-104", "Borrowed"),

        (5, "SG90 Micro Servo Motor", "Motors",
     "Small servo motor with mounting hole on plastic arm.",
     "EQ-RFID-105", "Available"),

        (6, "Jumper Wires (Male-to-Male)", "Cables & Adapters",
     "Bundle of flexible jumper wires with tagged cable tie.",
     "EQ-RFID-106", "Available"),

        (7, "RGB LED Module", "LEDs",
     "RGB LED module for electronic prototyping.",
     "EQ-RFID-107", "Borrowed")
]

    cursor.executemany("""
    INSERT OR IGNORE INTO Equipment
    (EquipmentID, EquipmentName, Category, Description, EquipmentRFID, Status)
    VALUES (?, ?, ?, ?, ?, ?)
""", equipment)

# BorrowingRecord Data
    borrowing_records = [
    (1, 1, 3, "10-05-2026", "11-05-2026", "18-05-2026", "17-05-2026", "Returned"),
    (2, 2, 1, "12-05-2026", "12-05-2026", "20-05-2026", "19-05-2026", "Returned"),
    (3, 3, 4, "14-05-2026", "15-05-2026", "22-05-2026", None, "Borrowed"),
    (4, 4, 5, "15-05-2026", "16-05-2026", "23-05-2026", "22-05-2026", "Returned"),
    (5, 5, 6, "18-05-2026", "18-05-2026", "25-05-2026", None, "Borrowed"),
    (6, 6, 2, "20-05-2026", "21-05-2026", "28-05-2026", "27-05-2026", "Returned"),
    (7, 7, 7, "22-05-2026", "22-05-2026", "29-05-2026", None, "Borrowed")
    ]


    cursor.executemany("""
    INSERT OR IGNORE INTO BorrowingRecord
    (RecordID, UserID, EquipmentID, RequestDate, BorrowDate,
     ExpectedReturnDate, ActualReturnDate, BorrowStatus)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", borrowing_records)


# Save changes
    conn.commit()

   
# Display all tables and their data
    for table in ["User", "Equipment", "BorrowingRecord", "GraduationReport"]:
        print(f"\n{'-' * 80}")
        print(f"Table: {table}")
        print("=" * 80)

        cursor.execute(f"SELECT * FROM {table}")

        # Display column names
        columns = [description[0] for description in cursor.description]
        print(" | ".join(columns))
        print("-" * 80)

        # Display records
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                print(row)
        else:
            print("No records found.")

    conn.close()


# Display database summary
    print("UniShare database created successfully!")

    for table in ["User", "Equipment", "BorrowingRecord", "GraduationReport"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")

    conn.close()

if __name__ == "__main__":
    create_database()
