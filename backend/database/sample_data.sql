USE BBMS_SE;

-- =====================================================
-- SAMPLE DATA - 3NF SRS VERSION
-- Password for all users: password123
-- NOTE: password_hash is sample text for now.
-- =====================================================

-- Hospitals
INSERT INTO Hospital (hospital_name, location, contact_info) VALUES
('Rafik Hariri University Hospital', 'Beirut, Lebanon', '+961-1-830000'),
('American University of Beirut Medical Center', 'Hamra, Beirut', '+961-1-350000'),
('Hotel Dieu de France Hospital', 'Achrafieh, Beirut', '+961-1-615300');

-- Users
INSERT INTO UserAccount
(first_name, last_name, age, gender, email, password_hash, phone, role)
VALUES
('Admin', 'User', 35, 'Other', 'admin@bbms.com', 'password123', '+96170000001', 'Administrator'),

('Lina', 'Mansour', 31, 'Female', 'lina.staff@bbms.com', 'password123', '+96170000002', 'HospitalStaff'),
('Karim', 'Fares', 34, 'Male', 'karim.staff@bbms.com', 'password123', '+96170000003', 'HospitalStaff'),

('Ali', 'Mohamad', 28, 'Male', 'ali.donor@bbms.com', 'password123', '+96170111111', 'Donor'),
('Fatima', 'Hasan', 35, 'Female', 'fatima.donor@bbms.com', 'password123', '+96171222222', 'Donor'),
('Nadia', 'Ghosn', 27, 'Female', 'nadia.donor@bbms.com', 'password123', '+96171333333', 'Donor'),

('Marwan', 'Tabbara', 52, 'Male', 'marwan.recipient@bbms.com', 'password123', '+96170201010', 'Recipient'),
('Salma', 'Harb', 28, 'Female', 'salma.recipient@bbms.com', 'password123', '+96171202020', 'Recipient');

-- Staff profiles
INSERT INTO HospitalStaff (user_id, hospital_id, staff_role) VALUES
(2, 1, 'Lab Technician'),
(3, 2, 'Nurse');

-- Donor profiles
INSERT INTO Donor
(user_id, blood_type, health_status, weight_kg, medication_restricted, last_donation_date, eligibility_status)
VALUES
(4, 'O+', 'Healthy', 70.5, FALSE, '2025-10-10', 'Eligible'),
(5, 'A+', 'Healthy', 62.0, FALSE, '2025-08-20', 'Eligible'),
(6, 'O-', 'Healthy', 58.0, FALSE, NULL, 'Eligible');

-- Recipient profiles
INSERT INTO Recipient
(user_id, blood_type, medical_condition)
VALUES
(7, 'O+', 'Cardiac surgery'),
(8, 'A+', 'Pregnancy complication');

-- Blood units
INSERT INTO BloodUnit
(hospital_id, donor_id, blood_type, component_type, quantity_ml, donation_date, expiry_date, status)
VALUES
(1, 1, 'O+', 'Whole Blood', 450, '2026-04-01', '2026-05-15', 'Available'),
(1, 2, 'A+', 'Whole Blood', 450, '2026-04-05', '2026-05-20', 'Available'),
(2, 3, 'O-', 'Whole Blood', 450, '2026-04-10', '2026-05-25', 'Available');

-- Donations
INSERT INTO Donation
(donor_id, staff_id, hospital_id, blood_unit_id, donation_date, status)
VALUES
(1, 1, 1, 1, '2026-04-01', 'Processed'),
(2, 1, 1, 2, '2026-04-05', 'Processed'),
(3, 2, 2, 3, '2026-04-10', 'Processed');

-- Blood requests
INSERT INTO BloodRequest
(recipient_id, hospital_id, blood_type, quantity_needed_ml, priority_level, status)
VALUES
(1, 1, 'O+', 400, 'High', 'Pending'),
(2, 1, 'A+', 350, 'Critical', 'Pending');

-- Appointments
INSERT INTO Appointment
(donor_id, hospital_id, appointment_datetime, status, eligibility_snapshot, notes)
VALUES
(1, 1, '2026-05-05 10:00:00', 'Scheduled', 'Eligible', 'Routine donation appointment'),
(2, 2, '2026-05-06 11:00:00', 'Scheduled', 'Eligible', 'Routine donation appointment');

-- Notifications
INSERT INTO Notification
(user_id, message, type)
VALUES
(4, 'Urgent O+ blood shortage reported at Rafik Hariri University Hospital.', 'Shortage'),
(7, 'Your blood request has been submitted successfully.', 'Request');

-- Activity logs
INSERT INTO ActivityLog
(user_id, action_type, entity_type, entity_id, description)
VALUES
(1, 'CREATE', 'Hospital', 1, 'Initial hospital data inserted.'),
(2, 'CREATE', 'BloodUnit', 1, 'Blood unit added to inventory.');

SELECT 'Sample data inserted successfully' AS message;