from .connection import get_db_connection
from werkzeug.security import generate_password_hash
import sqlite3

def get_all_users():
    with get_db_connection() as conn:
        return conn.execute('SELECT User_ID, Username, Password, Money FROM users').fetchall()

def get_user_money(user_id):
    with get_db_connection() as conn:
        result = conn.execute('SELECT Money FROM users WHERE User_Id = ?', (user_id,)).fetchone()
        return result['Money'] if result else 0

def get_user_by_username(username):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        result = cursor.execute('SELECT User_ID, Username, Password, Money FROM users WHERE Username = ?', (username,)).fetchone()
        return result

def create_user(username, email, password):
    with get_db_connection() as conn:
        # Check if username or email already exists
        result = conn.execute('SELECT 1 FROM users WHERE Username = ? OR Email = ?', (username, email)).fetchone()
        if result:
            return False, "Username or email already taken"
        
        # Hash password
        pw_hash = generate_password_hash(password)
        
        # Insert new user
        conn.execute('INSERT INTO users (Username, Email, Password, Money) VALUES (?, ?, ?, 10000)', (username, email, pw_hash))
        return True, None

def is_valid_email(email):
    import re
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
