USE BBMS_SE;

DROP VIEW IF EXISTS vw_donor_profiles;
CREATE VIEW vw_donor_profiles AS
SELECT
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
JOIN UserAccount u ON d.user_id = u.user_id;


DROP VIEW IF EXISTS vw_recipient_profiles;
CREATE VIEW vw_recipient_profiles AS
SELECT
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
JOIN UserAccount u ON r.user_id = u.user_id;


DROP VIEW IF EXISTS vw_blood_inventory;
CREATE VIEW vw_blood_inventory AS
SELECT
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
LEFT JOIN UserAccount u ON d.user_id = u.user_id;


DROP VIEW IF EXISTS vw_blood_requests;
CREATE VIEW vw_blood_requests AS
SELECT
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
LEFT JOIN BloodUnit bu ON br.blood_unit_id = bu.blood_unit_id;


DROP VIEW IF EXISTS vw_donation_history;
CREATE VIEW vw_donation_history AS
SELECT
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
LEFT JOIN UserAccount su ON hs.user_id = su.user_id;


DROP VIEW IF EXISTS vw_appointments;
CREATE VIEW vw_appointments AS
SELECT
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
JOIN Hospital h ON a.hospital_id = h.hospital_id;


SELECT 'SRS 3NF views created successfully' AS message;