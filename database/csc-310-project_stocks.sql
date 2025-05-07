-- Table structure for table `stocks`

DROP TABLE IF EXISTS stocks;

CREATE TABLE stocks (
  Ticker_Name TEXT NOT NULL,
  Full_Name TEXT NOT NULL,
  Price DECIMAL(10, 2) NOT NULL,
  Sector TEXT DEFAULT NULL,
  PRIMARY KEY (Ticker_Name)
);

-- Dumping data for table `stocks'
