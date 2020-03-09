"""Default configuration

Use env var to override
"""
import os

ENV = os.getenv("FLASK_ENV")
DEBUG = ENV == "development"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", '').replace('\\n', '\n')
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", '').replace('\\n', '\n')

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
