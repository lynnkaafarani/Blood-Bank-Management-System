-- =====================================================
-- Blood Bank Management System - 3NF SRS Version
-- =====================================================

DROP DATABASE IF EXISTS BBMS_SE;
CREATE DATABASE BBMS_SE;
USE BBMS_SE;

-- =========================
-- USER ACCOUNT
-- =========================
CREATE TABLE UserAccount (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    role ENUM('Administrator', 'HospitalStaff', 'Donor', 'Recipient') NOT NULL,
    account_status ENUM('Active', 'Locked', 'Inactive') DEFAULT 'Active',
    failed_login_attempts INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CHECK (age IS NULL OR age BETWEEN 1 AND 120)
);

CREATE TABLE Hospital (
    hospital_id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_name VARCHAR(150) NOT NULL,
    location VARCHAR(200) NOT NULL,
    contact_info VARCHAR(100) NOT NULL
);

CREATE TABLE HospitalStaff (
    staff_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    hospital_id INT NOT NULL,
    staff_role VARCHAR(80) NOT NULL,

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Donor (
    donor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    health_status VARCHAR(100) DEFAULT 'Healthy',
    weight_kg DECIMAL(5,2),
    medication_restricted BOOLEAN DEFAULT FALSE,
    last_donation_date DATE,
    eligibility_status ENUM('Eligible', 'TemporarilyDeferred', 'PermanentlyDeferred') DEFAULT 'Eligible',
    deferral_reason VARCHAR(255),

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CHECK (weight_kg IS NULL OR weight_kg > 0)
);

CREATE TABLE Recipient (
    recipient_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    medical_condition VARCHAR(255),

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE BloodUnit (
    blood_unit_id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_id INT NOT NULL,
    donor_id INT,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    component_type VARCHAR(50) DEFAULT 'Whole Blood',
    quantity_ml INT NOT NULL,
    donation_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('Available', 'Reserved', 'Used', 'Expired') DEFAULT 'Available',

    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CHECK (quantity_ml > 0),
    CHECK (expiry_date > donation_date)
);

CREATE TABLE Donation (
    donation_id INT PRIMARY KEY AUTO_INCREMENT,
    donor_id INT NOT NULL,
    staff_id INT,
    hospital_id INT NOT NULL,
    blood_unit_id INT UNIQUE,
    donation_date DATE NOT NULL,
    status ENUM('Pending', 'Processed', 'Rejected') DEFAULT 'Pending',

    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (staff_id) REFERENCES HospitalStaff(staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (blood_unit_id) REFERENCES BloodUnit(blood_unit_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE BloodRequest (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    recipient_id INT NOT NULL,
    hospital_id INT NOT NULL,
    processed_by_staff_id INT,
    blood_unit_id INT,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    quantity_needed_ml INT NOT NULL,
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    priority_level ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    status ENUM('Pending', 'Approved', 'Rejected', 'Cancelled', 'Fulfilled') DEFAULT 'Pending',

    FOREIGN KEY (recipient_id) REFERENCES Recipient(recipient_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (processed_by_staff_id) REFERENCES HospitalStaff(staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    FOREIGN KEY (blood_unit_id) REFERENCES BloodUnit(blood_unit_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CHECK (quantity_needed_ml > 0)
);

CREATE TABLE Appointment (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    donor_id INT NOT NULL,
    hospital_id INT NOT NULL,
    appointment_datetime DATETIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    eligibility_snapshot VARCHAR(100),
    notes VARCHAR(255),

    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Notification (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    message VARCHAR(255) NOT NULL,
    notification_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    type ENUM('Info', 'Appointment', 'Request', 'Shortage', 'System') DEFAULT 'Info',
    is_read BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ActivityLog (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action_type VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80),
    entity_id INT,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE AuthSession (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,

    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_user_email ON UserAccount(email);
CREATE INDEX idx_user_role ON UserAccount(role);
CREATE INDEX idx_blood_type_status ON BloodUnit(blood_type, status);
CREATE INDEX idx_request_status ON BloodRequest(status);
CREATE INDEX idx_notification_user ON Notification(user_id);

SELECT '3NF BloodBank_SRS_DB schema created successfully' AS message;