# database.py
import sqlite3

DB_PATH = "numeron.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ データベースを初期化しました")

def get_user_by_username(username):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return user

def create_user(username, hashed_password):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_record(user_id, game, difficulty, attempts):
    conn = get_db()
    conn.execute(
        "INSERT INTO records (user_id, game, difficulty, attempts) VALUES (?, ?, ?, ?)",
        (user_id, game, difficulty, attempts)
    )
    conn.commit()
    conn.close()

def get_best_records_all(user_id):
    conn = get_db()
    records = conn.execute("""
        SELECT game, difficulty, MIN(attempts) as best, COUNT(*) as plays
        FROM records
        WHERE user_id = ?
        GROUP BY game, difficulty
        ORDER BY game, attempts ASC
    """, (user_id,)).fetchall()
    conn.close()
    return records

def get_ranking_all():
    conn = get_db()
    rankings = {}
    games = ["numeron", "countdown"]
    difficulties = {
        "numeron": ["easy", "normal", "hard"],
        "countdown": ["easy", "normal", "hard"]
    }
    for game in games:
        rankings[game] = {}
        for diff in difficulties[game]:
            rows = conn.execute("""
                SELECT u.username, MIN(r.attempts) as best, COUNT(*) as plays
                FROM records r
                JOIN users u ON r.user_id = u.id
                WHERE r.game = ? AND r.difficulty = ?
                GROUP BY r.user_id
                ORDER BY best ASC
                LIMIT 10
            """, (game, diff)).fetchall()
            rankings[game][diff] = rows
    conn.close()
    return rankings