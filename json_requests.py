import requests, sqlite3, time, json
from datetime import datetime

API_KEY = 'IF0HEJ1Y252KI0W0'

request_count = 0
last_reset_date = datetime.now().date()
recent_requests = []

def enforce_rate_limit():
    global request_count, last_reset_date, recent_requests

    # Reset daily counters
    today = datetime.now().date()
    if today != last_reset_date:
        request_count = 0
        last_reset_date = today
        recent_requests = []

    if request_count >= 500:
        raise Exception("Daily API request limit reached (500/day).")

    # Enforce 5 requests per minute
    now = datetime.now()
    recent_requests = [t for t in recent_requests if (now - t).total_seconds() < 60]

    if len(recent_requests) >= 5:
        wait_time = 60 - (now - recent_requests[0]).total_seconds()
        print(f"Rate limit reached: waiting {int(wait_time) + 1} seconds...")
        time.sleep(wait_time + 1)

    # Register this request
    recent_requests.append(datetime.now())
    request_count += 1
    print(f"API Request #{request_count} today")

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_stock_data_batch():
    symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'META', 'TSLA', 'WMT',
               'JPM', 'XOM', 'COST', 'NFLX', 'BAC', 'DIS', 'MA', 'UNH', 'ORCL', 'PG', 'HD']

    for symbol in symbols:
        print(f"Fetching data for {symbol}")
        price = get_stock_price(symbol)
        company_info = get_company_info(symbol)

        if price is not None and company_info is not None:
            stock_data = {
                "symbol": symbol,
                "price": price,
                "name": company_info["name"],
                "sector": company_info["sector"]
            }
            insert_or_update_stock(stock_data)

def get_company_info(symbol):
    enforce_rate_limit()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch company info for {symbol}")
        return None

    data = response.json()
    if "Name" not in data:
        print(f"No company data for {symbol}")
        return None

    return {
        "name": data.get("Name", "Unknown"),
        "sector": data.get("Sector", "Unknown")
    }

def get_stock_price(symbol):
    enforce_rate_limit()
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch price for {symbol}")
        return None

    data = response.json()
    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        print(f"No price data for {symbol}")
        return None

    latest = next(iter(time_series.items()))
    return float(latest[1]["4. close"])

def insert_or_update_stock(stock_data):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO stocks (ticker_name, full_name, price, sector)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ticker_name)
        DO UPDATE SET
            full_name = excluded.full_name,
            price = excluded.price,
            sector = excluded.sector
    """, (
        stock_data["symbol"],
        stock_data["name"],
        stock_data["price"],
        stock_data["sector"]
    ))

    conn.commit()
    conn.close()
