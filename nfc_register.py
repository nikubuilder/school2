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