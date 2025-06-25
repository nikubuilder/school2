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

