import sqlite3


def get_stocks_from_db():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        
        # Query to get stock data from the stocks table
        cursor.execute('''SELECT Ticker_Name, Full_Name, Price, Sector FROM stocks''')
        stocks = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching stocks: {e}")
        stocks = []
    finally:
        conn.close()

    return stocks

def get_logins_from_db():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query to get login data from the users table
        cursor.execute('''SELECT User_id, Username, Password, Money FROM users''')
        logins = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching logins: {e}")
        logins = []
    finally:
        conn.close()

    return logins

def is_in_watchlist(user_id, stock_symbol):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Corrected SQL query to prevent SQL injection
        cursor.execute('''SELECT COUNT(*) FROM watchlist WHERE User_id = ? AND Ticker_Name = ?''', (user_id, stock_symbol))
        result = cursor.fetchone()[0]

        return result > 0
    except sqlite3.Error as e:
        print(f"Error checking watchlist: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_money(user_id):
    conn = None
    money = 0
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''SELECT Money FROM users WHERE User_id = ?''', (user_id,))
        result = cursor.fetchone()

        if result:
            money = result[0]
    finally:
        if conn:
            conn.close()
        return money

