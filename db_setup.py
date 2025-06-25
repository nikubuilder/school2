# db_setup.py

import sqlite3

def init_db():
    conn = sqlite3.connect("school.db")
    c = conn.cursor()

    # Admins table
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Teachers login table
    c.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Teacher details
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        father_name TEXT,
        id_card TEXT,
        education TEXT,
        contact TEXT,
        enrolment_id TEXT UNIQUE,
        status TEXT DEFAULT 'active'
    )''')

    # Students
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        father_name TEXT,
        mother_name TEXT,
        id_card TEXT,
        contact TEXT,
        student_class TEXT,
        enrolment_no TEXT UNIQUE,
        status TEXT DEFAULT 'active'
    )''')

    # Attendance
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrolment_no TEXT,
        role TEXT,  -- student or teacher
        date TEXT,
        time TEXT
    )''')

    # Test records
    c.execute('''CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT,
        test_date TEXT,
        full_marks INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS test_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER,
        student_enrolment TEXT,
        obtained_marks INTEGER,
        FOREIGN KEY(test_id) REFERENCES tests(id)
    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
