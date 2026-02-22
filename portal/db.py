# portal/db.py
import mysql.connector
from django.conf import settings

def get_connection():
    """
    Returns a new MySQL connection using Django DATABASES settings.
    Assumes you're using the standard Django DATABASES['default'] config.
    """
    db = settings.DATABASES["default"]

    return mysql.connector.connect(
        host=db.get("HOST", "localhost"),
        user=db.get("USER", ""),
        password=db.get("PASSWORD", ""),
        database=db.get("NAME", ""),
        port=int(db.get("PORT", 3306)),
        autocommit=True,
    )
