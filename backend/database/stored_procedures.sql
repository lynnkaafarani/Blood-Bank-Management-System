USE BBMS_SE;

DELIMITER //

DROP PROCEDURE IF EXISTS RegisterDonation//

CREATE PROCEDURE RegisterDonation(
    IN p_donor_id INT,
    IN p_staff_id INT,
    IN p_hospital_id INT,
    IN p_blood_type VARCHAR(3),
    IN p_quantity_ml INT,
    OUT p_donation_id INT,
    OUT p_blood_unit_id INT
)
BEGIN
    DECLARE v_last_donation DATE;
    DECLARE v_health_status VARCHAR(100);
    DECLARE v_eligibility_status VARCHAR(50);
    DECLARE v_medication_restricted BOOLEAN;
    DECLARE v_donor_blood_type VARCHAR(3);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT blood_type, health_status, medication_restricted, last_donation_date, eligibility_status
    INTO v_donor_blood_type, v_health_status, v_medication_restricted, v_last_donation, v_eligibility_status
    FROM Donor
    WHERE donor_id = p_donor_id;

    IF v_donor_blood_type IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor not found';
    END IF;

    IF v_donor_blood_type <> p_blood_type THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood type does not match donor blood type';
    END IF;

    IF v_health_status <> 'Healthy' OR v_medication_restricted = TRUE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor health status is not suitable for donation';
    END IF;

    IF v_eligibility_status <> 'Eligible' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor is not eligible for donation';
    END IF;

    IF v_last_donation IS NOT NULL AND DATEDIFF(CURDATE(), v_last_donation) < 56 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor must wait at least 56 days between donations';
    END IF;

    INSERT INTO BloodUnit (
        hospital_id,
        donor_id,
        blood_type,
        component_type,
        quantity_ml,
        donation_date,
        expiry_date,
        status
    )
    VALUES (
        p_hospital_id,
        p_donor_id,
        p_blood_type,
        'Whole Blood',
        p_quantity_ml,
        CURDATE(),
        DATE_ADD(CURDATE(), INTERVAL 42 DAY),
        'Available'
    );

    SET p_blood_unit_id = LAST_INSERT_ID();

    INSERT INTO Donation (
        donor_id,
        staff_id,
        hospital_id,
        blood_unit_id,
        donation_date,
        status
    )
    VALUES (
        p_donor_id,
        p_staff_id,
        p_hospital_id,
        p_blood_unit_id,
        CURDATE(),
        'Processed'
    );

    SET p_donation_id = LAST_INSERT_ID();

    UPDATE Donor
    SET last_donation_date = CURDATE()
    WHERE donor_id = p_donor_id;

    INSERT INTO ActivityLog (
        user_id,
        action_type,
        entity_type,
        entity_id,
        description
    )
    SELECT hs.user_id, 'CREATE', 'Donation', p_donation_id,
           CONCAT('Registered donation for donor ID ', p_donor_id)
    FROM HospitalStaff hs
    WHERE hs.staff_id = p_staff_id;

    COMMIT;

    SELECT 'Donation registered successfully' AS message,
           p_donation_id AS donation_id,
           p_blood_unit_id AS blood_unit_id;
END//


DROP PROCEDURE IF EXISTS ProcessBloodRequest//

CREATE PROCEDURE ProcessBloodRequest(
    IN p_request_id INT,
    IN p_blood_unit_id INT,
    IN p_staff_id INT
)
BEGIN
    DECLARE v_request_status VARCHAR(30);
    DECLARE v_request_blood_type VARCHAR(3);
    DECLARE v_quantity_needed INT;
    DECLARE v_recipient_user_id INT;

    DECLARE v_unit_status VARCHAR(30);
    DECLARE v_unit_blood_type VARCHAR(3);
    DECLARE v_unit_quantity INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT br.status, br.blood_type, br.quantity_needed_ml, ua.user_id
    INTO v_request_status, v_request_blood_type, v_quantity_needed, v_recipient_user_id
    FROM BloodRequest br
    JOIN Recipient r ON br.recipient_id = r.recipient_id
    JOIN UserAccount ua ON r.user_id = ua.user_id
    WHERE br.request_id = p_request_id;

    IF v_request_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood request not found';
    END IF;

    IF v_request_status <> 'Pending' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood request is not pending';
    END IF;

    SELECT status, blood_type, quantity_ml
    INTO v_unit_status, v_unit_blood_type, v_unit_quantity
    FROM BloodUnit
    WHERE blood_unit_id = p_blood_unit_id;

    IF v_unit_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood unit not found';
    END IF;

    IF v_unit_status <> 'Available' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood unit is not available';
    END IF;

    IF v_unit_blood_type <> v_request_blood_type THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood type does not match request';
    END IF;

    IF v_unit_quantity < v_quantity_needed THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient blood quantity';
    END IF;

    UPDATE BloodUnit
    SET status = 'Used'
    WHERE blood_unit_id = p_blood_unit_id;

    UPDATE BloodRequest
    SET status = 'Fulfilled',
        processed_by_staff_id = p_staff_id,
        blood_unit_id = p_blood_unit_id
    WHERE request_id = p_request_id;

    INSERT INTO Notification (user_id, message, type)
    VALUES (
        v_recipient_user_id,
        CONCAT('Your blood request #', p_request_id, ' has been fulfilled.'),
        'Request'
    );

    INSERT INTO ActivityLog (
        user_id,
        action_type,
        entity_type,
        entity_id,
        description
    )
    SELECT hs.user_id, 'UPDATE', 'BloodRequest', p_request_id,
           CONCAT('Fulfilled blood request using blood unit ID ', p_blood_unit_id)
    FROM HospitalStaff hs
    WHERE hs.staff_id = p_staff_id;

    COMMIT;

    SELECT 'Blood request fulfilled successfully' AS message;
END//


DROP PROCEDURE IF EXISTS RejectBloodRequest//

CREATE PROCEDURE RejectBloodRequest(
    IN p_request_id INT,
    IN p_staff_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE v_request_status VARCHAR(30);
    DECLARE v_recipient_user_id INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT br.status, ua.user_id
    INTO v_request_status, v_recipient_user_id
    FROM BloodRequest br
    JOIN Recipient r ON br.recipient_id = r.recipient_id
    JOIN UserAccount ua ON r.user_id = ua.user_id
    WHERE br.request_id = p_request_id;

    IF v_request_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Blood request not found';
    END IF;

    IF v_request_status <> 'Pending' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only pending requests can be rejected';
    END IF;

    UPDATE BloodRequest
    SET status = 'Rejected',
        processed_by_staff_id = p_staff_id
    WHERE request_id = p_request_id;

    INSERT INTO Notification (user_id, message, type)
    VALUES (
        v_recipient_user_id,
        CONCAT('Your blood request #', p_request_id, ' was rejected. Reason: ', p_reason),
        'Request'
    );

    INSERT INTO ActivityLog (
        user_id,
        action_type,
        entity_type,
        entity_id,
        description
    )
    SELECT hs.user_id, 'UPDATE', 'BloodRequest', p_request_id,
           CONCAT('Rejected blood request. Reason: ', p_reason)
    FROM HospitalStaff hs
    WHERE hs.staff_id = p_staff_id;

    COMMIT;

    SELECT 'Blood request rejected successfully' AS message;
END//


DROP PROCEDURE IF EXISTS UpdateExpiredBloodUnits//

CREATE PROCEDURE UpdateExpiredBloodUnits()
BEGIN
    UPDATE BloodUnit
    SET status = 'Expired'
    WHERE expiry_date < CURDATE()
      AND status = 'Available';

    SELECT ROW_COUNT() AS expired_units_updated;
END//

DELIMITER ;

SELECT 'SRS 3NF stored procedures created successfully' AS message;