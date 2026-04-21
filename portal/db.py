# portal/db.py

import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Starbucks2022!",
        database="patient_portal",
        port=3306,
        autocommit=True,
    )