-- Table structure for table `holdings`

DROP TABLE IF EXISTS holdings;

CREATE TABLE holdings (
  Holdings_ID INTEGER PRIMARY KEY AUTOINCREMENT,
  User_ID INTEGER NOT NULL,
  Date_bought TIMESTAMP NOT NULL,
  Price_bought REAL NOT NULL,
  Price DECIMAL(10, 2) NOT NULL,
  Quantity DECIMAL(15, 4) NOT NULL,
  Ticker_Name TEXT,
  FOREIGN KEY (User_ID) REFERENCES users (User_ID),
  FOREIGN KEY (Ticker_Name) REFERENCES stocks (Ticker_Name)
);

-- Ensure foreign keys are enabled in SQLite
PRAGMA foreign_keys = ON;

-- Example insert statement (adjust as necessary)
-- INSERT INTO holdings (User_ID, Date_bought, Price_bought, Price, Quantity, Ticker_Name)
-- VALUES (1, '2025-04-01 10:00:00', 100.50, 120.75, 10, 'AAPL');
