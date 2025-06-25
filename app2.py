# combined_school_app.py
# A full School Management System with NFC, built with Streamlit

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date

# === DATABASE ===
DB = "school.db"


# === BEGIN auth.py ===
# auth.py

import sqlite3
import hashlib

DB = "school.db"
ADMIN_CODE = "3075"

def get_hashed_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_admin(username, password, code):
    if code != ADMIN_CODE:
        return "Invalid admin code!"
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                  (username, get_hashed_password(password)))
        conn.commit()
        return "Signup successful!"
    except sqlite3.IntegrityError:
        return "Username already exists!"
    finally:
        conn.close()

def login_user(role, username, password):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    table = "admins" if role == "Admin" else "teachers"
    c.execute(f"SELECT password FROM {table} WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0] == get_hashed_password(password):
        return True
    return False

def change_password(role, username, old_pass, new_pass):
    if not login_user(role, username, old_pass):
        return "Old password incorrect!"
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    table = "admins" if role == "Admin" else "teachers"
    c.execute(f"UPDATE {table} SET password = ? WHERE username = ?", 
              (get_hashed_password(new_pass), username))
    conn.commit()
    conn.close()
    return "Password changed successfully."


# === END auth.py ===


# === BEGIN db_setup.py ===
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

# === END db_setup.py ===


# === BEGIN dashboard.py ===
# dashboard.py

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px # type: ignore
from datetime import datetime

DB = "school.db"

def fetch_count(query):
    with sqlite3.connect(DB) as conn:
        return conn.execute(query).fetchone()[0]

def fetch_dataframe(query, params=()):
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query(query, conn, params=params)

def dashboard():
    st.title("📊 Dashboard")

    # === KPIs ===
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_students = fetch_count("SELECT COUNT(*) FROM students WHERE status='active'")
        st.metric("Total Students", total_students)

    with col2:
        total_teachers = fetch_count("SELECT COUNT(*) FROM teacher_details WHERE status='active'")
        st.metric("Total Teachers", total_teachers)

    today = datetime.now().strftime("%Y-%m-%d")

    with col3:
        present_students = fetch_count(
            "SELECT COUNT(DISTINCT enrolment_no) FROM attendance WHERE date=? AND role='student'", (today,))
        st.metric("Present Students Today", present_students)

    with col4:
        present_teachers = fetch_count(
            "SELECT COUNT(DISTINCT enrolment_no) FROM attendance WHERE date=? AND role='teacher'", (today,))
        st.metric("Present Teachers Today", present_teachers)

    st.markdown("---")

    # === Attendance Trends ===
    st.subheader("📈 Attendance Trends Over Time")
    role_filter = st.selectbox("Select Role", ["student", "teacher", "both"])

    if role_filter == "both":
        query = "SELECT date, role, COUNT(DISTINCT enrolment_no) as present FROM attendance GROUP BY date, role"
    else:
        query = "SELECT date, role, COUNT(DISTINCT enrolment_no) as present FROM attendance WHERE role=? GROUP BY date"

    df = fetch_dataframe(query, (role_filter,) if role_filter != "both" else ())

    if df.empty:
        st.info("No attendance data available to show trends.")
    else:
        fig = px.line(df, x="date", y="present", color="role", markers=True,
                      labels={"present": "Present Count", "date": "Date"},
                      title="Attendance Over Time")
        st.plotly_chart(fig, use_container_width=True)


# === END dashboard.py ===


# === BEGIN student.py ===
# student.py

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

DB = "school.db"

def generate_enrolment_no():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        now = datetime.now().strftime("%y%m%d%H%M%S")
        return f"STU-{now}"

def add_student_form():
    st.subheader("➕ Add New Student")

    with st.form("add_student_form"):
        name = st.text_input("Student Name", max_chars=100)
        father = st.text_input("Father's Name")
        mother = st.text_input("Mother's Name")
        id_card = st.text_input("ID Card Number")
        contact = st.text_input("Contact Number")
        student_class = st.text_input("Class")
        enrolment_no = st.text_input("Enrolment Number (leave blank to auto-generate)", value="")

        submitted = st.form_submit_button("Add Student")

        if submitted:
            if not name or not father or not mother or not id_card or not contact or not student_class:
                st.warning("Please fill in all fields.")
                return

            if enrolment_no.strip() == "":
                enrolment_no = generate_enrolment_no()

            try:
                with sqlite3.connect(DB) as conn:
                    conn.execute("""
                        INSERT INTO students 
                        (name, father_name, mother_name, id_card, contact, student_class, enrolment_no)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (name, father, mother, id_card, contact, student_class, enrolment_no))
                    conn.commit()
                st.success(f"Student added with Enrolment No: {enrolment_no}")
            except sqlite3.IntegrityError:
                st.error("Enrolment number already exists!")

def live_search_students():
    st.subheader("🔍 Search Students")

    keyword = st.text_input("Search by name, parent name, ID card, contact, or class")

    query = """
        SELECT id, name, father_name, mother_name, id_card, contact, student_class, enrolment_no 
        FROM students WHERE status='active' AND (
            name LIKE ? OR father_name LIKE ? OR mother_name LIKE ? OR 
            id_card LIKE ? OR contact LIKE ? OR student_class LIKE ?
        )
        ORDER BY id DESC
    """

    like_keyword = f"%{keyword}%"
    df = pd.read_sql_query(query, sqlite3.connect(DB),
                           params=(like_keyword,)*6)

    st.dataframe(df, use_container_width=True)

def drop_student():
    st.subheader("📤 Drop Student")

    enrolment_no = st.text_input("Enter Enrolment Number to Drop")

    if st.button("Drop Student"):
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM students WHERE enrolment_no=? AND status='active'", (enrolment_no,))
            result = c.fetchone()
            if result:
                c.execute("UPDATE students SET status='dropped' WHERE enrolment_no=?", (enrolment_no,))
                conn.commit()
                st.success(f"Student '{result[0]}' has been dropped.")
            else:
                st.error("No active student found with that enrolment number.")

def student_page():
    if st.session_state.role != "Admin":
        st.error("Access denied. Admins only.")
        return

    st.title("🎓 Student Management")

    tabs = st.tabs(["Add Student", "Search Students", "Drop Student"])

    with tabs[0]:
        add_student_form()
    with tabs[1]:
        live_search_students()
    with tabs[2]:
        drop_student()


# === END student.py ===


# === BEGIN teacher.py ===
# teacher.py

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import hashlib

DB = "school.db"

def get_hashed_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_enrolment_id():
    now = datetime.now().strftime("%y%m%d%H%M%S")
    return f"TCH-{now}"

def add_teacher_form():
    st.subheader("➕ Add New Teacher")

    with st.form("add_teacher_form"):
        name = st.text_input("Name")
        father = st.text_input("Father's Name")
        id_card = st.text_input("ID Card Number")
        education = st.text_input("Education")
        contact = st.text_input("Contact Number")
        enrolment_id = st.text_input("Enrolment ID (leave blank to auto-generate)", value="")

        username = st.text_input("Login Username")
        password = st.text_input("Login Password", type="password")

        submitted = st.form_submit_button("Add Teacher")

        if submitted:
            if not name or not father or not id_card or not education or not contact or not username or not password:
                st.warning("Please fill in all fields.")
                return

            if enrolment_id.strip() == "":
                enrolment_id = generate_enrolment_id()

            try:
                with sqlite3.connect(DB) as conn:
                    # Insert into teacher details
                    conn.execute("""
                        INSERT INTO teacher_details 
                        (name, father_name, id_card, education, contact, enrolment_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, father, id_card, education, contact, enrolment_id))

                    # Insert into login credentials
                    conn.execute("""
                        INSERT INTO teachers (username, password)
                        VALUES (?, ?)
                    """, (username, get_hashed_password(password)))

                    conn.commit()

                st.success(f"Teacher added with Enrolment ID: {enrolment_id}")
            except sqlite3.IntegrityError as e:
                st.error("Username or Enrolment ID already exists.")

def live_search_teachers():
    st.subheader("🔍 Search Teachers")

    keyword = st.text_input("Search by name, father name, ID card, education, contact")

    query = """
        SELECT id, name, father_name, id_card, education, contact, enrolment_id 
        FROM teacher_details WHERE status='active' AND (
            name LIKE ? OR father_name LIKE ? OR id_card LIKE ? OR 
            education LIKE ? OR contact LIKE ?
        )
        ORDER BY id DESC
    """

    like_keyword = f"%{keyword}%"
    df = pd.read_sql_query(query, sqlite3.connect(DB),
                           params=(like_keyword,)*5)

    st.dataframe(df, use_container_width=True)

def resign_teacher():
    st.subheader("📤 Resign Teacher")

    enrolment_id = st.text_input("Enter Enrolment ID to Resign")

    if st.button("Resign Teacher"):
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM teacher_details WHERE enrolment_id=? AND status='active'", (enrolment_id,))
            result = c.fetchone()
            if result:
                c.execute("UPDATE teacher_details SET status='resigned' WHERE enrolment_id=?", (enrolment_id,))
                conn.commit()
                st.success(f"Teacher '{result[0]}' has been marked as resigned.")
            else:
                st.error("No active teacher found with that enrolment ID.")

def teacher_page():
    if st.session_state.role != "Admin":
        st.error("Access denied. Admins only.")
        return

    st.title("👨‍🏫 Teacher Management")

    tabs = st.tabs(["Add Teacher", "Search Teachers", "Resign Teacher"])

    with tabs[0]:
        add_teacher_form()
    with tabs[1]:
        live_search_teachers()
    with tabs[2]:
        resign_teacher()


# === END teacher.py ===


# === BEGIN attendance.py ===
# attendance.py

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

DB = "school.db"

try:
    import nfc
    NFC_AVAILABLE = True
except ImportError:
    NFC_AVAILABLE = False

def read_nfc_uid():
    try:
        clf = nfc.ContactlessFrontend('usb')
        tag = clf.connect(rdwr={'on-connect': lambda tag: False})
        clf.close()
        return str(tag).strip()
    except Exception as e:
        return None

def mark_attendance():
    st.subheader("📝 Mark Attendance")

    use_nfc = st.toggle("Use NFC for Attendance", value=False, disabled=not NFC_AVAILABLE)
    role = st.selectbox("Select Role", ["student", "teacher"])

    if use_nfc:
        st.info("Tap NFC card to mark attendance.")
        if st.button("Scan NFC"):
            uid = read_nfc_uid()
            if not uid:
                st.error("NFC read failed. Please try again.")
                return

            table = "students" if role == "student" else "teacher_details"
            uid_column = "nfc_uid"

            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT enrolment_no FROM {table} WHERE {uid_column} = ?", (uid,))
                result = cursor.fetchone()
                if not result:
                    st.error("NFC card not registered.")
                    return
                enrolment_no = result[0]
    else:
        enrolment_no = st.text_input("Enter Enrolment Number")
        if not enrolment_no.strip():
            st.warning("Please enter a valid enrolment number.")
            return

    if st.button("Mark Attendance"):
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")

        with sqlite3.connect(DB) as conn:
            table = "students" if role == "student" else "teacher_details"
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE enrolment_no = ?", (enrolment_no,))
            if cursor.fetchone():
                cursor.execute("INSERT INTO attendance (enrolment_no, role, date, time) VALUES (?, ?, ?, ?)",
                               (enrolment_no, role, date, time))
                conn.commit()
                st.success(f"Attendance marked for {enrolment_no} at {time}")
            else:
                st.error("Enrolment number not found.")



# === END attendance.py ===


# === BEGIN test.py ===
# test.py

import sqlite3
import pandas as pd
import streamlit as st
from datetime import date

DB = "school.db"

def create_test():
    st.subheader("🧪 Create New Test")

    with st.form("create_test_form"):
        test_name = st.text_input("Test Name")
        test_date = st.date_input("Test Date", value=date.today())
        full_marks = st.number_input("Full Marks", min_value=1, step=1)

        submitted = st.form_submit_button("Create Test")

        if submitted:
            with sqlite3.connect(DB) as conn:
                conn.execute("""
                    INSERT INTO tests (test_name, test_date, full_marks)
                    VALUES (?, ?, ?)
                """, (test_name, test_date.strftime("%Y-%m-%d"), full_marks))
                conn.commit()
                st.success("Test created successfully!")

def add_test_records():
    st.subheader("➕ Add Student Marks to Test")

    # Load existing tests
    with sqlite3.connect(DB) as conn:
        tests = conn.execute("SELECT id, test_name, test_date FROM tests ORDER BY id DESC").fetchall()

    if not tests:
        st.warning("No tests available. Please create a test first.")
        return

    test_map = {f"{name} ({d})": tid for tid, name, d in tests}
    test_selected = st.selectbox("Select Test", list(test_map.keys()))
    test_id = test_map[test_selected]

    with st.form("add_scores_form"):
        enrolment_no = st.text_input("Student Enrolment Number")
        obtained_marks = st.number_input("Obtained Marks", min_value=0, step=1)

        submitted = st.form_submit_button("Add Record")

        if submitted:
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM students WHERE enrolment_no=? AND status='active'", (enrolment_no,))
                result = cursor.fetchone()

                if not result:
                    st.error("No active student found with that enrolment number.")
                    return

                cursor.execute("""
                    INSERT INTO test_records (test_id, student_enrolment, obtained_marks)
                    VALUES (?, ?, ?)
                """, (test_id, enrolment_no, obtained_marks))
                conn.commit()

                st.success(f"Score added for {enrolment_no}.")

def view_test_records():
    st.subheader("📑 View Test Records")

    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query("""
            SELECT tr.id, t.test_name, t.test_date, tr.student_enrolment, tr.obtained_marks, t.full_marks
            FROM test_records tr
            JOIN tests t ON tr.test_id = t.id
            ORDER BY t.test_date DESC
        """, conn)

    if df.empty:
        st.info("No test records found.")
    else:
        df["Percentage"] = (df["obtained_marks"] / df["full_marks"]) * 100
        st.dataframe(df, use_container_width=True)

def test_page():
    st.title("🧪 Test Management")

    tabs = st.tabs(["Create Test", "Add Student Marks", "View Test Records"])

    with tabs[0]:
        create_test()
    with tabs[1]:
        add_test_records()
    with tabs[2]:
        view_test_records()


# === END test.py ===


# === BEGIN exporter.py ===
# exporter.py

import sqlite3
import pandas as pd
import streamlit as st
from io import BytesIO

DB = "school.db"

def get_attendance_df():
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("SELECT * FROM attendance ORDER BY date DESC, time DESC", conn)

def get_test_df():
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("""
            SELECT tr.id, t.test_name, t.test_date, tr.student_enrolment, tr.obtained_marks, t.full_marks
            FROM test_records tr
            JOIN tests t ON tr.test_id = t.id
            ORDER BY t.test_date DESC
        """, conn)

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def convert_df_to_xlsx(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return output.getvalue()

def export_page():
    if st.session_state.role != "Admin":
        st.error("Access denied. Admins only.")
        return

    st.title("📤 Export Data")

    export_tabs = st.tabs(["Export Attendance", "Export Test Records"])

    # === Attendance Export ===
    with export_tabs[0]:
        st.subheader("📅 Attendance Records")
        att_df = get_attendance_df()

        if att_df.empty:
            st.info("No attendance data found.")
        else:
            st.dataframe(att_df, use_container_width=True)

            csv = convert_df_to_csv(att_df)
            xlsx = convert_df_to_xlsx(att_df)

            st.download_button("⬇️ Download CSV", data=csv, file_name="attendance.csv", mime="text/csv")
            st.download_button("⬇️ Download Excel", data=xlsx, file_name="attendance.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # === Test Record Export ===
    with export_tabs[1]:
        st.subheader("🧪 Test Records")
        test_df = get_test_df()

        if test_df.empty:
            st.info("No test records found.")
        else:
            st.dataframe(test_df, use_container_width=True)

            csv = convert_df_to_csv(test_df)
            xlsx = convert_df_to_xlsx(test_df)

            st.download_button("⬇️ Download CSV", data=csv, file_name="test_records.csv", mime="text/csv")
            st.download_button("⬇️ Download Excel", data=xlsx, file_name="test_records.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# === END exporter.py ===


# === BEGIN nfc_register.py ===
# nfc_register.py

import sqlite3
import streamlit as st

DB = "school.db"

def read_nfc_uid():
    try:
        import nfc
        clf = nfc.ContactlessFrontend('usb')
        tag = clf.connect(rdwr={'on-connect': lambda tag: False})
        clf.close()
        return str(tag.identifier.hex())
    except Exception as e:
        st.error(f"NFC read failed: {e}")
        return None

def assign_nfc_uid():
    st.title("📇 NFC Registration")
    if st.session_state.role != "Admin":
        st.error("Access denied. Admins only.")
        return

    st.subheader("📡 Scan NFC Card")
    uid = None

    if st.button("Scan Now"):
        uid = read_nfc_uid()
        if uid:
            st.success(f"NFC UID Detected: {uid}")

            # Check if UID is already assigned
            with sqlite3.connect(DB) as conn:
                cur = conn.cursor()
                cur.execute("SELECT enrolment_no FROM students WHERE nfc_uid=?", (uid,))
                student = cur.fetchone()
                cur.execute("SELECT enrolment_id FROM teacher_details WHERE nfc_uid=?", (uid,))
                teacher = cur.fetchone()

            if student:
                st.warning(f"UID already assigned to student: {student[0]}")
            elif teacher:
                st.warning(f"UID already assigned to teacher: {teacher[0]}")
            else:
                st.success("This card is available for assignment.")

    st.subheader("🔗 Assign UID to User")

    role = st.radio("Assign To", ["student", "teacher"], horizontal=True)
    enrol_input = st.text_input("Enter Enrolment No (student) or Enrolment ID (teacher)")

    if uid and enrol_input and st.button("Assign Card"):
        table = "students" if role == "student" else "teacher_details"
        enrol_col = "enrolment_no" if role == "student" else "enrolment_id"

        with sqlite3.connect(DB) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT id FROM {table} WHERE {enrol_col}=? AND status='active'", (enrol_input,))
            if cur.fetchone():
                cur.execute(f"UPDATE {table} SET nfc_uid=? WHERE {enrol_col}=?", (uid, enrol_input))
                conn.commit()
                st.success(f"NFC card assigned to {role} successfully.")
            else:
                st.error("No active user found with that enrolment.")

def nfc_register_page():
    assign_nfc_uid()
# === END nfc_register.py ===


# === BEGIN app.py ===

from auth import login_user, signup_admin, change_password as cp
from dashboard import dashboard as dashboard_page
from student import student_page
from teacher import teacher_page
from attendance import attendance_page
from test import test_page
from exporter import export_page
from nfc_register import nfc_register_page

# Simulated session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

st.set_page_config(page_title="School Management", layout="wide")

# === Page Routing ===
def login():
    st.title("🔐 Login")
    role = st.selectbox("Role", ["Admin", "Teacher"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(role, username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = role
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

def admin_signup():
    st.title("📝 Admin Signup")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    code = st.text_input("Admin Code", type="password")
    if st.button("Sign Up"):
        msg = signup_admin(username, password, code)
        if "successful" in msg:
            st.success(msg)
        else:
            st.error(msg)

def change_password_ui():
    st.title("🔒 Change Password")
    role = st.session_state.role if st.session_state.authenticated else st.selectbox("Role", ["Admin", "Teacher"])
    username = st.session_state.username if st.session_state.authenticated else st.text_input("Username")
    old_pass = st.text_input("Old Password", type="password")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Change Password"):
        result = cp(role, username, old_pass, new_pass)
        if "successfully" in result:
            st.success(result)
        else:
            st.error(result)

# Navigation Menu
if st.session_state.authenticated:
    menu = ["Dashboard", "Students", "Teachers", "Attendance", "Tests", "Export", "NFC Register", "Change Password", "Logout"]
else:
    menu = ["Login", "Admin Signup", "Change Password"]

choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Login":
    login()
elif choice == "Admin Signup":
    admin_signup()
elif choice == "Change Password":
    change_password_ui()
elif choice == "Logout":
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.success("Logged out.")
    st.rerun()
elif st.session_state.authenticated:
    if choice == "Dashboard":
        dashboard_page()
    elif choice == "Students" and st.session_state.role == "Admin":
        student_page()
    elif choice == "Teachers" and st.session_state.role == "Admin":
        teacher_page()
    elif choice == "Attendance":
        attendance_page()
    elif choice == "Tests":
        test_page()
    elif choice == "Export" and st.session_state.role == "Admin":
        export_page()
    elif choice == "NFC Register" and st.session_state.role == "Admin":
        nfc_register_page()
