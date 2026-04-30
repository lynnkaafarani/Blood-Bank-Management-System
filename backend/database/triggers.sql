USE BBMS_SE;

DELIMITER //

DROP TRIGGER IF EXISTS trg_after_blood_request_insert//

CREATE TRIGGER trg_after_blood_request_insert
AFTER INSERT ON BloodRequest
FOR EACH ROW
BEGIN
    INSERT INTO Notification (user_id, message, type)
    SELECT r.user_id,
           CONCAT('Your blood request #', NEW.request_id, ' has been submitted successfully.'),
           'Request'
    FROM Recipient r
    WHERE r.recipient_id = NEW.recipient_id;
END//


DROP TRIGGER IF EXISTS trg_after_blood_request_update//

CREATE TRIGGER trg_after_blood_request_update
AFTER UPDATE ON BloodRequest
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO Notification (user_id, message, type)
        SELECT r.user_id,
               CONCAT('Your blood request #', NEW.request_id, ' status changed to ', NEW.status, '.'),
               'Request'
        FROM Recipient r
        WHERE r.recipient_id = NEW.recipient_id;
    END IF;
END//


DROP TRIGGER IF EXISTS trg_after_blood_unit_insert//

CREATE TRIGGER trg_after_blood_unit_insert
AFTER INSERT ON BloodUnit
FOR EACH ROW
BEGIN
    INSERT INTO ActivityLog (
        user_id,
        action_type,
        entity_type,
        entity_id,
        description
    )
    VALUES (
        NULL,
        'CREATE',
        'BloodUnit',
        NEW.blood_unit_id,
        CONCAT('New blood unit added: ', NEW.blood_type, ', ', NEW.quantity_ml, ' ml.')
    );
END//


DROP TRIGGER IF EXISTS trg_before_blood_unit_insert//

CREATE TRIGGER trg_before_blood_unit_insert
BEFORE INSERT ON BloodUnit
FOR EACH ROW
BEGIN
    IF NEW.expiry_date <= NEW.donation_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Expiry date must be after donation date';
    END IF;

    IF NEW.quantity_ml <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood quantity must be greater than zero';
    END IF;
END//


DROP TRIGGER IF EXISTS trg_after_appointment_insert//

CREATE TRIGGER trg_after_appointment_insert
AFTER INSERT ON Appointment
FOR EACH ROW
BEGIN
    INSERT INTO Notification (user_id, message, type)
    SELECT d.user_id,
           CONCAT('Your donation appointment has been scheduled for ', NEW.appointment_datetime, '.'),
           'Appointment'
    FROM Donor d
    WHERE d.donor_id = NEW.donor_id;
END//


DROP TRIGGER IF EXISTS trg_after_donation_insert//

CREATE TRIGGER trg_after_donation_insert
AFTER INSERT ON Donation
FOR EACH ROW
BEGIN
    INSERT INTO ActivityLog (
        user_id,
        action_type,
        entity_type,
        entity_id,
        description
    )
    SELECT hs.user_id,
           'CREATE',
           'Donation',
           NEW.donation_id,
           CONCAT('Donation recorded for donor ID ', NEW.donor_id)
    FROM HospitalStaff hs
    WHERE hs.staff_id = NEW.staff_id;
END//


DROP TRIGGER IF EXISTS trg_after_donor_update//

CREATE TRIGGER trg_after_donor_update
AFTER UPDATE ON Donor
FOR EACH ROW
BEGIN
    IF OLD.eligibility_status <> NEW.eligibility_status THEN
        INSERT INTO Notification (user_id, message, type)
        VALUES (
            NEW.user_id,
            CONCAT('Your donor eligibility status changed to ', NEW.eligibility_status, '.'),
            'System'
        );
    END IF;
END//

DELIMITER ;

SELECT 'SRS 3NF triggers created successfully' AS message;