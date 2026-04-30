from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from config import Config
import os
app = Flask(__name__)
CORS(app)


def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


def query_db(query, params=None, fetch=True):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            data = cursor.fetchall()
        else:
            conn.commit()
            data = cursor.lastrowid

        cursor.close()
        return data

    except Error as e:
        print("Database error:", e)
        return None

    finally:
        if conn:
            conn.close()


@app.route("/")
def home():
    return jsonify({"message": "BBMS_SE backend running"})


@app.route("/api/test-db")
def test_db():
    return jsonify({"success": True, "tables": query_db("SHOW TABLES")})


# =====================================================
# AUTH / LOGIN
# =====================================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password")

    user = query_db("""
        SELECT user_id, first_name, last_name, email, role, password_hash, account_status
        FROM UserAccount
        WHERE email = %s
    """, (email,))

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    user = user[0]

    if user["account_status"] != "Active":
        return jsonify({"success": False, "message": "Account is not active"}), 403

    if user["password_hash"] != password:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "user_id": user["user_id"],
            "full_name": f"{user['first_name']} {user['last_name']}",
            "email": user["email"],
            "role": user["role"]
        }
    })


# =====================================================
# ADMIN REQUIREMENTS
# =====================================================

@app.route("/api/users")
def get_users():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT user_id, first_name, last_name, email, phone, role, account_status
            FROM UserAccount
            ORDER BY user_id
        """)
    })


@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT hospital_id, hospital_name, location, contact_info
            FROM Hospital
            ORDER BY hospital_name
        """)
    })


@app.route("/api/hospitals", methods=["POST"])
def add_hospital():
    data = request.json or {}

    hospital_id = query_db("""
        INSERT INTO Hospital (hospital_name, location, contact_info)
        VALUES (%s, %s, %s)
    """, (
        data.get("hospital_name"),
        data.get("location"),
        data.get("contact_info")
    ), fetch=False)

    return jsonify({"success": True, "hospital_id": hospital_id})


@app.route("/api/activity-logs")
def get_activity_logs():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT log_id, user_id, action_type, entity_type, entity_id, description, created_at
            FROM ActivityLog
            ORDER BY created_at DESC
        """)
    })


# =====================================================
# DONORS
# =====================================================

@app.route("/api/donors")
def get_donors():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_donor_profiles ORDER BY donor_id")
    })


@app.route("/api/donors/<int:donor_id>/history")
def donor_history(donor_id):
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT *
            FROM vw_donation_history
            WHERE donor_id = %s
            ORDER BY donation_date DESC
        """, (donor_id,))
    })


@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_appointments ORDER BY appointment_datetime DESC")
    })


@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    data = request.json or {}

    appointment_id = query_db("""
        INSERT INTO Appointment
        (donor_id, hospital_id, appointment_datetime, status, eligibility_snapshot, notes)
        VALUES (%s, %s, %s, 'Scheduled', %s, %s)
    """, (
        data.get("donor_id"),
        data.get("hospital_id"),
        data.get("appointment_datetime"),
        data.get("eligibility_snapshot", "Eligible"),
        data.get("notes", "")
    ), fetch=False)

    return jsonify({"success": True, "appointment_id": appointment_id})


# =====================================================
# RECIPIENTS
# =====================================================

@app.route("/api/recipients")
def get_recipients():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_recipient_profiles ORDER BY recipient_id")
    })


# =====================================================
# BLOOD INVENTORY
# =====================================================

@app.route("/api/blood-inventory")
def blood_inventory():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_blood_inventory ORDER BY expiry_date ASC")
    })


@app.route("/api/blood-units", methods=["POST"])
def add_blood_unit():
    data = request.json or {}

    blood_unit_id = query_db("""
        INSERT INTO BloodUnit
        (hospital_id, donor_id, blood_type, component_type, quantity_ml, donation_date, expiry_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Available')
    """, (
        data.get("hospital_id"),
        data.get("donor_id"),
        data.get("blood_type"),
        data.get("component_type", "Whole Blood"),
        data.get("quantity_ml"),
        data.get("donation_date"),
        data.get("expiry_date")
    ), fetch=False)
    if blood_unit_id is None:
        return jsonify({"success": False, "message": "Failed to add blood unit"}), 400

    return jsonify({"success": True, "blood_unit_id": blood_unit_id})


@app.route("/api/blood-units/<int:blood_unit_id>", methods=["DELETE"])
def delete_blood_unit(blood_unit_id):
    query_db("""
        DELETE FROM BloodUnit
        WHERE blood_unit_id = %s
    """, (blood_unit_id,), fetch=False)

    return jsonify({"success": True, "message": "Blood unit deleted"})


# =====================================================
# DONATIONS / STORED PROCEDURE
# =====================================================

@app.route("/api/donations")
def get_donations():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_donation_history ORDER BY donation_date DESC")
    })


@app.route("/api/donations/register", methods=["POST"])
def register_donation():
    data = request.json or {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        args = [
            data.get("donor_id"),
            data.get("staff_id"),
            data.get("hospital_id"),
            data.get("blood_type"),
            data.get("quantity_ml"),
            0,
            0
        ]

        result_args = cursor.callproc("RegisterDonation", args)
        conn.commit()

        return jsonify({
            "success": True,
            "donation_id": result_args[5],
            "blood_unit_id": result_args[6]
        })

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()


# =====================================================
# BLOOD REQUESTS
# =====================================================

@app.route("/api/blood-requests")
def get_blood_requests():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_blood_requests ORDER BY request_date DESC")
    })


@app.route("/api/blood-requests", methods=["POST"])
def create_blood_request():
    data = request.json or {}

    request_id = query_db("""
        INSERT INTO BloodRequest
        (recipient_id, hospital_id, blood_type, quantity_needed_ml, priority_level, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """, (
        data.get("recipient_id"),
        data.get("hospital_id"),
        data.get("blood_type"),
        data.get("quantity_needed_ml"),
        data.get("priority_level", "Medium")
    ), fetch=False)

    return jsonify({"success": True, "request_id": request_id})


@app.route("/api/blood-requests/<int:request_id>/fulfill", methods=["POST"])
def fulfill_request(request_id):
    data = request.json or {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.callproc("ProcessBloodRequest", [
            request_id,
            data.get("blood_unit_id"),
            data.get("staff_id")
        ])

        conn.commit()
        return jsonify({"success": True, "message": "Blood request fulfilled"})

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()


@app.route("/api/blood-requests/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id):
    data = request.json or {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.callproc("RejectBloodRequest", [
            request_id,
            data.get("staff_id"),
            data.get("reason", "Request rejected by hospital staff")
        ])

        conn.commit()
        return jsonify({"success": True, "message": "Blood request rejected"})

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()


@app.route("/api/blood-requests/<int:request_id>/cancel", methods=["PUT"])
def cancel_request(request_id):
    query_db("""
        UPDATE BloodRequest
        SET status = 'Cancelled'
        WHERE request_id = %s AND status = 'Pending'
    """, (request_id,), fetch=False)

    return jsonify({"success": True, "message": "Request cancelled"})


# =====================================================
# NOTIFICATIONS
# =====================================================

@app.route("/api/notifications/<int:user_id>")
def get_notifications(user_id):
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT notification_id, message, notification_date, type, is_read
            FROM Notification
            WHERE user_id = %s
            ORDER BY notification_date DESC
        """, (user_id,))
    })


@app.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_notification_read(notification_id):
    query_db("""
        UPDATE Notification
        SET is_read = TRUE
        WHERE notification_id = %s
    """, (notification_id,), fetch=False)

    return jsonify({"success": True, "message": "Notification marked as read"})

# =====================================================
# MAINTENANCE
# =====================================================

@app.route("/api/update-expired-blood", methods=["POST"])
def update_expired_blood():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("UpdateExpiredBloodUnits")
        conn.commit()

        return jsonify({"success": True, "message": "Expired blood units updated"})

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()

# =====================================================
# STAFF-SPECIFIC ENDPOINTS
# =====================================================

@app.route("/api/staff/<int:user_id>/profile")
def staff_profile(user_id):
    data = query_db("""
        SELECT 
            hs.staff_id,
            hs.user_id,
            hs.hospital_id,
            hs.staff_role,
            h.hospital_name
        FROM HospitalStaff hs
        JOIN Hospital h ON hs.hospital_id = h.hospital_id
        WHERE hs.user_id = %s
    """, (user_id,))

    if not data:
        return jsonify({"success": False, "message": "Staff profile not found"}), 404

    return jsonify({"success": True, "data": data[0]})


@app.route("/api/staff/<int:user_id>/inventory")
def staff_inventory(user_id):
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT bi.*
            FROM vw_blood_inventory bi
            JOIN HospitalStaff hs ON bi.hospital_id = hs.hospital_id
            WHERE hs.user_id = %s
            ORDER BY bi.expiry_date ASC
        """, (user_id,))
    })


@app.route("/api/staff/<int:user_id>/requests")
def staff_requests(user_id):
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT br.*
            FROM vw_blood_requests br
            JOIN HospitalStaff hs ON br.hospital_name = (
                SELECT hospital_name
                FROM Hospital
                WHERE hospital_id = hs.hospital_id
            )
            WHERE hs.user_id = %s
            ORDER BY br.request_date DESC
        """, (user_id,))
    })


@app.route("/api/blood-units/<int:blood_unit_id>", methods=["PUT"])
def edit_blood_unit(blood_unit_id):
    data = request.json or {}

    query_db("""
        UPDATE BloodUnit
        SET quantity_ml = %s,
            expiry_date = %s,
            status = %s
        WHERE blood_unit_id = %s
    """, (
        data.get("quantity_ml"),
        data.get("expiry_date"),
        data.get("status"),
        blood_unit_id
    ), fetch=False)

    return jsonify({"success": True, "message": "Blood unit updated successfully"})


@app.route("/api/staff/register-donation", methods=["POST"])
def staff_register_donation():
    data = request.json or {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        args = [
            data.get("donor_id"),
            data.get("staff_id"),
            data.get("hospital_id"),
            data.get("blood_type"),
            data.get("quantity_ml"),
            0,
            0
        ]

        result = cursor.callproc("RegisterDonation", args)
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Donation registered successfully",
            "donation_id": result[5],
            "blood_unit_id": result[6]
        })

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()
# =====================================================
# ADMIN - STAFF MANAGEMENT
# =====================================================

@app.route("/api/admin/staff", methods=["GET"])
def get_staff_accounts():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT 
                hs.staff_id,
                hs.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                u.account_status,
                hs.staff_role,
                h.hospital_id,
                h.hospital_name
            FROM HospitalStaff hs
            JOIN UserAccount u ON hs.user_id = u.user_id
            JOIN Hospital h ON hs.hospital_id = h.hospital_id
            ORDER BY hs.staff_id
        """)
    })


@app.route("/api/admin/staff", methods=["POST"])
def create_staff_account():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    age = int(data.get("age", 0))
    gender = data.get("gender")

    if not email.endswith("@bbms.com"):
        return jsonify({"success": False, "message": "Staff email must end with @bbms.com"}), 400

    if age < 18 or age > 65:
        return jsonify({"success": False, "message": "Staff age must be between 18 and 65"}), 400

    if gender not in ["Male", "Female", "Other"]:
        return jsonify({"success": False, "message": "Gender must be Male, Female, or Other"}), 400

    if len(data.get("password", "")) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400
    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'HospitalStaff')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("age"),
        data.get("gender"),
        data.get("email", "").strip().lower(),
        data.get("password"),
        data.get("phone")
    ), fetch=False)

    if user_id is None:
        return jsonify({"success": False, "message": "Could not create staff user"}), 400

    staff_id = query_db("""
        INSERT INTO HospitalStaff (user_id, hospital_id, staff_role)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        data.get("hospital_id"),
        data.get("staff_role")
    ), fetch=False)

    return jsonify({
        "success": True,
        "user_id": user_id,
        "staff_id": staff_id
    })


@app.route("/api/admin/staff/<int:user_id>/status", methods=["PUT"])
def update_staff_status(user_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount
        SET account_status = %s
        WHERE user_id = %s AND role = 'HospitalStaff'
    """, (
        data.get("account_status"),
        user_id
    ), fetch=False)

    return jsonify({"success": True, "message": "Staff status updated"})


@app.route("/api/admin/staff/<int:staff_id>", methods=["DELETE"])
def delete_staff_account(staff_id):
    query_db("""
        DELETE u FROM UserAccount u
        JOIN HospitalStaff hs ON u.user_id = hs.user_id
        WHERE hs.staff_id = %s
    """, (staff_id,), fetch=False)

    return jsonify({"success": True, "message": "Staff deleted"})
# =====================================================
# DONOR REGISTRATION / PROFILE UPDATE
# =====================================================

@app.route("/api/donors/register", methods=["POST"])
def register_donor():
    data = request.json or {}
    existing = query_db("""
                        SELECT user_id
                        FROM UserAccount
                        WHERE email = %s
                        """, (data.get("email", "").strip().lower()))

    if existing:
        return jsonify({"success": False, "message": "Email already exists"}), 400
    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Donor')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("age"),
        data.get("gender"),
        data.get("email", "").strip().lower(),
        data.get("password"),
        data.get("phone")
    ), fetch=False)

    if user_id is None:
        return jsonify({"success": False, "message": "Could not create donor account"}), 400

    donor_id = query_db("""
        INSERT INTO Donor
        (user_id, blood_type, health_status, weight_kg, medication_restricted, eligibility_status)
        VALUES (%s, %s, %s, %s, %s, 'Eligible')
    """, (
        user_id,
        data.get("blood_type"),
        data.get("health_status", "Healthy"),
        data.get("weight_kg"),
        data.get("medication_restricted", False)
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "donor_id": donor_id})


@app.route("/api/donors/<int:donor_id>", methods=["PUT"])
def update_donor_profile(donor_id):
    data = request.json or {}

    donor = query_db("""
        SELECT user_id FROM Donor WHERE donor_id = %s
    """, (donor_id,))

    if not donor:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    user_id = donor[0]["user_id"]

    query_db("""
        UPDATE UserAccount
        SET first_name = %s,
            last_name = %s,
            phone = %s
        WHERE user_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("phone"),
        user_id
    ), fetch=False)

    query_db("""
        UPDATE Donor
        SET health_status = %s,
            weight_kg = %s,
            medication_restricted = %s
        WHERE donor_id = %s
    """, (
        data.get("health_status"),
        data.get("weight_kg"),
        data.get("medication_restricted", False),
        donor_id
    ), fetch=False)

    return jsonify({"success": True, "message": "Donor profile updated"})
# =====================================================
# RECIPIENT PROFILE UPDATE
# =====================================================

@app.route("/api/recipients/<int:recipient_id>", methods=["PUT"])
def update_recipient_profile(recipient_id):
    data = request.json or {}

    recipient = query_db("""
        SELECT user_id FROM Recipient WHERE recipient_id = %s
    """, (recipient_id,))

    if not recipient:
        return jsonify({"success": False, "message": "Recipient not found"}), 404

    user_id = recipient[0]["user_id"]

    query_db("""
        UPDATE UserAccount
        SET first_name = %s,
            last_name = %s,
            phone = %s
        WHERE user_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("phone"),
        user_id
    ), fetch=False)

    query_db("""
        UPDATE Recipient
        SET medical_condition = %s
        WHERE recipient_id = %s
    """, (
        data.get("medical_condition"),
        recipient_id
    ), fetch=False)

    return jsonify({"success": True, "message": "Recipient profile updated"})
@app.route("/api/recipients/register", methods=["POST"])
def register_recipient():
    data = request.json or {}
    existing = query_db("""
                        SELECT user_id
                        FROM UserAccount
                        WHERE email = %s
                        """, (data.get("email", "").strip().lower()))

    if existing:
        return jsonify({"success": False, "message": "Email already exists"}), 400
    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Recipient')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("age"),
        data.get("gender"),
        data.get("email", "").strip().lower(),
        data.get("password"),
        data.get("phone")
    ), fetch=False)

    if user_id is None:
        return jsonify({"success": False, "message": "Could not create recipient account"}), 400

    recipient_id = query_db("""
        INSERT INTO Recipient
        (user_id, blood_type, medical_condition)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        data.get("blood_type"),
        data.get("medical_condition", "")
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "recipient_id": recipient_id})
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)