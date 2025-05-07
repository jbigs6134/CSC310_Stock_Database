from .connection import get_db_connection

def get_all_stocks():
    with get_db_connection() as conn:
        return conn.execute('SELECT Ticker_Name, Full_Name, Price, Sector FROM stocks').fetchall()

def insert_or_update_stock(stock_data):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO stocks (ticker_name, full_name, price, sector)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker_name)
            DO UPDATE SET
                full_name = excluded.full_name,
                price = excluded.price,
                sector = excluded.sector
        """, (
            stock_data['symbol'], stock_data['name'], stock_data['price'], stock_data['sector']
        ))
        conn.commit()

def get_stocks_from_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Query to fetch all stock data from the stocks table
        cursor.execute('''SELECT Ticker_Name, Full_Name, Price, Sector FROM stocks''')
        stocks = cursor.fetchall()

    return stocks