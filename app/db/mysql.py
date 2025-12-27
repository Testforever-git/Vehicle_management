# app/db/mysql.py
import os
import configparser
import mysql.connector
from mysql.connector import pooling

_POOL = None

def _load_db_cfg():
    ini_path = os.environ.get("DB_INI_PATH", os.path.join(os.getcwd(), "env.ini"))
    cp = configparser.ConfigParser()
    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"env.ini not found: {ini_path}")

    cp.read(ini_path, encoding="utf-8")
    if "database" not in cp:
        raise KeyError("Missing [database] section in env.ini")

    db = cp["database"]
    return {
        "host": db.get("host", "").strip(),
        "port": int((db.get("port", "") or "3306").strip()),
        "database": db.get("name", "").strip(),
        "user": db.get("user", "").strip(),
        "password": db.get("password", "").strip(),
        "charset": (db.get("charset", "") or "utf8mb4").strip(),
    }

def init_pool():
    global _POOL
    if _POOL is not None:
        return _POOL

    cfg = _load_db_cfg()
    # mysql-connector 使用 connection pool
    _POOL = pooling.MySQLConnectionPool(
        pool_name="ac_pool",
        pool_size=5,
        pool_reset_session=True,
        **cfg,
    )
    return _POOL

def get_conn():
    pool = init_pool()
    return pool.get_connection()

def fetch_all(sql: str, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        conn.close()

def fetch_one(sql: str, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchone()
    finally:
        conn.close()

def execute(sql: str, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
