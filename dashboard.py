# dashboard.py

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

DB = "school.db"

def fetch_count(query, params=()):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0


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

