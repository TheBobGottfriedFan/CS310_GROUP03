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
 'view_insurance'
);
