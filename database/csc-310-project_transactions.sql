-- Table structure for table `transactions`

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
  Transaction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
  User_ID INTEGER NOT NULL,
  Ticker_Name TEXT NOT NULL,
  Quantity DECIMAL(15,4) NOT NULL,
  Price DECIMAL(10,2) NOT NULL,
  Transaction_Type TEXT CHECK(Transaction_Type IN ('Buy', 'Sell')) NOT NULL,
  Transaction_Date TIMESTAMP DEFAULT NULL,
  FOREIGN KEY (User_ID) REFERENCES users (user_id),
  FOREIGN KEY (Ticker_Name) REFERENCES stocks (ticker_name)
);

-- Dumping data for table `transactions`
-- You can insert the data here after adjusting for SQLite
