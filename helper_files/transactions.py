from .connection import get_db_connection

def add_transaction(user_id, ticker_name, quantity, price, transaction_type, conn):
    cursor = conn.cursor()
    
    # Insert transaction record
    cursor.execute("""
        INSERT INTO transactions (User_ID, Ticker_Name, Quantity, Price, Transaction_Type, Transaction_Date)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, ticker_name, float(quantity), float(price), transaction_type))
    
    conn.commit()

def get_transactions(user_id):
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        cursor.execute('''SELECT * FROM transactions WHERE User_ID = ?''', (user_id,))
        transactions = cursor.fetchall()

        return transactions

    except sqlite3.Error as e:
        print(f"Error getting Transaction: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

