import os
import sqlite3
from django.conf import settings
from django.contrib.auth.hashers import make_password

def dict_factory(cursor, row):
    """Convert SQLite row tuple to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Retrieve raw SQLite connection with dictionary row factory enabled."""
    db_path = settings.DATABASES['default']['NAME']
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(query, params=None):
    """Execute generic SQL query and return fetched rows."""
    if params is None:
        params = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall()

def execute_read(query, params=None):
    """Execute read-only SQL query and return rows as dictionary list."""
    if params is None:
        params = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def execute_write(query, params=None):
    """Execute state-changing query (INSERT/UPDATE/DELETE) and return (lastrowid, rowcount)."""
    if params is None:
        params = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid, cursor.rowcount

def init_db():
    """Initialize the database if it does not already exist. This ensures a clean state for first run without overwriting existing data on subsequent imports."""
    schema_path = os.path.join(settings.BASE_DIR, 'sql', 'schema.sql')
    if not os.path.exists(schema_path):
        print(f"Schema file not found at: {schema_path}")
        return

    db_path = settings.DATABASES['default']['NAME']
    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # If DB file does not exist, create and populate schema
    if not os.path.exists(db_path):
        # Create empty DB file
        open(db_path, 'a').close()
        # Apply schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()
        # Seed admin user if not present
        admin_users = execute_read("SELECT * FROM users WHERE username = ?", ['admin'])
        if not admin_users:
            admin_pass = 'admin123'
            admin_hash = make_password(admin_pass)
            execute_write(
                "INSERT INTO users (username, password_hash, plain_password, role) VALUES (?, ?, ?, ?)",
                ['admin', admin_hash, admin_pass, 'Admin']
            )
            print("Seeded default admin user (admin / admin123).")
    else:
        # DB already exists; ensure admin user exists
        admin_users = execute_read("SELECT * FROM users WHERE username = ?", ['admin'])
        if not admin_users:
            admin_pass = 'admin123'
            admin_hash = make_password(admin_pass)
            execute_write(
                "INSERT INTO users (username, password_hash, plain_password, role) VALUES (?, ?, ?, ?)",
                ['admin', admin_hash, admin_pass, 'Admin']
            )
            print("Seeded default admin user (admin / admin123).")
