import os
import psycopg2
import psycopg2.extras

def get_db():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL", ""),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            game TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_user_by_username(username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username = %s", (username,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(username, hashed_password):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.errors.UniqueViolation:
        return False

def save_record(user_id, game, difficulty, attempts):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO records (user_id, game, difficulty, attempts) VALUES (%s, %s, %s, %s)",
        (user_id, game, difficulty, attempts)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_best_records_all(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            game,
            difficulty,
            CASE
                WHEN game = '2048' THEN MAX(attempts)
                ELSE MIN(attempts)
            END as best,
            COUNT(*) as plays
        FROM records
        WHERE user_id = %s
        GROUP BY game, difficulty
        ORDER BY
            CASE game
                WHEN 'countdown' THEN 1
                WHEN 'numeron' THEN 2
                WHEN '2048' THEN 3
                ELSE 4
            END,
            CASE difficulty
                WHEN 'easy' THEN 1
                WHEN 'normal' THEN 2
                WHEN 'hard' THEN 3
                ELSE 4
            END
    """, (user_id,))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def get_ranking_all():
    conn = get_db()
    cur = conn.cursor()
    rankings = {}
    for game in ["numeron", "countdown", "2048"]:
        rankings[game] = {}
        for difficulty in ["easy", "normal", "hard"]:
            order = "DESC" if game == "2048" else "ASC"
            agg = "MAX" if game == "2048" else "MIN"
            cur.execute(f"""
                SELECT
                    u.username,
                    {agg}(r.attempts) as best,
                    COUNT(*) as plays
                FROM records r
                JOIN users u ON r.user_id = u.id
                WHERE r.game = %s AND r.difficulty = %s
                GROUP BY u.username
                ORDER BY best {order}
                LIMIT 10
            """, (game, difficulty))
            rankings[game][difficulty] = cur.fetchall()
    cur.close()
    conn.close()
    return rankings