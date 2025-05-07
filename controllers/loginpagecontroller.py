import sqlite3

class LoginPageController:
    def login(self, username, password):
        """Login check for username and password."""
        try:
            print("Attempting login...")
            conn = sqlite3.connect('database.db', check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE Username = ? AND Password = ?", (username, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                print(f"User {username} found.")
            else:
                print("User not found.")
            return user is not None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
