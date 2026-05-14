-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               12.0.2-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             12.11.0.7065
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for bbms_se
DROP DATABASE IF EXISTS `bbms_se`;
CREATE DATABASE IF NOT EXISTS `bbms_se` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;
USE `bbms_se`;

-- Dumping structure for table bbms_se.activitylog
CREATE TABLE IF NOT EXISTS `activitylog` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `action_type` varchar(80) NOT NULL,
  `entity_type` varchar(80) DEFAULT NULL,
  `entity_id` int(11) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`log_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `activitylog_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.activitylog: ~16 rows (approximately)
INSERT IGNORE INTO `activitylog` (`log_id`, `user_id`, `action_type`, `entity_type`, `entity_id`, `description`, `created_at`) VALUES
	(1, NULL, 'CREATE', 'BloodUnit', 1, 'New blood unit added: O+, 450 ml.', '2026-05-15 01:40:36'),
	(2, NULL, 'CREATE', 'BloodUnit', 2, 'New blood unit added: A+, 450 ml.', '2026-05-15 01:40:36'),
	(3, NULL, 'CREATE', 'BloodUnit', 3, 'New blood unit added: O-, 450 ml.', '2026-05-15 01:40:36'),
	(4, 3, 'CREATE', 'Donation', 1, 'Donation recorded for donor ID 4', '2026-05-15 01:40:46'),
	(5, 3, 'CREATE', 'Donation', 2, 'Donation recorded for donor ID 5', '2026-05-15 01:40:46'),
	(6, 1, 'CREATE', 'Hospital', 1, 'Initial hospital data inserted.', '2026-05-15 01:41:22'),
	(7, 2, 'CREATE', 'BloodUnit', 1, 'Blood unit added to inventory.', '2026-05-15 01:41:22');

-- Dumping structure for table bbms_se.appointment
CREATE TABLE IF NOT EXISTS `appointment` (
  `appointment_id` int(11) NOT NULL AUTO_INCREMENT,
  `donor_id` int(11) NOT NULL,
  `hospital_id` int(11) NOT NULL,
  `appointment_datetime` datetime NOT NULL,
  `status` enum('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled',
  `eligibility_snapshot` varchar(100) DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`appointment_id`),
  KEY `donor_id` (`donor_id`),
  KEY `hospital_id` (`hospital_id`),
  CONSTRAINT `appointment_ibfk_1` FOREIGN KEY (`donor_id`) REFERENCES `donor` (`donor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `appointment_ibfk_2` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.appointment: ~8 rows (approximately)
INSERT IGNORE INTO `appointment` (`appointment_id`, `donor_id`, `hospital_id`, `appointment_datetime`, `status`, `eligibility_snapshot`, `notes`) VALUES
	(1, 4, 1, '2026-05-05 10:00:00', 'Scheduled', 'Eligible', 'Routine donation appointment'),
	(2, 5, 2, '2026-05-06 11:00:00', 'Scheduled', 'Eligible', 'Routine donation appointment');

-- Dumping structure for table bbms_se.authsession
CREATE TABLE IF NOT EXISTS `authsession` (
  `session_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `token_hash` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL,
  PRIMARY KEY (`session_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `authsession_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.authsession: ~0 rows (approximately)

-- Dumping structure for table bbms_se.bloodrequest
CREATE TABLE IF NOT EXISTS `bloodrequest` (
  `request_id` int(11) NOT NULL AUTO_INCREMENT,
  `recipient_id` int(11) NOT NULL,
  `hospital_id` int(11) NOT NULL,
  `processed_by_staff_id` int(11) DEFAULT NULL,
  `blood_unit_id` int(11) DEFAULT NULL,
  `blood_type` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
  `quantity_needed_ml` int(11) NOT NULL,
  `request_date` datetime DEFAULT current_timestamp(),
  `priority_level` enum('Low','Medium','High','Critical') DEFAULT 'Medium',
  `status` enum('Pending','Approved','Rejected','Cancelled','Fulfilled') DEFAULT 'Pending',
  PRIMARY KEY (`request_id`),
  KEY `recipient_id` (`recipient_id`),
  KEY `hospital_id` (`hospital_id`),
  KEY `processed_by_staff_id` (`processed_by_staff_id`),
  KEY `blood_unit_id` (`blood_unit_id`),
  KEY `idx_request_status` (`status`),
  CONSTRAINT `bloodrequest_ibfk_1` FOREIGN KEY (`recipient_id`) REFERENCES `recipient` (`recipient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `bloodrequest_ibfk_2` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `bloodrequest_ibfk_3` FOREIGN KEY (`processed_by_staff_id`) REFERENCES `hospitalstaff` (`staff_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `bloodrequest_ibfk_4` FOREIGN KEY (`blood_unit_id`) REFERENCES `bloodunit` (`blood_unit_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `CONSTRAINT_1` CHECK (`quantity_needed_ml` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.bloodrequest: ~5 rows (approximately)
INSERT IGNORE INTO `bloodrequest` (`request_id`, `recipient_id`, `hospital_id`, `processed_by_staff_id`, `blood_unit_id`, `blood_type`, `quantity_needed_ml`, `request_date`, `priority_level`, `status`) VALUES
	(1, 1, 1, NULL, NULL, 'O+', 400, '2026-05-15 01:40:55', 'High', 'Pending'),
	(2, 2, 1, NULL, NULL, 'A+', 350, '2026-05-15 01:40:55', 'Critical', 'Pending');

-- Dumping structure for table bbms_se.bloodunit
CREATE TABLE IF NOT EXISTS `bloodunit` (
  `blood_unit_id` int(11) NOT NULL AUTO_INCREMENT,
  `hospital_id` int(11) NOT NULL,
  `donor_id` int(11) DEFAULT NULL,
  `blood_type` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
  `component_type` varchar(50) DEFAULT 'Whole Blood',
  `quantity_ml` int(11) NOT NULL,
  `donation_date` date NOT NULL,
  `expiry_date` date NOT NULL,
  `status` enum('Available','Reserved','Used','Expired') DEFAULT 'Available',
  PRIMARY KEY (`blood_unit_id`),
  KEY `hospital_id` (`hospital_id`),
  KEY `donor_id` (`donor_id`),
  KEY `idx_blood_type_status` (`blood_type`,`status`),
  CONSTRAINT `bloodunit_ibfk_1` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `bloodunit_ibfk_2` FOREIGN KEY (`donor_id`) REFERENCES `donor` (`donor_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `CONSTRAINT_1` CHECK (`quantity_ml` > 0),
  CONSTRAINT `CONSTRAINT_2` CHECK (`expiry_date` > `donation_date`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.bloodunit: ~6 rows (approximately)
INSERT IGNORE INTO `bloodunit` (`blood_unit_id`, `hospital_id`, `donor_id`, `blood_type`, `component_type`, `quantity_ml`, `donation_date`, `expiry_date`, `status`) VALUES
	(1, 1, 4, 'O+', 'Whole Blood', 450, '2026-04-01', '2026-05-15', 'Available'),
	(2, 1, 5, 'A+', 'Whole Blood', 450, '2026-04-05', '2026-05-20', 'Available'),
	(3, 2, 6, 'O-', 'Whole Blood', 450, '2026-04-10', '2026-05-25', 'Available');

-- Dumping structure for table bbms_se.donation
CREATE TABLE IF NOT EXISTS `donation` (
  `donation_id` int(11) NOT NULL AUTO_INCREMENT,
  `donor_id` int(11) NOT NULL,
  `staff_id` int(11) DEFAULT NULL,
  `hospital_id` int(11) NOT NULL,
  `blood_unit_id` int(11) DEFAULT NULL,
  `donation_date` date NOT NULL,
  `status` enum('Pending','Processed','Rejected') DEFAULT 'Pending',
  PRIMARY KEY (`donation_id`),
  UNIQUE KEY `blood_unit_id` (`blood_unit_id`),
  KEY `donor_id` (`donor_id`),
  KEY `staff_id` (`staff_id`),
  KEY `hospital_id` (`hospital_id`),
  CONSTRAINT `donation_ibfk_1` FOREIGN KEY (`donor_id`) REFERENCES `donor` (`donor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `donation_ibfk_2` FOREIGN KEY (`staff_id`) REFERENCES `hospitalstaff` (`staff_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `donation_ibfk_3` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `donation_ibfk_4` FOREIGN KEY (`blood_unit_id`) REFERENCES `bloodunit` (`blood_unit_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.donation: ~3 rows (approximately)
INSERT IGNORE INTO `donation` (`donation_id`, `donor_id`, `staff_id`, `hospital_id`, `blood_unit_id`, `donation_date`, `status`) VALUES
	(1, 4, 2, 1, 1, '2026-04-01', 'Processed'),
	(2, 5, 2, 1, 2, '2026-04-05', 'Processed'),
	(3, 6, 3, 2, 3, '2026-04-10', 'Processed');

-- Dumping structure for table bbms_se.donor
CREATE TABLE IF NOT EXISTS `donor` (
  `donor_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `blood_type` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
  `health_status` varchar(100) DEFAULT 'Healthy',
  `weight_kg` decimal(5,2) DEFAULT NULL,
  `medication_restricted` tinyint(1) DEFAULT 0,
  `last_donation_date` date DEFAULT NULL,
  `eligibility_status` enum('Eligible','TemporarilyDeferred','PermanentlyDeferred') DEFAULT 'Eligible',
  `deferral_reason` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`donor_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `donor_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `CONSTRAINT_1` CHECK (`weight_kg` is null or `weight_kg` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.donor: ~8 rows (approximately)
INSERT IGNORE INTO `donor` (`donor_id`, `user_id`, `blood_type`, `health_status`, `weight_kg`, `medication_restricted`, `last_donation_date`, `eligibility_status`, `deferral_reason`) VALUES
	(1, 4, 'O+', 'Healthy', 70.50, 0, '2025-10-10', 'Eligible', NULL),
	(2, 5, 'A+', 'Healthy', 62.00, 0, '2025-08-20', 'Eligible', NULL),
	(3, 6, 'O-', 'Healthy', 58.00, 0, NULL, 'Eligible', NULL);

-- Dumping structure for table bbms_se.hospital
CREATE TABLE IF NOT EXISTS `hospital` (
  `hospital_id` int(11) NOT NULL AUTO_INCREMENT,
  `hospital_name` varchar(150) NOT NULL,
  `location` varchar(200) NOT NULL,
  `contact_info` varchar(100) NOT NULL,
  PRIMARY KEY (`hospital_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.hospital: ~6 rows (approximately)
INSERT IGNORE INTO `hospital` (`hospital_id`, `hospital_name`, `location`, `contact_info`) VALUES
	(1, 'Rafik Hariri University Hospital', 'Beirut, Lebanon', '+961-1-830000'),
	(2, 'American University of Beirut Medical Center', 'Hamra, Beirut', '+961-1-350000'),
	(3, 'Hotel Dieu de France Hospital', 'Achrafieh, Beirut', '+961-1-615300');

-- Dumping structure for table bbms_se.hospitalstaff
CREATE TABLE IF NOT EXISTS `hospitalstaff` (
  `staff_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `hospital_id` int(11) NOT NULL,
  `staff_role` varchar(80) NOT NULL,
  PRIMARY KEY (`staff_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `hospital_id` (`hospital_id`),
  CONSTRAINT `hospitalstaff_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `hospitalstaff_ibfk_2` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.hospitalstaff: ~2 rows (approximately)
INSERT IGNORE INTO `hospitalstaff` (`staff_id`, `user_id`, `hospital_id`, `staff_role`) VALUES
	(1, 2, 1, 'Lab Technician'),
	(2, 3, 2, 'Nurse');

-- Dumping structure for table bbms_se.notification
CREATE TABLE IF NOT EXISTS `notification` (
  `notification_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` varchar(255) NOT NULL,
  `notification_date` datetime DEFAULT current_timestamp(),
  `type` enum('Info','Appointment','Request','Shortage','System') DEFAULT 'Info',
  `is_read` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`notification_id`),
  KEY `idx_notification_user` (`user_id`),
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.notification: ~21 rows (approximately)
INSERT IGNORE INTO `notification` (`notification_id`, `user_id`, `message`, `notification_date`, `type`, `is_read`) VALUES
	(1, 7, 'Your blood request #1 has been submitted successfully.', '2026-05-15 01:40:55', 'Request', 0),
	(2, 8, 'Your blood request #2 has been submitted successfully.', '2026-05-15 01:40:55', 'Request', 0),
	(3, 4, 'Urgent O+ blood shortage reported at RHUH.', '2026-05-15 01:41:12', 'Shortage', 0),
	(4, 7, 'Your blood request has been submitted successfully.', '2026-05-15 01:41:12', 'Request', 0);

-- Dumping structure for procedure bbms_se.ProcessBloodRequest
DELIMITER //
CREATE PROCEDURE `ProcessBloodRequest`(
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
DELIMITER ;

-- Dumping structure for table bbms_se.recipient
CREATE TABLE IF NOT EXISTS `recipient` (
  `recipient_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `blood_type` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
  `medical_condition` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`recipient_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `recipient_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.recipient: ~5 rows (approximately)
INSERT IGNORE INTO `recipient` (`recipient_id`, `user_id`, `blood_type`, `medical_condition`) VALUES
	(1, 7, 'O+', 'Cardiac surgery'),
	(2, 8, 'A+', 'Pregnancy complication');

-- Dumping structure for procedure bbms_se.RegisterDonation
DELIMITER //
CREATE PROCEDURE `RegisterDonation`(
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
DELIMITER ;

-- Dumping structure for procedure bbms_se.RejectBloodRequest
DELIMITER //
CREATE PROCEDURE `RejectBloodRequest`(
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
DELIMITER ;

-- Dumping structure for procedure bbms_se.UpdateExpiredBloodUnits
DELIMITER //
CREATE PROCEDURE `UpdateExpiredBloodUnits`()
BEGIN
    UPDATE BloodUnit
    SET status = 'Expired'
    WHERE expiry_date < CURDATE()
      AND status = 'Available';

    SELECT ROW_COUNT() AS expired_units_updated;
END//
DELIMITER ;

-- Dumping structure for table bbms_se.useraccount
CREATE TABLE IF NOT EXISTS `useraccount` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(80) NOT NULL,
  `last_name` varchar(80) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` enum('Male','Female','Other') DEFAULT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `role` enum('Administrator','HospitalStaff','Donor','Recipient') NOT NULL,
  `account_status` enum('Active','Locked','Inactive') DEFAULT 'Active',
  `failed_login_attempts` int(11) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_user_email` (`email`),
  KEY `idx_user_role` (`role`),
  CONSTRAINT `CONSTRAINT_1` CHECK (`age` is null or `age` between 1 and 120)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Dumping data for table bbms_se.useraccount: ~23 rows (approximately)
INSERT IGNORE INTO `useraccount` (`user_id`, `first_name`, `last_name`, `age`, `gender`, `email`, `password_hash`, `phone`, `role`, `account_status`, `failed_login_attempts`, `created_at`) VALUES
	(1, 'Admin', 'User', 35, 'Other', 'admin@bbms.com', 'password123', '+96170000001', 'Administrator', 'Active', 0, '2026-05-15 01:37:39'),
	(2, 'Lina', 'Mansour', 31, 'Female', 'lina.staff@bbms.com', 'password123', '+96170000002', 'HospitalStaff', 'Active', 0, '2026-05-15 01:37:39'),
	(3, 'Karim', 'Fares', 34, 'Male', 'karim.staff@bbms.com', 'password123', '+96170000003', 'HospitalStaff', 'Active', 0, '2026-05-15 01:37:39'),
	(4, 'Ali', 'Mohamad', 28, 'Male', 'ali.donor@bbms.com', 'password123', '+96170111111', 'Donor', 'Active', 0, '2026-05-15 01:37:39'),
	(5, 'Fatima', 'Hasan', 35, 'Female', 'fatima.donor@bbms.com', 'password123', '+96171222222', 'Donor', 'Active', 0, '2026-05-15 01:37:39'),
	(6, 'Nadia', 'Ghosn', 27, 'Female', 'nadia.donor@bbms.com', 'password123', '+96171333333', 'Donor', 'Active', 0, '2026-05-15 01:37:39'),
	(7, 'Marwan', 'Tabbara', 52, 'Male', 'marwan.recipient@bbms.com', 'password123', '+96170201010', 'Recipient', 'Active', 0, '2026-05-15 01:37:39'),
	(8, 'Salma', 'Harb', 28, 'Female', 'salma.recipient@bbms.com', 'password123', '+96171202020', 'Recipient', 'Active', 0, '2026-05-15 01:37:39');

-- Dumping structure for view bbms_se.vw_appointments
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_appointments` (
	`appointment_id` INT(11) NOT NULL,
	`appointment_datetime` DATETIME NOT NULL,
	`status` ENUM('Scheduled','Completed','Cancelled') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`eligibility_snapshot` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`notes` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`donor_id` INT(11) NOT NULL,
	`donor_name` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`hospital_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`location` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci'
);

-- Dumping structure for view bbms_se.vw_blood_inventory
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_blood_inventory` (
	`blood_unit_id` INT(11) NOT NULL,
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`component_type` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`quantity_ml` INT(11) NOT NULL,
	`donation_date` DATE NOT NULL,
	`expiry_date` DATE NOT NULL,
	`days_until_expiry` INT(8) NULL,
	`status` ENUM('Available','Reserved','Used','Expired') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`hospital_id` INT(11) NOT NULL,
	`hospital_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`location` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`donor_id` INT(11) NULL,
	`donor_name` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci'
);

-- Dumping structure for view bbms_se.vw_blood_requests
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_blood_requests` (
	`request_id` INT(11) NOT NULL,
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`quantity_needed_ml` INT(11) NOT NULL,
	`priority_level` ENUM('Low','Medium','High','Critical') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`status` ENUM('Pending','Approved','Rejected','Cancelled','Fulfilled') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`request_date` DATETIME NULL,
	`hospital_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`location` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`recipient_id` INT(11) NOT NULL,
	`recipient_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`recipient_email` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`blood_unit_id` INT(11) NULL
);

-- Dumping structure for view bbms_se.vw_donation_history
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_donation_history` (
	`donation_id` INT(11) NOT NULL,
	`donation_date` DATE NOT NULL,
	`status` ENUM('Pending','Processed','Rejected') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`donor_id` INT(11) NOT NULL,
	`donor_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`hospital_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`quantity_ml` INT(11) NULL,
	`expiry_date` DATE NULL,
	`recorded_by` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci'
);

-- Dumping structure for view bbms_se.vw_donor_profiles
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_donor_profiles` (
	`donor_id` INT(11) NOT NULL,
	`user_id` INT(11) NOT NULL,
	`first_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`last_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`full_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`email` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`phone` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`age` INT(11) NULL,
	`gender` ENUM('Male','Female','Other') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`health_status` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`weight_kg` DECIMAL(5,2) NULL,
	`medication_restricted` TINYINT(1) NULL,
	`last_donation_date` DATE NULL,
	`eligibility_status` ENUM('Eligible','TemporarilyDeferred','PermanentlyDeferred') NULL COLLATE 'utf8mb4_uca1400_ai_ci'
);

-- Dumping structure for view bbms_se.vw_recipient_profiles
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `vw_recipient_profiles` (
	`recipient_id` INT(11) NOT NULL,
	`user_id` INT(11) NOT NULL,
	`full_name` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`email` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`phone` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`age` INT(11) NULL,
	`gender` ENUM('Male','Female','Other') NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`blood_type` ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL COLLATE 'utf8mb4_uca1400_ai_ci',
	`medical_condition` VARCHAR(1) NULL COLLATE 'utf8mb4_uca1400_ai_ci'
);

-- Dumping structure for trigger bbms_se.trg_after_appointment_insert
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_after_blood_request_insert
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_after_blood_request_update
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_after_blood_unit_insert
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_after_donation_insert
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_after_donor_update
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Dumping structure for trigger bbms_se.trg_before_blood_unit_insert
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
DELIMITER //
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
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_appointments`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_appointments` AS SELECT
    a.appointment_id,
    a.appointment_datetime,
    a.status,
    a.eligibility_snapshot,
    a.notes,
    d.donor_id,
    CONCAT(u.first_name, ' ', u.last_name) AS donor_name,
    d.blood_type,
    h.hospital_name,
    h.location
FROM Appointment a
JOIN Donor d ON a.donor_id = d.donor_id
JOIN UserAccount u ON d.user_id = u.user_id
JOIN Hospital h ON a.hospital_id = h.hospital_id 
;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_blood_inventory`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_blood_inventory` AS SELECT
    b.blood_unit_id,
    b.blood_type,
    b.component_type,
    b.quantity_ml,
    b.donation_date,
    b.expiry_date,
    DATEDIFF(b.expiry_date, CURDATE()) AS days_until_expiry,
    b.status,
    h.hospital_id,
    h.hospital_name,
    h.location,
    d.donor_id,
    CONCAT(u.first_name, ' ', u.last_name) AS donor_name
FROM BloodUnit b
JOIN Hospital h ON b.hospital_id = h.hospital_id
LEFT JOIN Donor d ON b.donor_id = d.donor_id
LEFT JOIN UserAccount u ON d.user_id = u.user_id 
;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_blood_requests`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_blood_requests` AS SELECT
    br.request_id,
    br.blood_type,
    br.quantity_needed_ml,
    br.priority_level,
    br.status,
    br.request_date,
    h.hospital_name,
    h.location,
    r.recipient_id,
    CONCAT(u.first_name, ' ', u.last_name) AS recipient_name,
    u.email AS recipient_email,
    bu.blood_unit_id
FROM BloodRequest br
JOIN Recipient r ON br.recipient_id = r.recipient_id
JOIN UserAccount u ON r.user_id = u.user_id
JOIN Hospital h ON br.hospital_id = h.hospital_id
LEFT JOIN BloodUnit bu ON br.blood_unit_id = bu.blood_unit_id 
;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_donation_history`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_donation_history` AS SELECT
    dn.donation_id,
    dn.donation_date,
    dn.status,
    d.donor_id,
    CONCAT(du.first_name, ' ', du.last_name) AS donor_name,
    h.hospital_name,
    b.blood_type,
    b.quantity_ml,
    b.expiry_date,
    CONCAT(su.first_name, ' ', su.last_name) AS recorded_by
FROM Donation dn
JOIN Donor d ON dn.donor_id = d.donor_id
JOIN UserAccount du ON d.user_id = du.user_id
JOIN Hospital h ON dn.hospital_id = h.hospital_id
LEFT JOIN BloodUnit b ON dn.blood_unit_id = b.blood_unit_id
LEFT JOIN HospitalStaff hs ON dn.staff_id = hs.staff_id
LEFT JOIN UserAccount su ON hs.user_id = su.user_id 
;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_donor_profiles`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_donor_profiles` AS SELECT
    d.donor_id,
    u.user_id,
    u.first_name,
    u.last_name,
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.email,
    u.phone,
    u.age,
    u.gender,
    d.blood_type,
    d.health_status,
    d.weight_kg,
    d.medication_restricted,
    d.last_donation_date,
    d.eligibility_status
FROM Donor d
JOIN UserAccount u ON d.user_id = u.user_id 
;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `vw_recipient_profiles`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_recipient_profiles` AS SELECT
    r.recipient_id,
    u.user_id,
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.email,
    u.phone,
    u.age,
    u.gender,
    r.blood_type,
    r.medical_condition
FROM Recipient r
JOIN UserAccount u ON r.user_id = u.user_id 
;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
