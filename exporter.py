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

