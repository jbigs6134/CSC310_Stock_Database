import os, sqlite3, json, secrets, re, firebase_admin
from flask_apscheduler import APScheduler
from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from firebase_admin import credentials, auth
from database import *
from json_requests import get_stock_data_batch # Assuming this is the correct import
from functools import wraps



app = Flask(__name__)

app.config['SCHEDULER_API_ENABLED'] = True
app.config['SESSION_COOKIE_NAME'] = 'session_cookie'
app.config['SESSION_TYPE'] = 'filesystem'  # or 'redis', etc.
app.secret_key = secrets.token_hex(16)  # Random string for security
app.config['SESSION_PERMANENT'] = True
scheduler = APScheduler()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Use a global variable to store the username
main_username = ""

def token_required(f):
    def decorated(*args, **kwargs):
        if not main_username:
            return jsonify({'message': 'Token is missing'}), 403
        
        return f(*args, **kwargs)

    return decorated

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not main_username:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#@scheduler.task('cron', id='fetch_stocks', hour='8,11,12,14,15', minute='30', timezone='America/Chicago')
#def scheduled_task():
#    print("Running scheduled stock fetch...")
#    get_stock_data_batch()


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/about")
def about():
    return render_template('about.html')


def get_user_by_username(username):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
 SELECT User_id, Username, Password, Money FROM users WHERE Username = ?
 """,
        (username,)
    )
    row = cursor.fetchone()    
    if row == None:
        return None

    conn.close()
    return row

def get_user_holdings(user_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
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
    )
    holdings = cursor.fetchall()
    conn.close()
    return holdings


def get_user_watchlist(username):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT w.Ticker_Name, s.Full_Name, s.Sector, s.Price
        FROM watchlist w
        JOIN users u ON w.User_id = u.User_id
        JOIN stocks s ON w.Ticker_Name = s.Ticker_Name
        WHERE u.Username = ?
        """,
        (username,),
    )

    watchlist = cursor.fetchall()
    conn.close()
    return watchlist

def create_user(username, email, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute("SELECT 1 FROM users WHERE Username = ? OR Email = ?", (username, email))
    if cursor.fetchone():
        conn.close()
        return False, "Username or email already taken"

    pw_hash = generate_password_hash(password)
    cursor.execute(
 """
 INSERT INTO users (Username, Email, Password, Money) VALUES (?, ?, ?, 10000)""",
        (username, email, pw_hash),
    )
    conn.commit()
    conn.close()
    return True, None


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user_row = get_user_by_username(username)
        if user_row and check_password_hash(user_row[2], password):
            global main_username
            main_username = username  # Set the global variable
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'})
    return render_template('loginpage.html')

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        success, error = create_user(username, email, password)
        if not is_valid_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'})
        if success:
            global main_username
            main_username = username  # Set the global variable
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': error})
    else:
        return render_template('register.html')


@app.route('/home')
@login_required
def home():
    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    return render_template('homepage.html', username=main_username, money=money)


@app.route('/logout')
def logout():
    global main_username
    main_username = ""
    return redirect(url_for('login'))




@app.route('/stocks')
def stocks():
    #get_stock_data_batch()  # Fetch stocks from your database
    stocks_data = get_stocks_from_db()
    user_holdings = get_user_holdings(main_username)
    user_watchlist = get_user_watchlist(main_username)
    
    watchlist_tickers = {stock['Ticker_Name'] for stock in user_watchlist}

    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    return render_template('stocks.html', stocks=stocks_data, holdings = user_holdings, watchlist = user_watchlist, money=money)

@app.route('/holdings')
@login_required
def holdings():
    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    user_holdings = get_user_holdings(user['User_id']) if user else []
    return render_template('holdings.html', holdings=user_holdings, money=money)
    
@app.route('/watchlist')
@login_required
def watchlist():
    user_watchlist = get_user_watchlist(main_username)    
    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    return render_template('watchlist.html', watchlist=user_watchlist, money=money)

@app.route('/add_to_holdings', methods=['POST'])
@login_required
def add_to_holdings():
    user = get_user_by_username(main_username)
    if not user:
        return redirect(url_for('login'))
    user_id = user['User_id']
    ticker = request.form.get('Ticker_Name')
    quantity = int(request.form.get('quantity'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    price = 0
     # Get the current price for this ticker
    cursor.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,))
    row = cursor.fetchone()
    if row is not None:
        price = row[0]
    cursor.execute("INSERT INTO holdings (User_id, Ticker_Name, Price, quantity, Date_bought, Price_bought) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)", (user_id, ticker, price, quantity, price))
    
    # Update user's money
    total_cost = price * quantity
    cursor.execute("UPDATE users SET Money = Money - ? WHERE User_id = ?", (total_cost, user_id))
    
    # Add transaction record
    add_transaction(user_id, ticker, quantity, price, 'Buy', conn)
    
    conn.commit()
    conn.close()
    return redirect(url_for('stocks'))

@app.route('/is_stock_in_watchlist/<stock_symbol>')
@token_required
def is_stock_in_watchlist(stock_symbol):
    user = get_user_by_username(main_username)
    if user and is_in_watchlist(user['User_id'], stock_symbol):
        return jsonify({"isInWatchlist": True})
    return jsonify({"isInWatchlist": False})

@app.route('/toggle_watchlist/<ticker>', methods=['POST'])
@login_required
def toggle_watchlist(ticker):
    user_id = get_user_by_username(main_username)['User_id']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    price = 0
    # Get the current price for this ticker
    cursor.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,))
    row = cursor.fetchone()
    # Check if the stock is already in the watchlist
    cursor.execute("SELECT 1 FROM watchlist WHERE User_id = ? AND Ticker_Name = ?", (user_id, ticker))
    if row:
        price = row[0]
    else:
        conn.close()
        return abort(400, description="Stock not found")


    exists = cursor.fetchone()

    if exists:
        # Remove from watchlist
        cursor.execute("DELETE FROM watchlist WHERE User_id = ? AND Ticker_Name = ?", (user_id, ticker))
    else:
        # Add to watchlist
        cursor.execute("INSERT INTO watchlist (User_id, Ticker_Name, Price) VALUES (?, ?, ?)", (user_id, ticker, price))

    conn.commit()
    conn.close()
    return redirect(url_for('stocks'))

@app.route('/sell_stock', methods=['POST'])
def sell_stock():
    user = get_user_by_username(main_username)
    if not user:
        return redirect(url_for('login'))
    user_id = user['User_id']
    ticker = request.form.get('Ticker_Name')

    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # 1 relevant rows
        cursor.execute("SELECT rowid, quantity FROM holdings WHERE User_id = ? AND Ticker_Name = ?", (user_id, ticker))
        holdings_rows = cursor.fetchall()

        if not holdings_rows:
            return abort(400, description="Holding not found for this user and ticker")

        #2. Check if there is a row with a positive quantity
        positive_row_found = False
        for row in holdings_rows:
            if row[1] > 0:
                positive_row_found = True
                break

        # 3. Prioritize positive Quantities
        sold = False
        for row in holdings_rows:
            rowid, quantity = row
            if quantity > 0:
                new_quantity = quantity - 1
                if new_quantity == 0:
                    # Delete the row
                    cursor.execute("DELETE FROM holdings WHERE rowid = ?", (rowid,))
                else:
                    # Update the row
                    cursor.execute("UPDATE holdings SET quantity = ? WHERE rowid = ?", (new_quantity, rowid))
                sold = True
                break  # Only sell one at a time

        if not sold:
            return abort(400, description="Cannot sell stock. No stock to sell")

        # Get the current price for the sell transaction to update the user's money
        cursor.execute("SELECT Price FROM stocks WHERE Ticker_Name = ?", (ticker,))
        row = cursor.fetchone()
        price = row[0] if row else 0

        # Add transaction record for sell
        add_transaction(user_id, ticker, 1, price, 'Sell', conn)  # Selling one share at a time

        # Update user's money
        cursor.execute("UPDATE users SET Money = Money + ? WHERE User_id = ?", (price, user_id))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error selling stock: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return redirect(url_for('holdings'))


def add_transaction(user_id, ticker_name, quantity, price, transaction_type, conn):
    cursor = conn.cursor()
    
    # Insert transaction record
    cursor.execute("""
        INSERT INTO transactions (User_ID, Ticker_Name, Quantity, Price, Transaction_Type, Transaction_Date)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, ticker_name, float(quantity), float(price), transaction_type))
    
    # Commit the transaction insertion
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
        

@app.route('/transactions')
@login_required
def transactions():
    user = get_user_by_username(main_username)
    user_id = user['User_id']
    money = user['Money'] if user else 0
    try:
        user_transactions = get_transactions(user_id)
        print(f"Fetched transactions: {user_transactions}")
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        user_transactions = []
    return render_template('transactions.html', transactions=user_transactions, money=money)





if __name__ == "__main__":
    print("Doing initial stock data fetch...")
    get_stock_data_batch()

    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

