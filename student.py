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

