import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bluprint.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'simple'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
    JWT_ALGORITHM = 'HS256'
    
    # Logging
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

config = {'development': Config, 'default': Config}