# portal/db.py

import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mookie123*",
        database="patient_portal",
        port=3306,
        autocommit=True,
    )