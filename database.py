import sqlite3

# Connect to database
conn = sqlite3.connect("unishare.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


# Delete old tables

cursor.execute("DROP TABLE IF EXISTS BorrowingRecord")
cursor.execute("DROP TABLE IF EXISTS Equipment")
cursor.execute("DROP TABLE IF EXISTS User")
cursor.execute("DROP TABLE IF EXISTS GraduationReport")


# Create User Table

cursor.execute("""
CREATE TABLE User (
    UserID INTEGER PRIMARY KEY,
    FullName TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    Password TEXT NOT NULL,
    Role TEXT NOT NULL
)
""")

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
INSERT INTO User VALUES (?, ?, ?, ?, ?)
""", users)



# Create Equipment Table

cursor.execute("""
CREATE TABLE Equipment (
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



# Create BorrowingRecord Table

cursor.execute("""
CREATE TABLE BorrowingRecord (
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

conn.commit()

print("Database created successfully!")


# Display Tables

tables = ["User", "Equipment", "BorrowingRecord"]

for table in tables:
    print("\n" + "=" * 60)
    print(f"TABLE: {table}")
    print("=" * 60)

    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    columns = [description[0] for description in cursor.description]
    print(columns)

    for row in rows:
        print(row)

    print(f"\nTotal Records: {len(rows)}")

conn.close()
