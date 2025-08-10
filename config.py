import os
from dotenv import load_dotenv
import pymysql

# Install PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql://work_user:work_pass123@mysql/work_management')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'pool_timeout': 20,
        'connect_args': {
            'charset': 'utf8mb4'
        }
    }
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this')
    
    # File Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'production')