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

