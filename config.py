import os
from dotenv import load_dotenv

load_dotenv()

def env(name, default=None, strip=True):
    value = os.getenv(name, default)
    if isinstance(value, str) and strip:
        return value.strip()
    return value

class Config:
    ENVIRONMENT = env('FLASK_ENV', env('APP_ENV', 'production')).lower()
    IS_PRODUCTION = ENVIRONMENT == 'production'

    SECRET_KEY = env('SECRET_KEY')
    if IS_PRODUCTION and not SECRET_KEY:
        raise RuntimeError('SECRET_KEY must be set in production.')
    if not SECRET_KEY:
        SECRET_KEY = 'dev-only-change-me'

    DB_USER = env('DB_USER', 'root')
    DB_PASSWORD = env('DB_PASSWORD', '')
    DB_HOST = env('DB_HOST', 'localhost')
    DB_NAME = env('DB_NAME', 'jj_softaroma')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images')

    DEBUG = env('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes') and not IS_PRODUCTION

    WTF_CSRF_ENABLED = env('WTF_CSRF_ENABLED', 'true').lower() not in ('0', 'false', 'no')
    WTF_CSRF_TIME_LIMIT = int(env('WTF_CSRF_TIME_LIMIT', '3600'))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = IS_PRODUCTION
