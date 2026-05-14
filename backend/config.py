import os
from dotenv import load_dotenv
load_dotenv()
class Config:
        DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "localhost"
        DB_PORT = int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or 3306)
        DB_USER = os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root"
        DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or ""
        DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "bbms_se"
        DEBUG = os.getenv("DEBUG", "False") == "True"