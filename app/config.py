import os
import configparser


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    APP_DEFAULT_LANG = os.environ.get("APP_DEFAULT_LANG", "jp")
    DB_INI_PATH = os.environ.get("DB_INI_PATH", os.path.join(os.getcwd(), "env.ini"))

    @classmethod
    def load_db_uri(cls) -> str:
        """
        Reads DB settings from env.ini and builds a DB URI string.
        Note: This skeleton does NOT connect DB yet. You will use this
        URI when you integrate SQLAlchemy.
        """
        cp = configparser.ConfigParser()
        if not os.path.exists(cls.DB_INI_PATH):
            raise FileNotFoundError(f"env.ini not found: {cls.DB_INI_PATH}")

        cp.read(cls.DB_INI_PATH, encoding="utf-8")
        if "database" not in cp:
            raise KeyError("Missing [database] section in env.ini")

        db = cp["database"]
        driver = db.get("driver", "").strip()
        host = db.get("host", "").strip()
        port = db.get("port", "").strip()
        name = db.get("name", "").strip()
        user = db.get("user", "").strip()
        password = db.get("password", "").strip()
        charset = (db.get("charset", "") or "utf8mb4").strip()

        return f"{driver}://{user}:{password}@{host}:{port}/{name}?charset={charset}"
