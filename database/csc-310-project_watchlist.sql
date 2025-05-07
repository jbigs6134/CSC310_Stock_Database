-- Table structure for table `watchlist`

DROP TABLE IF EXISTS watchlist;

CREATE TABLE watchlist (
  Watchlist_ID INTEGER PRIMARY KEY AUTOINCREMENT,
  User_ID INTEGER NOT NULL,
  Ticker_Name TEXT NOT NULL,
  Price DECIMAL(10,2) NOT NULL,
  Date_Added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  In_Holdings INTEGER DEFAULT 0,
  UNIQUE (User_ID, Ticker_Name),
  FOREIGN KEY (User_ID) REFERENCES users (User_ID) ON DELETE CASCADE,
  FOREIGN KEY (Ticker_Name) REFERENCES stocks (Ticker_Name) ON DELETE CASCADE
);

-- Insert data for table `watchlist`
-- Example:
-- INSERT INTO watchlist (User_ID, Ticker_Name, Price) VALUES (1, 'AAPL', 145.50);
