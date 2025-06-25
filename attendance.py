# attendance.py

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

DB = "school.db"


def mark_attendance():
    st.subheader("📝 Mark Attendance")

    role = st.selectbox("Select Role", ["student", "teacher"])
    use_nfc = st.checkbox("Use NFC to Mark Attendance")

    enrolment_no = ""

    if use_nfc:
        st.info("Please scan the NFC card...")
        if st.button("Scan NFC"):
            try:
                import nfc
                clf = nfc.ContactlessFrontend('usb')
                tag = clf.connect(rdwr={'on-connect': lambda tag: False})
                clf.close()
                uid = str(tag.identifier.hex())
                st.success(f"NFC UID: {uid}")

                table = "students" if role == "student" else "teacher_details"
                enrol_col = "enrolment_no" if role == "student" else "enrolment_id"
                with sqlite3.connect(DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT {enrol_col} FROM {table} WHERE nfc_uid=? AND status='active'", (uid,))
                    result = cursor.fetchone()
                    if result:
                        enrolment_no = result[0]
                        st.success(f"Detected Enrolment: {enrolment_no}")
                    else:
                        st.error("No active user found with this NFC UID.")
                        return
            except Exception as e:
                st.error(f"NFC scan failed: {e}")
                return
    else:
        enrolment_no = st.text_input("Enter Enrolment Number")

    if st.button("Mark Attendance"):
        if not enrolment_no.strip():
            st.warning("Please enter a valid enrolment number.")
            return

        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")

        with sqlite3.connect(DB) as conn:
            table = "students" if role == "student" else "teacher_details"
            cursor = conn.cursor()
            column = "enrolment_no" if table == "students" else "enrolment_id"
            cursor.execute(f"SELECT id FROM {table} WHERE {column}=? AND status='active'", (enrolment_no,))
            result = cursor.fetchone()

            if not result:
                st.error(f"No active {role} found with enrolment number '{enrolment_no}'.")
                return

            conn.execute("""
                INSERT INTO attendance (enrolment_no, role, date, time)
                VALUES (?, ?, ?, ?)
            """, (enrolment_no, role, date, time))
            conn.commit()

            st.success(f"{role.title()} attendance marked for {enrolment_no} at {time} on {date}")


def view_attendance_records():
    st.subheader("📅 View Attendance Records")

    role_filter = st.selectbox("Filter by Role", ["All", "student", "teacher"])
    date_filter = st.date_input("Filter by Date (optional)", value=None)

    query = "SELECT * FROM attendance WHERE 1=1"
    params = []

    if role_filter != "All":
        query += " AND role=?"
        params.append(role_filter)

    if date_filter:
        query += " AND date=?"
        params.append(date_filter.strftime("%Y-%m-%d"))

    query += " ORDER BY date DESC, time DESC"

    df = pd.read_sql_query(query, sqlite3.connect(DB), params=params)

    st.dataframe(df, use_container_width=True)

def attendance_page():
    st.title("📋 Attendance Management")

    tabs = st.tabs(["Mark Attendance", "View Attendance Records"])

    with tabs[0]:
        mark_attendance()
    with tabs[1]:
        view_attendance_records()

