-- Table structure for table `users`

DROP TABLE IF EXISTS users;

CREATE TABLE users (
  User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
  Username TEXT UNIQUE NOT NULL,
  Email TEXT UNIQUE NOT NULL,
  Password TEXT NOT NULL,
  Money DECIMAL(15,2) DEFAULT 0.0,
  Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
