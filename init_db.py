import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('PRAGMA foreign_keys = ON;')
cursor = conn.cursor()

for sql_file in ['database/csc-310-project_holdings.sql', 
                'database/csc-310-project_watchlist.sql', 
                'database/csc-310-project_stocks.sql', 
                'database/csc-310-project_transactions.sql', 
                'database/csc-310-project_users.sql']:
    with open(sql_file, 'r') as f:
        cursor.executescript(f.read())

conn.commit()
conn.close()