from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from config import Config
import os
import re

app = Flask(__name__)
CORS(app)


# =====================================================
# VALIDATION HELPERS
# =====================================================

_EMAIL_RE = re.compile(
    r'^(?!.*\.\.)[a-zA-Z0-9][a-zA-Z0-9._%+\-]*[a-zA-Z0-9]'
    r'@[a-zA-Z0-9][a-zA-Z0-9.\-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
)

def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def clean_phone(phone) -> str | None:
    """
    Normalise a Lebanese phone number to its bare 8-digit form.
    Accepts: +961XXXXXXXX / 961XXXXXXXX / 0XXXXXXXX / XXXXXXXX
    Returns None when the number is missing or malformed.
    """
    if not phone:
        return None
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("+961"):
        phone = phone[4:]
    elif phone.startswith("961"):
        phone = phone[3:]
    elif phone.startswith("0"):
        phone = phone[1:]
    if not phone.isdigit() or len(phone) != 8:
        return None
    return phone


VALID_BLOOD_TYPES = frozenset({"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"})

def clean_blood_type(bt) -> str | None:
    if not bt:
        return None
    bt = str(bt).strip().upper()
    return bt if bt in VALID_BLOOD_TYPES else None


def safe_float(value) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


# =====================================================
# DB
# =====================================================

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


# =====================================================
# UNIQUENESS HELPERS
# =====================================================

def email_exists(email: str, role: str, exclude_user_id: int = None) -> bool:
    """True if email is already taken within the same role."""
    sql = "SELECT 1 FROM UserAccount WHERE email = %s AND role = %s"
    params = [email, role]
    if exclude_user_id is not None:
        sql += " AND user_id != %s"
        params.append(exclude_user_id)
    return bool(query_db(sql + " LIMIT 1", params))


def phone_exists(phone: str, role: str, exclude_user_id: int = None) -> bool:
    """True if phone (8-digit normalised) is already taken within the same role."""
    sql = "SELECT 1 FROM UserAccount WHERE phone = %s AND role = %s"
    params = [phone, role]
    if exclude_user_id is not None:
        sql += " AND user_id != %s"
        params.append(exclude_user_id)
    return bool(query_db(sql + " LIMIT 1", params))


# =====================================================
# ROOT / DEBUG
# =====================================================

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
            "user_id":   user["user_id"],
            "full_name": f"{user['first_name']} {user['last_name']}",
            "email":     user["email"],
            "role":      user["role"]
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


# ── /register MUST come before /<int:donor_id> so Flask matches it correctly ──

@app.route("/api/donors/register", methods=["POST"])
def register_donor():
    data = request.json or {}

    # Required fields
    required = ["first_name", "last_name", "email", "password", "phone", "blood_type", "weight_kg"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    # Email
    email = data["email"].strip().lower()
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    # Phone
    phone = clean_phone(data.get("phone"))
    if phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid phone number. Must be a Lebanese number with exactly 8 digits "
                       "(e.g. 03123456 or +96103123456)"
        }), 400

    # Blood type
    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    # Weight
    weight = safe_float(data.get("weight_kg"))
    if weight is None:
        return jsonify({"success": False, "message": "Invalid weight value"}), 400

    # Age (donors must be 18–65)
    age = safe_int(data.get("age"))
    if age is None or not (18 <= age <= 65):
        return jsonify({
            "success": False,
            "message": "Invalid age. Donors must be between 18 and 65 years old"
        }), 400

    # Uniqueness (scoped to Donor role)
    if email_exists(email, "Donor"):
        return jsonify({"success": False, "message": "Email is already registered to an existing donor"}), 409

    if phone_exists(phone, "Donor"):
        return jsonify({"success": False, "message": "Phone number is already registered to an existing donor"}), 409

    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Donor')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        age,
        data.get("gender"),
        email,
        data.get("password"),
        phone
    ), fetch=False)

    if user_id is None:
        return jsonify({"success": False, "message": "Could not create donor account"}), 400

    donor_id = query_db("""
        INSERT INTO Donor
        (user_id, blood_type, health_status, weight_kg, medication_restricted, eligibility_status)
        VALUES (%s, %s, %s, %s, %s, 'Eligible')
    """, (
        user_id,
        blood_type,
        data.get("health_status", "Healthy"),
        weight,
        data.get("medication_restricted", False)
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "donor_id": donor_id}), 201


@app.route("/api/donors/<int:donor_id>", methods=["PUT"])
def update_donor_profile(donor_id):
    data = request.json or {}

    donor = query_db("SELECT user_id FROM Donor WHERE donor_id = %s", (donor_id,))
    if not donor:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    user_id = donor[0]["user_id"]

    # Phone validation + uniqueness on update
    phone = clean_phone(data.get("phone"))
    if data.get("phone") and phone is None:
        return jsonify({"success": False, "message": "Invalid Lebanese phone number (must be 8 digits)"}), 400

    if phone and phone_exists(phone, "Donor", exclude_user_id=user_id):
        return jsonify({"success": False, "message": "Phone number already registered to another donor"}), 409

    query_db("""
        UPDATE UserAccount
        SET first_name = %s,
            last_name  = %s,
            phone      = %s
        WHERE user_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        phone,
        user_id
    ), fetch=False)

    query_db("""
        UPDATE Donor
        SET health_status         = %s,
            weight_kg             = %s,
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
# APPOINTMENTS
# =====================================================

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


# ── /register MUST come before /<int:recipient_id> so Flask matches it correctly ──

@app.route("/api/recipients/register", methods=["POST"])
def register_recipient():
    data = request.json or {}

    # Required fields
    required = ["first_name", "last_name", "email", "password", "phone", "blood_type"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    # Email
    email = data["email"].strip().lower()
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    # Phone
    phone = clean_phone(data.get("phone"))
    if phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid phone number. Must be a Lebanese number with exactly 8 digits "
                       "(e.g. 03123456 or +96103123456)"
        }), 400

    # Blood type
    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    # Age (recipients must be 18-120)
    age = safe_int(data.get("age"))
    if age is None or not (18 <= age <= 120):
        return jsonify({
            "success": False,
            "message": "Invalid age. Recipients must be between 18 and 120 years old"
        }), 400

    # Uniqueness (scoped to Recipient role)
    if email_exists(email, "Recipient"):
        return jsonify({"success": False, "message": "Email is already registered to an existing recipient"}), 409

    if phone_exists(phone, "Recipient"):
        return jsonify({"success": False, "message": "Phone number is already registered to an existing recipient"}), 409

    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Recipient')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        age,
        data.get("gender"),
        email,
        data.get("password"),
        phone
    ), fetch=False)

    if user_id is None:
        return jsonify({"success": False, "message": "Could not create recipient account"}), 400

    recipient_id = query_db("""
        INSERT INTO Recipient
        (user_id, blood_type, medical_condition)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        blood_type,
        data.get("medical_condition", "")
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "recipient_id": recipient_id}), 201


@app.route("/api/recipients/<int:recipient_id>", methods=["PUT"])
def update_recipient_profile(recipient_id):
    data = request.json or {}

    recipient = query_db("SELECT user_id FROM Recipient WHERE recipient_id = %s", (recipient_id,))
    if not recipient:
        return jsonify({"success": False, "message": "Recipient not found"}), 404

    user_id = recipient[0]["user_id"]

    # Phone validation + uniqueness on update
    phone = clean_phone(data.get("phone"))
    if data.get("phone") and phone is None:
        return jsonify({"success": False, "message": "Invalid Lebanese phone number (must be 8 digits)"}), 400

    if phone and phone_exists(phone, "Recipient", exclude_user_id=user_id):
        return jsonify({"success": False, "message": "Phone number already registered to another recipient"}), 409

    query_db("""
        UPDATE UserAccount
        SET first_name = %s,
            last_name  = %s,
            phone      = %s
        WHERE user_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        phone,
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

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    blood_unit_id = query_db("""
        INSERT INTO BloodUnit
        (hospital_id, donor_id, blood_type, component_type, quantity_ml, donation_date, expiry_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Available')
    """, (
        data.get("hospital_id"),
        data.get("donor_id"),
        blood_type,
        data.get("component_type", "Whole Blood"),
        data.get("quantity_ml"),
        data.get("donation_date"),
        data.get("expiry_date")
    ), fetch=False)

    if blood_unit_id is None:
        return jsonify({"success": False, "message": "Failed to add blood unit"}), 400

    return jsonify({"success": True, "blood_unit_id": blood_unit_id}), 201


@app.route("/api/blood-units/<int:blood_unit_id>", methods=["PUT"])
def edit_blood_unit(blood_unit_id):
    data = request.json or {}

    query_db("""
        UPDATE BloodUnit
        SET quantity_ml = %s,
            expiry_date = %s,
            status      = %s
        WHERE blood_unit_id = %s
    """, (
        data.get("quantity_ml"),
        data.get("expiry_date"),
        data.get("status"),
        blood_unit_id
    ), fetch=False)

    return jsonify({"success": True, "message": "Blood unit updated successfully"})


@app.route("/api/blood-units/<int:blood_unit_id>", methods=["DELETE"])
def delete_blood_unit(blood_unit_id):
    query_db("""
        DELETE FROM BloodUnit WHERE blood_unit_id = %s
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

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        args = [
            data.get("donor_id"),
            data.get("staff_id"),
            data.get("hospital_id"),
            blood_type,
            data.get("quantity_ml"),
            0,
            0
        ]

        result_args = cursor.callproc("RegisterDonation", args)
        conn.commit()

        return jsonify({
            "success":       True,
            "donation_id":   result_args[5],
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

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    request_id = query_db("""
        INSERT INTO BloodRequest
        (recipient_id, hospital_id, blood_type, quantity_needed_ml, priority_level, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """, (
        data.get("recipient_id"),
        data.get("hospital_id"),
        blood_type,
        data.get("quantity_needed_ml"),
        data.get("priority_level", "Medium")
    ), fetch=False)

    return jsonify({"success": True, "request_id": request_id}), 201


@app.route("/api/blood-requests/<int:request_id>/fulfill", methods=["POST"])
def fulfill_request(request_id):
    data = request.json or {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM bloodrequest WHERE request_id = %s", (request_id,))
        row = cursor.fetchone()

        print(f"[DEBUG] Request {request_id} - row: {row}")  # <-- add this

        if not row:
            return jsonify({"success": False, "error": "Request not found"}), 404

        if row[0] != "Pending":
            return jsonify({"success": False, "error": f"Request is already {row[0].lower()} and cannot be fulfilled"}), 400

        cursor.callproc("ProcessBloodRequest", [
            request_id,
            data.get("blood_unit_id"),
            data.get("staff_id")
        ])
        for result in cursor.stored_results():
            result.fetchall()
        conn.commit()
        return jsonify({"success": True, "message": "Blood request fulfilled"})

    except Error as e:
        print(f"[DEBUG] Exception: {str(e)}")  # <-- and this
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
        UPDATE Notification SET is_read = TRUE WHERE notification_id = %s
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
# STAFF
# =====================================================

@app.route("/api/staff/<int:user_id>/profile")
def staff_profile(user_id):
    data = query_db("""
        SELECT hs.staff_id, hs.user_id, hs.hospital_id, hs.staff_role, h.hospital_name
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
                SELECT hospital_name FROM Hospital WHERE hospital_id = hs.hospital_id
            )
            WHERE hs.user_id = %s
            ORDER BY br.request_date DESC
        """, (user_id,))
    })


@app.route("/api/staff/register-donation", methods=["POST"])
def staff_register_donation():
    data = request.json or {}

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        args = [
            data.get("donor_id"),
            data.get("staff_id"),
            data.get("hospital_id"),
            blood_type,
            data.get("quantity_ml"),
            0,
            0
        ]

        result = cursor.callproc("RegisterDonation", args)
        conn.commit()

        return jsonify({
            "success":       True,
            "message":       "Donation registered successfully",
            "donation_id":   result[5],
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
            SELECT hs.staff_id, hs.user_id, u.first_name, u.last_name,
                   u.email, u.phone, u.account_status,
                   hs.staff_role, h.hospital_id, h.hospital_name
            FROM HospitalStaff hs
            JOIN UserAccount u ON hs.user_id = u.user_id
            JOIN Hospital h    ON hs.hospital_id = h.hospital_id
            ORDER BY hs.staff_id
        """)
    })


@app.route("/api/admin/staff", methods=["POST"])
def create_staff_account():
    data = request.json or {}

    email  = data.get("email", "").strip().lower()
    age    = int(data.get("age", 0))
    gender = data.get("gender")

    if not email.endswith("@bbms.com"):
        return jsonify({"success": False, "message": "Staff email must end with @bbms.com"}), 400

    if age < 18 or age > 65:
        return jsonify({"success": False, "message": "Staff age must be between 18 and 65"}), 400

    if gender not in ("Male", "Female", "Other"):
        return jsonify({"success": False, "message": "Gender must be Male, Female, or Other"}), 400

    if len(data.get("password", "")) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400

    phone = clean_phone(data.get("phone"))
    if phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid phone number. Must be a Lebanese number with exactly 8 digits"
        }), 400

    if email_exists(email, "HospitalStaff"):
        return jsonify({"success": False, "message": "Email is already registered to an existing staff member"}), 409

    if phone_exists(phone, "HospitalStaff"):
        return jsonify({"success": False, "message": "Phone number is already registered to an existing staff member"}), 409

    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name, last_name, age, gender, email, password_hash, phone, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'HospitalStaff')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        age,
        gender,
        email,
        data.get("password"),
        phone
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

    return jsonify({"success": True, "user_id": user_id, "staff_id": staff_id}), 201


@app.route("/api/admin/staff/<int:user_id>/status", methods=["PUT"])
def update_staff_status(user_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount
        SET account_status = %s
        WHERE user_id = %s AND role = 'HospitalStaff'
    """, (data.get("account_status"), user_id), fetch=False)

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
# RUN
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
