# Patient Portal System

### Authors
- Colton - Created the Database Code, patientportalsystem folder code, authentication_service.py, backend.py, db.py, forms.py, models.py, notification_service.py, permissions.py, rbac.py, urls.py, views.py. readme.md
- Jeffrey - HTML and urls.py Code


## Overview
The GROUP03 Patient Portal Portal is a Django + MySQL web application which is designed to support healthcare portal functionality. Includes custom SQL-backend authentication, Role-Based Access Control [RBAC], bcrypt password hashing, session validation, notifications, and several workflows. The project uses Django for routing and some page templates, as well interacts with MySQL with the mysql.connector for the application logic.

## Stack
- Python
- Django
- MySQL
- mysql-connector-python
- bcrypt
- python-dotenv
- HTML / CSS


# How to Install
### 1. Clone the Repository
git clone: https://github.com/TheBobGottfriedFan/CS310_GROUP03.git
cd CS310_GROUP03

### 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

### 3. Install Dependencies
pip install -r REQUIREMENTS.txt

### 4. Create `.env` File

In the root directory, create a file named `.env` and add:

DJANGO_SECRET_KEY=your_secret_key_here

DB_NAME=patient_portal
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

### 5. Set Up MySQL Database

Open MySQL Workbench and run the SQL files in the `SQL/` folder:

00_create_db.sql  
01_schema.sql  
02_seed.sql  
03_triggers.sql  

This is to create the database with the required tables and data.

### 6. Run Django Migrations (SQLite fallback)
python manage.py migrate

### 7. Start the Server
python manage.py runserver

### 8. Access the Application

http://127.0.0.1:8000/login/  
or
http://127.0.0.1:8000/signup/  


# Trademark
Durgasoft™
