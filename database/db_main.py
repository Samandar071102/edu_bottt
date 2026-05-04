import sqlite3

def db_start():
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    
    # Guruhlar jadvali
    cur.execute("""CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE)""")
    
    # Foydalanuvchilar jadvali
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        group_id INTEGER,
        score INTEGER DEFAULT 0,
        FOREIGN KEY(group_id) REFERENCES groups(id))""")

    # Mavzular jadvali
    cur.execute("""CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        group_id INTEGER,
        FOREIGN KEY(group_id) REFERENCES groups(id))""")

    # Fayllar jadvali
    cur.execute("""CREATE TABLE IF NOT EXISTS materials(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        file_id TEXT,
        file_type TEXT,
        FOREIGN KEY(subject_id) REFERENCES subjects(id))""")

    conn.commit()
    conn.close()

# Namuna uchun guruh qo'shish
def add_default_groups():
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = [('911-guruh',), ('912-guruh',), ('913-guruh',)]
    cur.executemany("INSERT OR IGNORE INTO groups (name) VALUES (?)", groups)
    conn.commit()
    conn.close()
