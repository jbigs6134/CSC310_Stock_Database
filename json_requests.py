import requests, time
from datetime import datetime
from helper_files.stocks import insert_or_update_stock

API_KEY = 'IF0HEJ1Y252KI0W0'
request_count = 0
last_reset_date = datetime.now().date()
recent_requests = []

def enforce_rate_limit():
    global request_count, last_reset_date, recent_requests
    today = datetime.now().date()
    if today != last_reset_date:
        request_count, recent_requests, last_reset_date = 0, [], today

    now = datetime.now()
    recent_requests = [t for t in recent_requests if (now - t).total_seconds() < 60]

    if len(recent_requests) >= 5:
        wait_time = 60 - (now - recent_requests[0]).total_seconds()
        print(f"Rate limit reached: waiting {int(wait_time)+1} seconds...")
        time.sleep(wait_time + 1)

    recent_requests.append(datetime.now())
    request_count += 1
    print(f"API Request #{request_count} today")

def get_stock_data_batch():
    symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'META', 'TSLA', 'WMT',
               'JPM', 'XOM', 'COST', 'NFLX', 'BAC', 'DIS', 'MA', 'UNH', 'ORCL', 'PG', 'HD']

    for symbol in symbols:
        print(f"Fetching data for {symbol}")
        price = get_stock_price(symbol)
        company_info = get_company_info(symbol)

        if price is not None and company_info is not None:
            insert_or_update_stock({
                "symbol": symbol,
                "price": price,
                "name": company_info["name"],
                "sector": company_info["sector"]
            })

def get_company_info(symbol):
    enforce_rate_limit()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200 or "Name" not in data:
        return None
    return {"name": data.get("Name", "Unknown"), "sector": data.get("Sector", "Unknown")}

def get_stock_price(symbol):
    enforce_rate_limit()
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        return None
    latest = next(iter(time_series.items()))
    return float(latest[1]["4. close"])