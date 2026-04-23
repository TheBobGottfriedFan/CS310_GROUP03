# Patient Portal System
 
### Authors
- **Bob** - Project Lead, Backend, patientportalsystem folder, HTML/CSS frontend, authentication_service.py, backend.py, db.py, forms.py, models.py, notification_service.py, permissions.py, rbac.py, urls.py, views.py, Database Code, SQL schema, seed data, triggers, README
- **Jeffrey** - UI/UX, HTML/CSS frontend, Sign-in/Logout, urls.py, .env configuration, README
- **Kendra** - Frontend contributions, Contact Doctors Code, testing, README
- **Michael** - Testing (PPTC-012 through PPTC-016), appointment cancellation, delete account, README
- **Kirubel** - Testing (PPTC-007 through PPTC-011), unit test seeds

### Link
https://github.com/TheBobGottfriedFan/CS310_GROUP03

## Overview
The GROUP03 Patient Portal is a Django + MySQL web application designed to support healthcare portal functionality. It includes custom SQL-backend authentication, Role-Based Access Control (RBAC), bcrypt password hashing, session validation, notifications, and several patient workflows. The project uses Django for routing and page templates, and interacts with MySQL via mysql.connector for application logic.
 
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
Either do:
 
a. Download the Repository as a zip file and extract
 
b. git clone:
```bash
git clone https://github.com/TheBobGottfriedFan/CS310_GROUP03.git
cd CS310_GROUP03
```
 
c. Or clone the implementation branch directly:
```bash
git clone https://github.com/TheBobGottfriedFan/CS310_GROUP03/tree/TheBobGottfriedFan-Implementation-1
cd <project_folder>
```
 
> **Note:** `<project_folder>` is the path to where you want to install the project.
> Remove `/tree/TheBobGottfriedFan-Implementation-1` once it has been merged to main.
 
### 2. Create a Virtual Environment
 
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
 
Mac / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
 
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

or

```bash
pip install django mysql-connector-python bcrypt python-dotenv
```

### 4. Create `.env` File
#### Windows
In the root directory, create a file named `.env` and add:
 
```
DJANGO_SECRET_KEY=your_secret_key_here
DB_NAME=patient_portal
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

#### Mac
```
touch .env
nano .env
```
then paste:
```
DJANGO_SECRET_KEY=your_secret_key_here
DB_NAME=patient_portal
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```
 
> **Note:** See requirements.txt for instructions on generating a DJANGO_SECRET_KEY.
> A `.env` has been provided for the testing environment.
> **Also:** Update to your MySQL password in portal/db.py [ password="Mookie123*" ]
 
### 5. Set Up MySQL Database
#### Windows
 
**a. MySQL Workbench (Easier)**
 
Open MySQL Workbench and run the SQL files in the `SQL/` folder in order:
```
00_create_db.sql
01_schema.sql
02_seed.sql
03_triggers.sql
```
 
**b. Terminal (Harder)**
 
```bash
mysql -u your_mysql_user -p patient_portal < schema.sql
mysql -u your_mysql_user -p patient_portal < seed.sql
```
 
> Replace `your_mysql_user` with your MySQL username.


#### Mac
```
mysql -u root -p < SQL/00_create_db.sql
mysql -u root -p patient_portal < SQL/01_schema.sql
mysql -u root -p patient_portal < SQL/02_seed.sql
mysql -u root -p patient_portal < SQL/03_triggers.sql
```

### 6. Run Django Migrations
#### Windows
```bash
python manage.py migrate
```

#### Mac
```bash
python3 manage.py migrate
```

### 7. Start the Server
#### Windows
```bash
python manage.py runserver
```

#### Mac
```bash
python3 manage.py runserver
```

### 8. Access the Application
 
Open your browser to:
 
- Signup: http://127.0.0.1:8000/signup/
- Login: http://127.0.0.1:8000/login/
 
> **Note:** This is an HTTP testing environment, not HTTPS. The developers of this application are unpaid.
 
### 9. Signup / Login
 
You can either:
 
a. Login via a seeded user from the SQL seed files
 
b. Create a new patient account on the signup page
 
---

a. Login via a seeded user in the seeded SQL files

b. create a new patient account in the sign-up page


### Kindly Note
The User MUST manually set their role permissions (either in the admin panel or in the database) if they wish to become A doctor or an admin.
