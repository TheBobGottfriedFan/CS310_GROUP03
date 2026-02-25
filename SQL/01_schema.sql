USE patient_portal;
SET FOREIGN_KEY_CHECKS = 0;

-- Drop children first
DROP TABLE IF EXISTS insurance_documents;
DROP TABLE IF EXISTS insurance_policies;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS user_security_qa;
DROP TABLE IF EXISTS security_questions;
DROP TABLE IF EXISTS identity_verifications;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS data_sharing_prefs;
DROP TABLE IF EXISTS privacy_settings;
DROP TABLE IF EXISTS auto_refill_settings;
DROP TABLE IF EXISTS refill_requests;
DROP TABLE IF EXISTS pharmacy_patient;
DROP TABLE IF EXISTS pharmacies;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS message_threads;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS countered_visits;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS availability_slots;
DROP TABLE IF EXISTS allergies;
DROP TABLE IF EXISTS medical_history;
DROP TABLE IF EXISTS medical_records;
DROP TABLE IF EXISTS health_info;
DROP TABLE IF EXISTS profiles;
DROP TABLE IF EXISTS reset_password_tokens;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS login_history;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
SET FOREIGN_KEY_CHECKS = 1;

-- ROLES
CREATE TABLE roles (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ROLE PERMISSIONS
CREATE TABLE permissions (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE role_permissions (
 role_id INT NOT NULL,
 permission_id INT NOT NULL,
 PRIMARY KEY (role_id, permission_id),
 FOREIGN KEY (role_id) REFERENCES roles(id)
  ON DELETE CASCADE,
 FOREIGN KEY (permission_id) REFERENCES permissions(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_perm ON role_permissions(permission_id);

-- users
CREATE TABLE users (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 role_id INT NOT NULL,
 email VARCHAR(255) NOT NULL UNIQUE,
 password_hash VARCHAR(100) NOT NULL,
 first_name VARCHAR(100),
 last_name VARCHAR(100),
 phone VARCHAR(30),
 is_active BOOLEAN DEFAULT TRUE,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (role_id) REFERENCES roles(id)
  ON UPDATE CASCADE
  ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_user_role ON users(role_id);

-- Login History
CREATE TABLE login_history (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 ip_address VARCHAR(64),
 user_agent VARCHAR(255),
 success BOOLEAN NOT NULL DEFAULT TRUE,
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_login_user ON login_history(user_id);

-- Session Timeout Handling
CREATE TABLE sessions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 session_token VARCHAR(255) NOT NULL UNIQUE,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 expires_at DATETIME NOT NULL,
 revoked_at DATETIME NULL,
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_session_user ON sessions(user_id);

-- Tokens for Resetting Passwords
CREATE TABLE reset_password_tokens (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 token VARCHAR(255) NOT NULL UNIQUE,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 expires_at DATETIME NOT NULL,
 used_at DATETIME NULL,
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Profile
CREATE TABLE profiles (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL UNIQUE,
 address1 VARCHAR(255),
 address2 VARCHAR(255),
 city VARCHAR(120),
 state VARCHAR(60),
 zip VARCHAR(20),
 profile_picture_url VARCHAR(500),
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- HEALTHINFO
CREATE TABLE health_info (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL UNIQUE,
 height_cm DECIMAL(6,2),
 weight_kg DECIMAL(6,2),
 blood_type VARCHAR(5),
 conditions TEXT,
 medications TEXT,
 emergency_contact_name VARCHAR(200),
 emergency_contact_phone VARCHAR(30),
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Medical Records
CREATE TABLE medical_records (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 created_by BIGINT NULL,
 record_type VARCHAR(80),
 record_data TEXT,
 recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (created_by) REFERENCES users(id)
  ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE medical_history (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 updated_by BIGINT NULL,
 history_data TEXT,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (updated_by) REFERENCES users(id)
  ON DELETE SET NULL
) ENGINE=InnoDB;

-- Allergies
CREATE TABLE allergies (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 substance VARCHAR(200) NOT NULL,
 reaction VARCHAR(200),
 severity ENUM('mild','moderate','severe'),
 notes TEXT,
 recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_allergy_patient ON allergies(patient_id);

-- Provider
CREATE TABLE availability_slots (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 provider_id BIGINT NOT NULL,
 start_time DATETIME NOT NULL,
 end_time DATETIME NOT NULL,
 status ENUM('open','booked','blocked') DEFAULT 'open',
 FOREIGN KEY (provider_id) REFERENCES users(id)
  ON DELETE CASCADE,
 CHECK (end_time > start_time)
) ENGINE=InnoDB;

CREATE INDEX idx_avail_provider ON availability_slots(provider_id);
CREATE INDEX idx_avail_time ON availability_slots(start_time, end_time);

-- TRIGGER FINGER
CREATE INDEX idx_avail_provider_time_status
 ON availability_slots(provider_id, start_time, end_time, status);

-- Appointments
CREATE TABLE appointments (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 provider_id BIGINT NOT NULL,
-- One Slot
 slot_id BIGINT NOT NULL UNIQUE,
 parent_appointment_id BIGINT NULL,
 appointment_type ENUM('new','follow_up','visit') DEFAULT 'new',
 start_time DATETIME NOT NULL,
 end_time DATETIME NOT NULL,
 status ENUM('requested','scheduled','cancelled','completed') DEFAULT 'requested',
 reason VARCHAR(255),
 cancel_note VARCHAR(255),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (provider_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (slot_id) REFERENCES availability_slots(id)
  ON DELETE RESTRICT,
 FOREIGN KEY (parent_appointment_id) REFERENCES appointments(id)
  ON DELETE SET NULL,
 CHECK (end_time > start_time)
) ENGINE=InnoDB;
CREATE INDEX idx_appt_patient ON appointments(patient_id);
CREATE INDEX idx_appt_provider ON appointments(provider_id);
CREATE INDEX idx_appt_start ON appointments(start_time);
CREATE INDEX idx_appt_slot ON appointments(slot_id);
CREATE INDEX idx_appt_provider_time_status
 ON appointments(provider_id, start_time, end_time, status);
CREATE INDEX idx_appt_patient_time_status
 ON appointments(patient_id, start_time, end_time, status);

-- VISIT ENCOUNTERS
CREATE TABLE countered_visits (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 appointment_id BIGINT NOT NULL UNIQUE,
 checked_in_at DATETIME NULL,
 completed_at DATETIME NULL,
 notes TEXT,
 FOREIGN KEY (appointment_id) REFERENCES appointments(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- THREADS
CREATE TABLE message_threads (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 subject VARCHAR(255) NOT NULL,
 created_by BIGINT NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (created_by) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Messages
CREATE TABLE messages (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 thread_id BIGINT NULL,
 sender_id BIGINT NOT NULL,
 receiver_id BIGINT NOT NULL,
 body TEXT NOT NULL,
 sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 is_read BOOLEAN DEFAULT FALSE,
 read_at DATETIME NULL,
 FOREIGN KEY (thread_id) REFERENCES message_threads(id)
  ON DELETE SET NULL,
 FOREIGN KEY (sender_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (receiver_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_msg_receiver ON messages(receiver_id);
CREATE INDEX idx_msg_thread ON messages(thread_id);

-- Notifications
CREATE TABLE notifications (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 category ENUM('system','message','appointment','medication') DEFAULT 'system',
 message VARCHAR(255),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 is_read BOOLEAN DEFAULT FALSE,
 read_at DATETIME NULL,
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_notif_user ON notifications(user_id);

-- Pharmacy
CREATE TABLE pharmacies (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(255) NOT NULL,
 phone VARCHAR(30),
 address VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE pharmacy_patient (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 pharmacy_id BIGINT NOT NULL,
 is_preferred BOOLEAN DEFAULT FALSE,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Prescribe Drugs
CREATE TABLE prescriptions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 medication_name VARCHAR(200) NOT NULL,
 dosage VARCHAR(500),
 frequency VARCHAR(100),
 start_date DATE,
 end_date DATE,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_rx_patient ON prescriptions(patient_id);

-- Refills
CREATE TABLE refill_requests (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 prescription_id BIGINT NOT NULL,
 requested_by BIGINT NOT NULL,
 note VARCHAR(255),
 status ENUM('requested','approved','denied','cancelled') DEFAULT 'requested',
 requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 cancelled_at DATETIME NULL,
 cancel_reason VARCHAR(255),
 FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
  ON DELETE CASCADE,
 FOREIGN KEY (requested_by) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_refill_prescription ON refill_requests(prescription_id);
CREATE TABLE auto_refill_settings (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 prescription_id BIGINT NOT NULL UNIQUE,
 enabled BOOLEAN DEFAULT FALSE,
 interval_days INT,
 next_run_at DATETIME NULL,
 FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Preferences for Data and Privacy
CREATE TABLE privacy_settings (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL UNIQUE,
 allow_email BOOLEAN DEFAULT TRUE,
 allow_sms BOOLEAN DEFAULT FALSE,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE data_sharing_prefs (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL UNIQUE,
 share_with_providers BOOLEAN DEFAULT TRUE,
 share_for_research BOOLEAN DEFAULT FALSE,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tickets for Support
CREATE TABLE support_tickets (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 created_by BIGINT NOT NULL,
 assigned_to BIGINT NULL,
 subject VARCHAR(255) NOT NULL,
 description TEXT,
 status ENUM('open','in_progress','closed') DEFAULT 'open',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 closed_at DATETIME NULL,
 close_note VARCHAR(255),
 FOREIGN KEY (created_by) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (assigned_to) REFERENCES users(id)
  ON DELETE SET NULL
) ENGINE=InnoDB;

-- Security Questions, AMA
CREATE TABLE security_questions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 question_text VARCHAR(255) NOT NULL,
 is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE user_security_qa (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 question_id BIGINT NOT NULL,
 answer_hash VARCHAR(255) NOT NULL,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 UNIQUE KEY uq_user_question (user_id, question_id),
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE,
 FOREIGN KEY (question_id) REFERENCES security_questions(id)
  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- IDV
CREATE TABLE identity_verifications (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 action_type VARCHAR(80) NOT NULL,
 status ENUM('started','success','failure') DEFAULT 'started',
 requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 verified_at DATETIME NULL,
 failure_reason VARCHAR(255),
 FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

-- Insurance
CREATE TABLE insurance_policies (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 patient_id BIGINT NOT NULL,
 payer_name VARCHAR(255) NOT NULL,
 plan_name VARCHAR(255) NULL,
 member_id VARCHAR(80) NOT NULL,
 group_number VARCHAR(80) NULL,
 relationship_to_patient ENUM('self','spouse','child','other') DEFAULT 'self',
 policyholder_name VARCHAR(255) NULL,
 policyholder_dob DATE NULL,
 effective_start DATE NULL,
 effective_end DATE NULL,
 phone VARCHAR(30) NULL,
 address VARCHAR(255) NULL,
 is_primary BOOLEAN DEFAULT TRUE, 
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (patient_id) REFERENCES users(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX idx_ins_patient ON insurance_policies(patient_id);
CREATE INDEX idx_ins_member  ON insurance_policies(member_id);

CREATE TABLE insurance_documents (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 policy_id BIGINT NOT NULL,
 doc_type ENUM('front_card','back_card','other') DEFAULT 'front_card', -- Information.
 file_url VARCHAR(500) NOT NULL, -- This is the document file.
 uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (policy_id) REFERENCES insurance_policies(id)
  ON DELETE CASCADE
) ENGINE=InnoDB;

