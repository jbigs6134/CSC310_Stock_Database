import os, secrets, re, firebase_admin
from flask_apscheduler import APScheduler
from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from functools import wraps

# Custom modules
from helper_files.users import get_user_by_username, create_user, is_valid_email
from helper_files.holdings import get_user_holdings, add_to_holdings_db, sell_stock_db
from helper_files.watchlist import get_user_watchlist, toggle_watchlist_db, is_in_watchlist
from helper_files.transactions import get_transactions, add_transaction
from helper_files.stocks import get_stocks_from_db
from json_requests import get_stock_data_batch

app = Flask(__name__)

app.config['SCHEDULER_API_ENABLED'] = True
app.config['SESSION_COOKIE_NAME'] = 'session_cookie'
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = secrets.token_hex(16)
app.config['SESSION_PERMANENT'] = True
scheduler = APScheduler()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

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

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user_row = get_user_by_username(username)
        if user_row and check_password_hash(user_row[2], password):
            global main_username
            main_username = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'})
    return render_template('loginpage.html')

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
            main_username = username
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
    stocks_data = get_stocks_from_db()
    user = get_user_by_username(main_username)
    user_holdings = get_user_holdings(user['User_ID']) if user else []
    user_watchlist = get_user_watchlist(main_username)
    watchlist_tickers = {stock['Ticker_Name'] for stock in user_watchlist}
    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    return render_template('stocks.html', stocks=stocks_data, holdings=user_holdings, watchlist=user_watchlist, money=money)

@app.route('/holdings')
@login_required
def holdings():
    user = get_user_by_username(main_username)
    money = user['Money'] if user else 0
    user_holdings = get_user_holdings(user['User_ID']) if user else []
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
    add_to_holdings_db(request.form, user)
    return redirect(url_for('stocks'))

@app.route('/sell_stock', methods=['POST'])
@login_required
def sell_stock():
    user = get_user_by_username(main_username)
    if not user:
        return redirect(url_for('login'))
    ticker = request.form.get('Ticker_Name')
    sell_stock_db(user, ticker)
    return redirect(url_for('holdings'))

@app.route('/toggle_watchlist/<ticker>', methods=['POST'])
@login_required
def toggle_watchlist(ticker):
    user = get_user_by_username(main_username)
    if not user:
        return redirect(url_for('login'))
    toggle_watchlist_db(user['User_ID'], ticker)
    return redirect(url_for('stocks'))

@app.route('/is_stock_in_watchlist/<stock_symbol>')
@token_required
def is_stock_in_watchlist(stock_symbol):
    user = get_user_by_username(main_username)
    if not user:
        return jsonify({"isInWatchlist": False})
    if user and is_in_watchlist(user['User_ID'], stock_symbol):
        return jsonify({"isInWatchlist": True})
    return jsonify({"isInWatchlist": False})

@app.route('/transactions')
@login_required
def transactions():
    user = get_user_by_username(main_username)
    user_id = user['User_ID']
    money = user['Money'] if user else 0
    try:
        user_transactions = get_transactions(user_id)
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
