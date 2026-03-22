-- This File is rerunnable and is safe on the triggers
USE patient_portal;

-- Roles
INSERT IGNORE INTO roles (id, name) VALUES
(1, 'patient'),
(2, 'doctor'),
(3, 'nurse'),
(4, 'staff'),
(5, 'developer'),
(6, 'administrator');

-- Permissions (Perms)
INSERT IGNORE INTO permissions (id, name) VALUES
(1, 'access_patient_file'),
(2, 'update_patient_profile'),
(3, 'view_login_history'),
(4, 'view_messages'),
(5, 'request_appointment'),
(6, 'view_patient_profile'),
(7, 'manage_sessions'),
(8, 'manage_availability'),
(9, 'manage_appointments'),
(10, 'cancel_appointment'),
(11, 'create_medical_record'),
(12, 'update_medical_record'),
(13, 'send_messages'),
(14, 'manage_notifications'),
(15, 'view_prescriptions'),
(16, 'manage_prescriptions'),
(17, 'request_refill'),
(18, 'approve_refill'),
(19, 'view_insurance'),
(20, 'manage_insurance'),
(21, 'manage_users'),
(22, 'manage_roles_permissions');


-- = Role Permissions =

-- administrator gets EVERYTHING
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='administrator';

-- doctor permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='doctor' AND p.name IN (
 'access_patient_file',
 'view_patient_profile',
 'view_messages',
 'send_messages',
 'manage_availability',
 'request_appointment',
 'cancel_appointment',
 'create_medical_record',
 'update_medical_record',
 'view_prescriptions',
 'manage_prescriptions',
 'approve_refill',
 'view_insurance'
);

-- nurse permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='nurse' AND p.name IN (
 'access_patient_file',
 'view_patient_profile',
 'view_messages',
 'send_messages',
 'request_appointment',
 'cancel_appointment',
 'create_medical_record',
 'view_prescriptions',
 'approve_refill',
 'view_insurance'
);

-- staff permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='staff' AND p.name IN (
 'view_login_history',
 'view_messages',
 'send_messages',
 'manage_notifications',
 'manage_appointments',
 'cancel_appointment',
 'manage_insurance',
 'manage_users'
);

-- developer permissions [accessing tools]
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='developer' AND p.name IN (
 'view_login_history',
 'manage_roles_permissions',
 'manage_users'
);

-- patient permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name='patient' AND p.name IN (
 'view_patient_profile',
 'update_patient_profile',
 'request_appointment',
 'cancel_appointment',
 'view_messages',
 'send_messages',
 'view_prescriptions',
 'request_refill',
 'view_insurance',
 'manage_insurance'
);




-- Note: These are generated Seeds below [permission granted from teacher]. 

-- DA USERS
INSERT IGNORE INTO users (id, role_id, email, password_hash, first_name, last_name, phone)
VALUES
(1, 1, 'patient007@hrpp.com', 'hashed_password_here', 'John', 'Doe', NULL),
(2, 2, 'doctor1@hrpp.com', 'hashed_password_here', 'Alice', 'Smith', NULL),
(3, 4, 'staff1@hrpp.com', 'hashed_password_here', 'Robert', 'Brown', NULL),
(4, 6, 'administrator1@hrpp.com', 'hashed_password_here', 'System', 'Admin', NULL),
(5, 2, 'doctor2@hrpp.com', 'hashed_password_here', 'Evan', 'Lee', NULL),
(6, 1, 'patientdeuce@vgmail.com', 'hashed_password_here', 'Maya', 'Patel', NULL),
(7, 3, 'nurse1@hrpp.com', 'hashed_password_here', 'Nina', 'Reed', NULL),
(8, 5, 'developer@saget.com', 'hashed_password_here', 'Dev', 'User', NULL);

-- =========================
-- PROFILES
-- =========================
INSERT IGNORE INTO profiles (id, user_id, address1, address2, city, state, zip, profile_picture_url)
VALUES
(1, 1, '100 Main St', NULL, 'New York', 'NY', '10001', NULL),
(2, 2, '200 Clinic Rd', NULL, 'New York', 'NY', '10002', NULL),
(3, 6, '300 Oak Ave', 'Apt 2','Brooklyn', 'NY', '11201', NULL),
(4, 7, '400 Care Blvd', NULL, 'New York', 'NY', '10003', NULL);

-- =========================
-- HEALTH INFO
-- =========================
INSERT IGNORE INTO health_info
(id, patient_id, height_cm, weight_kg, blood_type, conditions, medications, emergency_contact_name, emergency_contact_phone)
VALUES
(1, 1, 180.00, 82.50, 'O+', 'asthma', 'albuterol', 'Jane Doe', '555-1111'),
(2, 6, 165.00, 60.00, 'A-', 'none', 'none', 'Sam Patel','555-2222');

-- =========================
-- MEDICAL RECORDS + HISTORY
-- =========================
INSERT IGNORE INTO medical_records (id, patient_id, created_by, record_type, record_data)
VALUES
(1, 1, 2, 'visit_note', 'Follow-up recommended in 2 weeks.'),
(2, 6, 5, 'visit_note', 'Initial consultation completed.'),
(3, 1, 7, 'nurse_note', 'Vitals taken and recorded.');

INSERT IGNORE INTO medical_history (id, patient_id, updated_by, history_data)
VALUES
(1, 1, 2, 'No major surgeries. Family history: hypertension.'),
(2, 6, 5, 'No known chronic conditions.');

-- =========================
-- ALLERGIES
-- =========================
INSERT IGNORE INTO allergies (id, patient_id, substance, reaction, severity, notes)
VALUES
(1, 1, 'Peanuts', 'Anaphylaxis', 'severe', NULL),
(2, 6, 'Penicillin', 'Rash', 'moderate', NULL);

-- =========================
-- LOGIN HISTORY
-- =========================
INSERT IGNORE INTO login_history (id, user_id, ip_address, user_agent, success)
VALUES
(1, 1, '127.0.0.1', 'demo-browser', TRUE),
(2, 2, '127.0.0.1', 'demo-browser', TRUE),
(3, 3, '127.0.0.1', 'demo-browser', TRUE),
(4, 4, '127.0.0.1', 'demo-browser', TRUE),
(5, 8, '127.0.0.1', 'demo-browser', TRUE);

-- =========================
-- SESSIONS
-- =========================
INSERT IGNORE INTO sessions (id, user_id, session_token, expires_at, revoked_at)
VALUES
(1, 1, 'demo_session_token_user_1', DATE_ADD(NOW(), INTERVAL 2 HOUR), NULL),
(2, 2, 'demo_session_token_user_2', DATE_ADD(NOW(), INTERVAL 2 HOUR), NULL),
(3, 4, 'demo_session_token_admin_4', DATE_ADD(NOW(), INTERVAL 2 HOUR), NULL);

-- =========================
-- RESET PASSWORD TOKENS
-- =========================
INSERT IGNORE INTO reset_password_tokens (id, user_id, token, expires_at, used_at)
VALUES
(1, 1, 'demo_reset_token_user_1', DATE_ADD(NOW(), INTERVAL 30 MINUTE), NULL);

-- =========================
-- AVAILABILITY SLOTS (trigger-safe)
-- =========================
INSERT IGNORE INTO availability_slots (id, provider_id, start_time, end_time, status)
VALUES
(1, 2, '2026-03-01 09:00:00', '2026-03-01 10:00:00', 'open'),
(2, 2, '2026-03-01 10:00:00', '2026-03-01 11:00:00', 'open'),
(3, 2, '2026-03-01 11:00:00', '2026-03-01 12:00:00', 'open'),
(4, 5, '2026-03-02 09:00:00', '2026-03-02 09:30:00', 'open'),
(5, 5, '2026-03-02 09:30:00', '2026-03-02 10:00:00', 'open');

-- =========================
-- APPOINTMENTS (must match OPEN slot; slot_id required)
-- =========================
INSERT IGNORE INTO appointments
(id, patient_id, provider_id, slot_id, parent_appointment_id, appointment_type, start_time, end_time, status, reason, cancel_note)
VALUES
(1, 1, 2, 1, NULL, 'new', '2026-03-01 09:00:00', '2026-03-01 10:00:00', 'scheduled', 'Checkup', NULL),
(2, 1, 2, 2, 1, 'follow_up', '2026-03-01 10:00:00', '2026-03-01 11:00:00', 'scheduled', 'Follow-up', NULL),
(3, 6, 5, 4, NULL, 'new', '2026-03-02 09:00:00', '2026-03-02 09:30:00', 'scheduled', 'New patient visit', NULL);
UPDATE appointments
SET status = 'cancelled', cancel_note = 'Patient request'
WHERE id = 2 AND status <> 'cancelled';
UPDATE availability_slots SET status='booked' WHERE id IN (1,4);
UPDATE availability_slots SET status='open' WHERE id IN (2,3,5);

-- =========================
-- VISIT ENCOUNTERS
-- =========================
INSERT IGNORE INTO countered_visits (id, appointment_id, checked_in_at, completed_at, notes)
VALUES
(1, 1, '2026-03-01 08:55:00', NULL, 'Patient checked in early.');

-- =========================
-- MESSAGE THREADS + MESSAGES
-- =========================
INSERT IGNORE INTO message_threads (id, subject, created_by)
VALUES
(1, 'Medication Question', 1),
(2, 'Appointment Follow-up', 6);

INSERT IGNORE INTO messages (id, thread_id, sender_id, receiver_id, body, is_read, read_at)
VALUES
(1, 1, 1, 2, 'Hello doctor, I have a question about my medication.', FALSE, NULL),
(2, 1, 2, 1, 'Sure—what medication and what symptoms are you experiencing?', FALSE, NULL),
(3, 2, 6, 5, 'Can I confirm my appointment time?', TRUE,  '2026-02-16 12:10:00');

-- =========================
-- NOTIFICATIONS
-- =========================
INSERT IGNORE INTO notifications (id, user_id, category, message, is_read, read_at)
VALUES
(1, 1, 'appointment', 'You have an upcoming appointment on March 1st.', FALSE, NULL),
(2, 1, 'message', 'You have a new message in Medication Question.', FALSE, NULL),
(3, 6, 'appointment', 'Your appointment is scheduled for March 2nd.', TRUE, '2026-02-16 12:15:00');

-- =========================
-- PHARMACIES + PATIENT PHARMACY
-- =========================
INSERT IGNORE INTO pharmacies (id, name, phone, address)
VALUES
(1, 'City Pharmacy', '555-3333', '10 Pharmacy Ln'),
(2, 'HealthMart', '555-4444', '20 Wellness Blvd');

INSERT IGNORE INTO pharmacy_patient (id, patient_id, pharmacy_id, is_preferred)
VALUES
(1, 1, 1, TRUE),
(2, 6, 2, TRUE);

-- =========================
-- PRESCRIPTIONS
-- =========================
INSERT IGNORE INTO prescriptions (id, patient_id, medication_name, dosage, frequency, start_date, end_date)
VALUES
(1, 1, 'Amoxicillin', '500mg', 'Twice daily', '2026-02-16', '2026-02-23'),
(2, 6, 'Ibuprofen', '200mg', 'As needed', '2026-02-16', NULL);

-- =========================
-- REFILL REQUESTS + AUTO REFILL SETTINGS
-- =========================
INSERT IGNORE INTO refill_requests
(id, prescription_id, requested_by, note, status, cancelled_at, cancel_reason)
VALUES
(1, 1, 1, 'Need refill soon', 'requested', NULL, NULL);

INSERT IGNORE INTO auto_refill_settings
(id, prescription_id, enabled, interval_days, next_run_at)
VALUES
(1, 1, TRUE, 30, '2026-03-15 09:00:00');

-- =========================
-- PRIVACY + DATA SHARING PREFS
-- =========================
INSERT IGNORE INTO privacy_settings (id, patient_id, allow_email, allow_sms)
VALUES
(1, 1, TRUE, FALSE),
(2, 6, TRUE, TRUE);

INSERT IGNORE INTO data_sharing_prefs (id, patient_id, share_with_providers, share_for_research)
VALUES
(1, 1, TRUE, FALSE),
(2, 6, TRUE, TRUE);

-- =========================
-- SUPPORT TICKETS
-- =========================
INSERT IGNORE INTO support_tickets
(id, created_by, assigned_to, subject, description, status, closed_at, close_note)
VALUES
(1, 1, 3, 'Portal access issue', 'Cannot upload insurance card.', 'in_progress', NULL, NULL);

-- =========================
-- SECURITY QUESTIONS + USER ANSWERS
-- =========================
INSERT IGNORE INTO security_questions (id, question_text, is_active)
VALUES
(1, 'What is the name of your first pet?', TRUE),
(2, 'What city were you born in?', TRUE);

INSERT IGNORE INTO user_security_qa (id, user_id, question_id, answer_hash)
VALUES
(1, 1, 1, 'answer_hash_here'),
(2, 1, 2, 'answer_hash_here');

-- =========================
-- IDENTITY VERIFICATION
-- =========================
INSERT IGNORE INTO identity_verifications
(id, user_id, action_type, status, verified_at, failure_reason)
VALUES
(1, 1, 'password_reset', 'success', '2026-02-16 12:05:00', NULL);

-- =========================
-- INSURANCE POLICIES + DOCUMENTS
-- =========================
INSERT IGNORE INTO insurance_policies
(id, patient_id, payer_name, plan_name, member_id, group_number, relationship_to_patient,
 policyholder_name, policyholder_dob, effective_start, effective_end, phone, address, is_primary)
VALUES
(1, 1, 'Blue Cross', 'Basic Plan', 'ABC123', 'G100', 'self',
 NULL, NULL, '2026-01-01', NULL, '555-7777', '1 Insurance Way', TRUE),
(2, 1, 'DentalCo', 'Dental Plan', 'DENT456', NULL, 'self',
 NULL, NULL, '2026-01-01', NULL, '555-8888', '2 Insurance Way', FALSE);

INSERT IGNORE INTO insurance_documents (id, policy_id, doc_type, file_url)
VALUES
(1, 1, 'front_card', 'https://example.com/insurance/front.png'),
(2, 1, 'back_card', 'https://example.com/insurance/back.png');


UPDATE users
SET password_hash = '$2b$12$hBvv3VGZXlJ0NaQSza4Yoegoc6foj.741ukzQt95nMHRLWEGX7CpG' -- Password123!
WHERE password_hash = 'hashed_password_here';

