from .connection import get_db_connection
from .transactions import add_transaction
import sqlite3

def get_user_holdings(user_id):
    with get_db_connection() as conn:
        return conn.execute(
        """
        SELECT 
            h.Ticker_Name,
            SUM(h.quantity) AS quantity, 
            s.Full_Name, 
            s.Price 
        FROM holdings h 
        JOIN stocks s ON h.Ticker_Name = s.Ticker_Name 
        WHERE h.User_id = ? 
        GROUP BY h.Ticker_Name
        HAVING SUM(h.quantity) > 0
        """, (user_id,)
    ).fetchall()

def add_to_holdings_db(form_data, user):
    ticker = form_data.get('Ticker_Name') 
    quantity = int(form_data.get('quantity', 0))  
    
    user_id = user['User_ID']
    
    # Get the current price for this ticker
    with get_db_connection() as conn:
        price = 0
        result = conn.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,)).fetchone()
        if result:
            price = result['Price']
        
        # Insert or update holdings
        conn.execute("""
            INSERT INTO holdings (User_ID, Ticker_Name, Price, Quantity, Date_bought, Price_bought)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(User_ID, Ticker_Name) 
            DO UPDATE SET Quantity = Quantity + excluded.Quantity
        """, (user_id, ticker, price, quantity, price))
        
        # Update user's money
        total_cost = price * quantity
        conn.execute("UPDATE users SET Money = Money - ? WHERE User_ID = ?", (total_cost, user_id))
        
        # Add transaction record
        add_transaction(user_id, ticker, quantity, price, 'Buy', conn)
        
        conn.commit()

def sell_stock_db(user, ticker):
    user_id = user['User_ID']
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch the unique holding row
        cursor.execute("SELECT Holdings_ID, Quantity FROM holdings WHERE User_ID = ? AND Ticker_Name = ?", (user_id, ticker))
        row = cursor.fetchone()

        if not row:
            raise ValueError("Holding not found for this user and ticker")

        rowid, quantity = row['Holdings_ID'], row['quantity']
        if quantity <= 0:
            raise ValueError("Cannot sell stock. No stock to sell")

        # Update or delete the row
        if quantity == 1:
            cursor.execute("DELETE FROM holdings WHERE rowid = ?", (rowid,))
        else:
            cursor.execute("UPDATE holdings SET quantity = ? WHERE rowid = ?", (quantity - 1, rowid))

        # Get current price
        cursor.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,))
        stock_row = cursor.fetchone()
        price = stock_row['Price'] if stock_row else 0

        # Add transaction and update money
        add_transaction(user_id, ticker, 1, price, 'Sell', conn)
        cursor.execute("UPDATE users SET Money = Money + ? WHERE User_ID = ?", (price, user_id))

        conn.commit()

    except Exception as e:
        print(f"[sell_stock_db] Error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
