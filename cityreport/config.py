import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # SQLite by default — zero setup, works out of the box.
    # To use MySQL/XAMPP instead, set DATABASE_URL in .env, e.g.:
    #   DATABASE_URL=mysql+pymysql://root:@localhost:3306/cityreport
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "cityreport")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'cityreport.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
    MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

    # City default map center (Douala, Cameroon)
    DEFAULT_LAT = float(os.environ.get("DEFAULT_LAT", 4.0511))
    DEFAULT_LNG = float(os.environ.get("DEFAULT_LNG", 9.7679))

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@cityreport.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")
