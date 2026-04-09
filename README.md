# Patient Portal System
 
### Authors
- **Bob** - Project Lead, Backend, patientportalsystem folder, authentication_service.py, backend.py, db.py, forms.py, models.py, notification_service.py, permissions.py, rbac.py, urls.py, views.py
- **Colton** - Database Code, SQL schema, seed data, triggers
- **Jeffrey** - UI/UX, HTML/CSS frontend, Sign-in/Logout, urls.py, .env configuration, README
- **Kendra** - Frontend contributions, testing
- **Kirubel** - Testing (PPTC-007 through PPTC-011)
- **Michael** - Testing (PPTC-012 through PPTC-016), appointment cancellation, delete account
- **Keshon** - Contributions
 
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
 
## Implemented Features
 
### Authentication & Session
- Patient login with bcrypt password hashing
- Patient signup (duplicate email rejected, required fields validated)
- Logout with session termination
- Session timeout with redirect to login
- Unauthenticated access redirects to login (@require_login decorator)
- Sensitive action identity verification
 
### Patient Dashboard
- Dashboard summary with data aggregation (appointments, messages, notifications, system status)
 
### Profile & Account
- View and update contact information
- View and update health information
- View and manage security questions
- Update password
- Delete account
 
### Appointments
- Request an appointment
- Cancel an appointment
- View appointment details (access controlled per patient)
- Filter appointments by date range
- Receive appointment reminders
 
### Messaging
- Send message to staff
- View message details
 
### Medical & Health
- View medical history
- Add and edit patient allergies
- Enter patient vitals
 
### Prescriptions
- Prescription search
- Request prescription refill
 
### Billing & Pharmacy
- View billing information
- Change patient pharmacy
 
### Privacy & Data
- View privacy settings
- Review data sharing preferences
 
### Notifications
- Mark notification as read
- Mark all notifications as read
- Receive appointment reminders
 
### Access Control
- Role-Based Access Control (RBAC) — patients cannot access staff/doctor routes
- Appointment detail access control — patients can only view their own appointments
 
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
 
### 4. Create `.env` File
In the root directory, create a file named `.env` and add:
 
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
 
### 5. Set Up MySQL Database
 
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
 
### 6. Run Django Migrations
```bash
python manage.py migrate
```
 
### 7. Start the Server
```bash
python manage.py runserver
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
 
# Trademark
Durgasoft™

a. Login via a seeded user in the seeded SQL files

b. create a new patient account in the sign-up page


# Trademark
Durgasoft™
