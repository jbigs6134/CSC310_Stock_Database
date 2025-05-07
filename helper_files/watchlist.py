from .connection import get_db_connection
from .users import get_user_by_username
import sqlite3



def get_user_watchlist(username):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT w.Ticker_Name, s.Full_Name, s.Sector, s.Price
            FROM watchlist w
            JOIN users u ON w.User_ID = u.User_ID
            JOIN stocks s ON w.Ticker_Name = s.Ticker_Name
            WHERE u.Username = ?
            """,
            (username,),
        )
        watchlist = cursor.fetchall()
    return watchlist

def is_in_watchlist(user_id, stock_symbol):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM watchlist WHERE User_ID = ? AND Ticker_Name = ?',
            (user_id, stock_symbol),
        )
        result = cursor.fetchone()
    return result[0] > 0

def toggle_watchlist_db(user_id, ticker):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get the current price for this ticker
        cursor.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,))
        row = cursor.fetchone()
        if row:
            price = row[0]
        else:
            return None  # Stock not found
        
        # Check if the stock is already in the watchlist
        cursor.execute("SELECT 1 FROM watchlist WHERE User_ID = ? AND Ticker_Name = ?", (user_id, ticker))
        exists = cursor.fetchone()

        if exists:
            # Remove from watchlist
            cursor.execute("DELETE FROM watchlist WHERE User_ID = ? AND Ticker_Name = ?", (user_id, ticker))
        else:
            # Add to watchlist
            cursor.execute("INSERT INTO watchlist (User_ID, Ticker_Name, Price) VALUES (?, ?, ?)", (user_id, ticker, price))

        conn.commit()
    return True
