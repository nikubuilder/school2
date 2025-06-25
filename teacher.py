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

