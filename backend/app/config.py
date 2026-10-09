import os


class Settings:
    APP_NAME = os.getenv("APP_NAME", "CallShield AI")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    API_PREFIX = os.getenv("API_PREFIX", "/api")


settings = Settings()
