USE patient_portal;

DELIMITER $$

CREATE TRIGGER trg_avail_end_after_start_ins
BEFORE INSERT ON availability_slots
FOR EACH ROW
BEGIN
 IF NEW.end_time <= NEW.start_time THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'availability_slots end_time must be > start_time.';
 END IF;
END$$

CREATE TRIGGER trg_avail_end_after_start_upd
BEFORE UPDATE ON availability_slots
FOR EACH ROW
BEGIN
 IF NEW.end_time <= NEW.start_time THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'availability_slots end_time must be > or = than start_time.';
 END IF;
END$$

CREATE TRIGGER trg_appt_end_after_start_ins
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
 IF NEW.end_time <= NEW.start_time THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'appointments end_time must be > start_time.';
 END IF;
END$$

CREATE TRIGGER trg_appt_end_after_start_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF NEW.end_time <= NEW.start_time THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'appointments end_time must be greater than start_time.';
 END IF;
END$$

CREATE TRIGGER trg_avail_no_overlap_ins
BEFORE INSERT ON availability_slots
FOR EACH ROW
BEGIN
 IF EXISTS (
  SELECT 1
  FROM availability_slots s
  WHERE s.provider_id = NEW.provider_id
   AND NOT (NEW.end_time <= s.start_time OR NEW.start_time >= s.end_time)
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'Overlap availability slot (provider).';
 END IF;
END$$

CREATE TRIGGER trg_avail_no_overlap_upd
BEFORE UPDATE ON availability_slots
FOR EACH ROW
BEGIN
 IF EXISTS (
  SELECT 1
   FROM availability_slots s
   WHERE s.provider_id = NEW.provider_id
    AND s.id <> NEW.id
    AND NOT (NEW.end_time <= s.start_time OR NEW.start_time >= s.end_time)
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'Overlap availability slot (provider).';
 END IF;
END$$

CREATE TRIGGER trg_appt_no_overlap_ins
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
 IF EXISTS (
  SELECT 1
  FROM appointments a
  WHERE a.provider_id = NEW.provider_id
   AND a.status IN ('requested','scheduled','completed') 
   AND NOT (NEW.end_time <= a.start_time OR NEW.start_time >= a.end_time)
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'The provider already has overlap appointment.';
 END IF;
-- patient overlapping
 IF EXISTS (
  SELECT 1
  FROM appointments a
  WHERE a.patient_id = NEW.patient_id
   AND a.status IN ('requested','scheduled','completed')
   AND NOT (NEW.end_time <= a.start_time OR NEW.start_time >= a.end_time)
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'Patient already has an overlapping appointment.';
 END IF;
END$$


CREATE TRIGGER trg_appt_requires_open_slot_ins
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
 IF NOT EXISTS (
  SELECT 1
  FROM availability_slots s
  WHERE s.id = NEW.slot_id
   AND s.provider_id = NEW.provider_id
   AND s.status = 'open'
   AND s.start_time = NEW.start_time
   AND s.end_time = NEW.end_time
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'slot_id must connect too open availability slot matching a provider, start, end.';
 END IF;
END$$

CREATE TRIGGER trg_appt_book_slot_after_ins
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
 UPDATE availability_slots
 SET status = 'booked'
 WHERE id = NEW.slot_id;
END$$

CREATE TRIGGER trg_appt_reopen_slot_after_upd
AFTER UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF NEW.status = 'cancelled' AND OLD.status <> 'cancelled' THEN
  UPDATE availability_slots
  SET status = 'open'
  WHERE id = NEW.slot_id;
 END IF;
END$$

CREATE TRIGGER trg_ins_one_primary_ins
BEFORE INSERT ON insurance_policies
FOR EACH ROW
BEGIN
 IF NEW.is_primary = TRUE THEN
  UPDATE insurance_policies
  SET is_primary = FALSE
  WHERE patient_id = NEW.patient_id;
 END IF;
END$$

CREATE TRIGGER trg_ins_one_primary_upd
BEFORE UPDATE ON insurance_policies
FOR EACH ROW
BEGIN
 IF NEW.is_primary = TRUE THEN
  UPDATE insurance_policies
  SET is_primary = FALSE
  WHERE patient_id = NEW.patient_id
   AND id <> NEW.id;
 END IF;
END$$

-- Aduit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 entity VARCHAR(50) NOT NULL,
 entity_id BIGINT NULL,
 action ENUM('INSERT','UPDATE','DELETE') NOT NULL,
 changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 details TEXT NULL
) ENGINE=InnoDB;



-- Rule Enforcements for Appointments
DROP TRIGGER IF EXISTS trg_appt_role_enforce_ins$$
CREATE TRIGGER trg_appt_role_enforce_ins
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
-- THE PATIENT IS A PATIENT WE HOPE.
 IF NOT EXISTS (
  SELECT 1
  FROM users u
  JOIN roles r ON r.id = u.role_id
  WHERE u.id = NEW.patient_id
   AND r.name = 'patient'
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'patient_id must reference user with the role "patient"';
 END IF;
-- THE PROVIDER IS (god hope so) A DOCTOR OR A NURSE
 IF NOT EXISTS (
  SELECT 1
  FROM users u
  JOIN roles r ON r.id = u.role_id
  WHERE u.id = NEW.provider_id
   AND r.name IN ('doctor','nurse')
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'provider_id must reference user with the roles of either a doctor or a nurse.';
 END IF;
END$$

DROP TRIGGER IF EXISTS trg_appt_role_enforce_upd$$
CREATE TRIGGER trg_appt_role_enforce_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
-- THE PATIENT IS A PATIENT WE HOPE.
 IF NOT EXISTS (
  SELECT 1
  FROM users u
  JOIN roles r ON r.id = u.role_id
  WHERE u.id = NEW.patient_id
   AND r.name = 'patient'
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'patient_id must reference user with the role patient.';
 END IF;
-- THE PROVIDER MUST BE EITHER A DOCTOR OR A NURSE
 IF NOT EXISTS (
  SELECT 1
  FROM users u
  JOIN roles r ON r.id = u.role_id
  WHERE u.id = NEW.provider_id
   AND r.name IN ('doctor','nurse')
 ) THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'provider_id must reference user with the role doctor or nurse.';
 END IF;
END$$


DROP TRIGGER IF EXISTS trg_appt_immutable_schedule_upd$$
CREATE TRIGGER trg_appt_immutable_schedule_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF NEW.patient_id <> OLD.patient_id
  OR NEW.provider_id <> OLD.provider_id
  OR NEW.slot_id <> OLD.slot_id
  OR NEW.start_time <> OLD.start_time
  OR NEW.end_time <> OLD.end_time
 THEN
  SIGNAL SQLSTATE '45000'
   SET MESSAGE_TEXT = 'Appointments cannot be rescheduled/retargeted (patient/provider/slot/start/end cannot be modified afterwards).';
 END IF;
END$$

DROP TRIGGER IF EXISTS trg_appt_no_overlap_upd$$
CREATE TRIGGER trg_appt_no_overlap_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF NEW.status IN ('requested','scheduled','completed') THEN
  IF EXISTS (
   SELECT 1
   FROM appointments a
   WHERE a.provider_id = NEW.provider_id
    AND a.id <> OLD.id
    AND a.status IN ('requested','scheduled','completed')
    AND NOT (NEW.end_time <= a.start_time OR NEW.start_time >= a.end_time)
  ) THEN
   SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Provider already has an overlapping appointment (UPDATE).';
  END IF;
  IF EXISTS (
   SELECT 1
   FROM appointments a
   WHERE a.patient_id = NEW.patient_id
    AND a.id <> OLD.id
    AND a.status IN ('requested','scheduled','completed')
    AND NOT (NEW.end_time <= a.start_time OR NEW.start_time >= a.end_time)
  ) THEN
   SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Patient already has an overlapping appointment (UPDATE).';
  END IF;
 END IF;
END$$

DROP TRIGGER IF EXISTS trg_appt_requires_open_slot_upd$$
CREATE TRIGGER trg_appt_requires_open_slot_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF OLD.status = 'cancelled' AND NEW.status IN ('requested','scheduled','completed') THEN
  IF NOT EXISTS (
   SELECT 1
   FROM availability_slots s
   WHERE s.id = NEW.slot_id
    AND s.provider_id = NEW.provider_id
    AND s.status = 'open'
    AND s.start_time = NEW.start_time
    AND s.end_time = NEW.end_time
  ) THEN
   SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot reactivate appointment: slot must be open and match provider/start/end.';
  END IF;
 END IF;
END$$

DROP TRIGGER IF EXISTS trg_appt_rebook_slot_after_upd$$
CREATE TRIGGER trg_appt_rebook_slot_after_upd
AFTER UPDATE ON appointments
FOR EACH ROW
BEGIN
 IF OLD.status = 'cancelled' AND NEW.status IN ('requested','scheduled','completed') THEN
  UPDATE availability_slots
  SET status = 'booked'
  WHERE id = NEW.slot_id;
 END IF;
END$$


DROP TRIGGER IF EXISTS trg_appt_reopen_slot_after_del$$
CREATE TRIGGER trg_appt_reopen_slot_after_del
AFTER DELETE ON appointments
FOR EACH ROW
BEGIN
 UPDATE availability_slots
 SET status = 'open'
 WHERE id = OLD.slot_id;
END$$


DROP TRIGGER IF EXISTS trg_audit_appt_ins$$
CREATE TRIGGER trg_audit_appt_ins
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('appointments', NEW.id, 'INSERT', CONCAT('Created appt id=', NEW.id));
END$$

DROP TRIGGER IF EXISTS trg_audit_appt_upd$$
CREATE TRIGGER trg_audit_appt_upd
AFTER UPDATE ON appointments
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('appointments', NEW.id, 'UPDATE', CONCAT('Updated appt id=', NEW.id, ' status ', OLD.status, ' -> ', NEW.status));
END$$

DROP TRIGGER IF EXISTS trg_audit_appt_del$$
CREATE TRIGGER trg_audit_appt_del
AFTER DELETE ON appointments
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('appointments', OLD.id, 'DELETE', CONCAT('Deleted appt id=', OLD.id));
END$$

DROP TRIGGER IF EXISTS trg_audit_avail_ins$$
CREATE TRIGGER trg_audit_avail_ins
AFTER INSERT ON availability_slots
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('availability_slots', NEW.id, 'INSERT', CONCAT('Created slot id=', NEW.id));
END$$

DROP TRIGGER IF EXISTS trg_audit_avail_upd$$
CREATE TRIGGER trg_audit_avail_upd
AFTER UPDATE ON availability_slots
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('availability_slots', NEW.id, 'UPDATE', CONCAT('Updated slot id=', NEW.id, ' status ', OLD.status, ' -> ', NEW.status));
END$$

DROP TRIGGER IF EXISTS trg_audit_avail_del$$
CREATE TRIGGER trg_audit_avail_del
AFTER DELETE ON availability_slots
FOR EACH ROW
BEGIN
 INSERT INTO audit_log (entity, entity_id, action, details)
 VALUES ('availability_slots', OLD.id, 'DELETE', CONCAT('Deleted slot id=', OLD.id));
END$$


 
DELIMITER ;
