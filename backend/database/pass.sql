-- ============================================
-- ELMS Database Setup Script
-- Run this first to create database and tables
-- ============================================

CREATE DATABASE IF NOT EXISTS proj_db;

USE proj_db;

-- ============================================
-- CREATE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS TEAM (
    TeamID INT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS STUDENT (
    StudentID INT PRIMARY KEY,
    Major VARCHAR(100),
    TeamID INT,
    FOREIGN KEY (TeamID) REFERENCES TEAM(TeamID)
);

CREATE TABLE IF NOT EXISTS EXPERIMENT (
    ExperimentID INT PRIMARY KEY,
    Title VARCHAR(200),
    Description TEXT,
    InstructorName VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS EQUIPMENT (
    EquipmentID INT PRIMARY KEY,
    Name VARCHAR(100),
    Status VARCHAR(50),
    NextCalibrationDue DATE,
    LastCalibrationDue DATE
);

CREATE TABLE IF NOT EXISTS COMPONENT (
    ComponentID INT PRIMARY KEY,
    Name VARCHAR(100),
    QuantityOnHand INT,
    ReorderPoint INT,
    Location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS TEAM_EXPERIMENT (
    TeamID INT,
    ExperimentID INT,
    Date DATETIME,
    PRIMARY KEY (TeamID, ExperimentID),
    FOREIGN KEY (TeamID) REFERENCES TEAM(TeamID),
    FOREIGN KEY (ExperimentID) REFERENCES EXPERIMENT(ExperimentID)
);

CREATE TABLE IF NOT EXISTS EXPERIMENT_CE (
    ExperimentID INT,
    ComponentID INT,
    EquipmentID INT,
    QuantityRequired INT,
    PRIMARY KEY (ExperimentID, ComponentID, EquipmentID),
    FOREIGN KEY (ExperimentID) REFERENCES EXPERIMENT(ExperimentID),
    FOREIGN KEY (ComponentID) REFERENCES COMPONENT(ComponentID),
    FOREIGN KEY (EquipmentID) REFERENCES EQUIPMENT(EquipmentID)
);

CREATE TABLE IF NOT EXISTS COMPONENT_USAGE (
    ComponentID INT,
    TeamID INT,
    ExperimentID INT,
    Quantity INT,
    IsReturned BOOLEAN,
    PRIMARY KEY (ComponentID, TeamID, ExperimentID),
    FOREIGN KEY (ComponentID) REFERENCES COMPONENT(ComponentID),
    FOREIGN KEY (TeamID, ExperimentID)
        REFERENCES TEAM_EXPERIMENT(TeamID, ExperimentID)
);

CREATE TABLE IF NOT EXISTS EQUIPMENT_RESERVATION (
    ReservationID INT PRIMARY KEY,
    TeamID INT,
    ExperimentID INT,
    EquipmentID INT,
    StartDateTime DATETIME,
    EndDateTime DATETIME,
    Status VARCHAR(50),
    FOREIGN KEY (EquipmentID) REFERENCES EQUIPMENT(EquipmentID),
    FOREIGN KEY (TeamID, ExperimentID)
        REFERENCES TEAM_EXPERIMENT(TeamID, ExperimentID)
);

-- ============================================
-- CREATE STORED PROCEDURES
-- ============================================

-- Transaction #1: Reserve Equipment
DELIMITER $$

DROP PROCEDURE IF EXISTS ReserveEquipment;

CREATE PROCEDURE ReserveEquipment(
    IN p_ReservationID INT,
    IN p_TeamID INT,
    IN p_ExperimentID INT,
    IN p_EquipmentID INT,
    IN p_Start DATETIME,
    IN p_End DATETIME
)
BEGIN
    DECLARE equipment_status VARCHAR(50);
    START TRANSACTION;
    
    -- Lock the equipment row to prevent conflicts
    SELECT Status INTO equipment_status
    FROM EQUIPMENT
    WHERE EquipmentID = p_EquipmentID
    FOR UPDATE;
    
    -- If equipment is not available → rollback
    IF equipment_status <> 'Available' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Equipment is not available for reservation.';
    END IF;
    
    -- Insert reservation
    INSERT INTO EQUIPMENT_RESERVATION (
        ReservationID, TeamID, ExperimentID, EquipmentID,
        StartDateTime, EndDateTime, Status
    ) VALUES (
        p_ReservationID, p_TeamID, p_ExperimentID, p_EquipmentID,
        p_Start, p_End, 'Active'
    );
    
    -- Update equipment status
    UPDATE EQUIPMENT
    SET Status = 'In Use'
    WHERE EquipmentID = p_EquipmentID;
    
    COMMIT;
END$$

-- Transaction #2: Use Component
DROP PROCEDURE IF EXISTS UseComponent;

CREATE PROCEDURE UseComponent(
    IN p_ComponentID INT,
    IN p_TeamID INT,
    IN p_ExperimentID INT,
    IN p_Quantity INT
)
BEGIN
    DECLARE current_qty INT;
    START TRANSACTION;
    
    -- Lock component row
    SELECT QuantityOnHand INTO current_qty
    FROM COMPONENT
    WHERE ComponentID = p_ComponentID
    FOR UPDATE;
    
    -- If not enough stock → rollback
    IF current_qty < p_Quantity THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not enough inventory to complete component usage.';
    END IF;
    
    -- Insert usage record
    INSERT INTO COMPONENT_USAGE (
        ComponentID, TeamID, ExperimentID, Quantity, IsReturned
    ) VALUES (
        p_ComponentID, p_TeamID, p_ExperimentID, p_Quantity, FALSE
    );
    
    -- Update inventory
    UPDATE COMPONENT
    SET QuantityOnHand = QuantityOnHand - p_Quantity
    WHERE ComponentID = p_ComponentID;
    
    COMMIT;
END$$

DELIMITER ;

-- ============================================
-- INSERT SEED DATA
-- ============================================

INSERT INTO TEAM (TeamID) VALUES
(1`equipmentcomponent_usagecomponent`), (2), (3);

INSERT INTO STUDENT (StudentID, Major, TeamID) VALUES
(101, 'Electrical Engineering', 1),
(102, 'Computer Engineering', 1),
(103, 'Electrical Engineering', 2),
(104, 'Biomedical Engineering', 2),
(105, 'Computer Engineering', 3);

INSERT INTO EXPERIMENT (ExperimentID, Title, Description, InstructorName) VALUES
(10, 'Ohm Law Verification', 'Measure voltage and current to verify Ohm\'s Law.', 'Dr. Helen Saad'),
(11, 'RC Circuits', 'Analyze charging and discharging of capacitors.', 'Dr. Helen Saad'),
(12, 'Op-Amp Applications', 'Study inverting and non-inverting amplifiers.', 'Dr. Karim Youssef');

INSERT INTO COMPONENT (ComponentID, Name, QuantityOnHand, ReorderPoint, Location) VALUES
(201, 'Resistor 1kΩ', 500, 100, 'Drawer A1'),
(202, 'Capacitor 100uF', 120, 30, 'Drawer A2'),
(203, 'Op-Amp LM741', 40, 15, 'Cabinet B1'),
(204, 'Breadboard', 20, 5, 'Shelf C1'),
(205, 'Jumper Wires Pack', 60, 20, 'Drawer A3');

INSERT INTO EQUIPMENT (EquipmentID, Name, Status, NextCalibrationDue, LastCalibrationDue) VALUES
(301, 'Multimeter', 'Available', '2025-12-01', '2024-12-01'),
(302, 'Oscilloscope', 'In Use', '2025-08-15', '2024-08-15'),
(303, 'Function Generator', 'Available', '2025-09-20', '2024-09-20'),
(304, 'DC Power Supply', 'Under Maintenance', '2025-10-05', '2024-10-05');

INSERT INTO TEAM_EXPERIMENT (TeamID, ExperimentID, Date) VALUES
(1, 10, '2025-02-01 10:00:00'),
(1, 11, '2025-02-05 14:00:00'),
(2, 10, '2025-02-03 09:30:00'),
(2, 12, '2025-02-10 15:00:00'),
(3, 11, '2025-02-07 13:00:00');

INSERT INTO EXPERIMENT_CE (ExperimentID, ComponentID, EquipmentID, QuantityRequired) VALUES
(10, 201, 301, 5),
(10, 205, 301, 1),
(11, 202, 302, 2),
(11, 204, 302, 1),
(12, 203, 303, 1);

INSERT INTO COMPONENT_USAGE (ComponentID, TeamID, ExperimentID, Quantity, IsReturned) VALUES
(201, 1, 10, 4, TRUE),
(205, 1, 10, 1, TRUE),
(202, 1, 11, 2, FALSE),
(204, 1, 11, 1, TRUE),
(201, 2, 10, 6, TRUE),
(203, 2, 12, 1, FALSE),
(202, 3, 11, 3, TRUE);

INSERT INTO EQUIPMENT_RESERVATION (ReservationID, TeamID, ExperimentID, EquipmentID, StartDateTime, EndDateTime, Status) VALUES
(1, 1, 10, 301, '20component_usagestudent25-02-01 09:00:00', '2025-02-01 11:00:00', 'Completed'),
(2, 1, 11, 302, '2025-02-05 13:30:00', '2025-02-05 16:00:00', 'Active'),
(3, 2, 10, 301, '2025-02-03 08:30:00', '2025-02-03 10:00:00', 'Completed'),
(4, 2, 12, 303, '2025-02-10 14:30:00', '2025-02-10 17:00:00', 'Active'),
(5, 3, 11, 302, '2025-02-07 12:00:00', '2025-02-07 15:00:00', 'Completed');
