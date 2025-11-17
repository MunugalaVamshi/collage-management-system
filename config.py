import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
    # URL-encoded password (the @ becomes %40)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql://root:11d41F@0031@localhost/CMS'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
