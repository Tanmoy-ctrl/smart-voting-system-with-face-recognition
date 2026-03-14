import sqlite3

# Path for your database
DB_PATH = "voting.db"  # Put this in the same folder as app.py

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ---------- Admin table ----------
c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# Default admin
c.execute("INSERT OR IGNORE INTO admin(username,password) VALUES (?,?)", ("admin","admin123"))

# ---------- Users table ----------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    aadhaar TEXT UNIQUE,
    face_encoding BLOB,
    has_voted INTEGER DEFAULT 0
)
""")

# ---------- Candidates table ----------
c.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    party TEXT
)
""")

# ---------- Votes table ----------
c.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    candidate_id INTEGER
)
""")

conn.commit()
conn.close()
print("voting.db has been created and initialized successfully!")
print("Default admin -> username:admin, password:admin123")
