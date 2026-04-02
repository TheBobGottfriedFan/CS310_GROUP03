# Patient Portal System

### Authors
- Colton - Created the Database Code, patientportalsystem folder code, authentication_service.py, backend.py, db.py, forms.py, models.py, notification_service.py, permissions.py, rbac.py, urls.py, views.py
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
either do:
a. Download the Repository as a zip file

b. git clone: https://github.com/TheBobGottfriedFan/CS310_GROUP03.git
cd CS310_GROUP03

c. execute below:
''' bash
git clone https://github.com/TheBobGottfriedFan/CS310_GROUP03/tree/TheBobGottfriedFan-Implementation-1
cd <project_folder>

note: <project_folder> is the path to where you want to install the project

note: remove "/tree/TheBobGottfriedFan-Implementation-1" once it has been merged to main.

### 2. Create a Virtual Environment
Windows, Mac, and Linux:
python3 -m venv venv
source venv/bin/activate

### 3. Install Dependencies
Install the following packages found in requirements.txt 
You can also do: pip install -r REQUIREMENTS.txt

### 4. Create `.env` File
In the root directory, create a file named `.env` and add:
DJANGO_SECRET_KEY=your_secret_key_here
DB_NAME=patient_portal
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
note: DJANGO_SECRET_KEY set-up is explained in requirements.txt
note: a .env has been provided for the testing environments.

### 5. Set Up MySQL Database
a. MySQL workbench (Easier) - 

Open MySQL Workbench and run the SQL files in the `SQL/` folder:
00_create_db.sql  
01_schema.sql  
02_seed.sql  
03_triggers.sql  
This is to create the database with the required tables and data.

b. Terminal (Harder) -

Create a MySQL Database, then import the schema and seed SQL files
Example: CREATE DATABASE patient_portal;
Then import the SQL files with either MySQL workbench or command line:
mysql -u your_mysql_user -p patient_portal < schema.sql
mysql -u your_mysql_user -p patient_portal < seed.sql
note: the "your_mysql_user" is the user you had created in MySQL.

### 6. Run Django Migrations (SQLite fallback)
Execute the following command:
python manage.py migrate

### 7. Start the Server
Execute the following command:
python manage.py runserver

### 8. Access the Application
In your webbrowser, open up:
Signup: http://127.0.0.1:8000/signup/
Login: http://127.0.0.1:8000/login/
note: this is not a https environment, this is a http testing environment. The developers of this application are unpaid.

### 9. Signup/Login
Now, you can either:
a. Login via a seeded user in the seeded SQL files
b. create a new patient account in the sign-up page


# Trademark
Durgasoft™
