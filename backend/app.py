from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from config import Config
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
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
from datetime import date, datetime, timedelta

def check_donor_eligibility(donor):
    if donor.get("is_active", 1) == 0:
        return False, "Donor inactive"

    dob = donor.get("dob")
    if not dob:
        return False, "Missing DOB"

    age = (date.today() - dob).days // 365
    if age < 18:
        return False, "Must be 18+"

    last = donor.get("last_donation_date")
    if last:
        if isinstance(last, str):
            last = datetime.strptime(last, "%Y-%m-%d").date()

        if date.today() - last < timedelta(days=56):
            return False, "Wait 8 weeks between donations"

    return True, "Eligible"

def email_exists(email: str, role: str, exclude_user_id: int = None) -> bool:
    sql = "SELECT 1 FROM UserAccount WHERE email = %s AND role = %s"
    params = [email, role]
    if exclude_user_id is not None:
        sql += " AND user_id != %s"
        params.append(exclude_user_id)
    return bool(query_db(sql + " LIMIT 1", params))


def phone_exists(phone: str, role: str, exclude_user_id: int = None) -> bool:
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

@app.route("/api/debug-db")
def debug_db():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() AS db")
        db = cursor.fetchall()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "database": db, "tables": tables})
    except Error as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/debug-config")
def debug_config():
    return jsonify({
        "DB_HOST": Config.DB_HOST,
        "DB_PORT": Config.DB_PORT,
        "DB_NAME": Config.DB_NAME,
        "DB_USER": Config.DB_USER
    })


# =====================================================
# AUTH / LOGIN
# =====================================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password")

    user = query_db("""
        SELECT user_id, first_name, last_name, email, role, password_hash,
               account_status, failed_login_attempts, locked_until
        FROM UserAccount
        WHERE email = %s
    """, (email,))

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    user = user[0]

    if user["locked_until"]:
        return jsonify({
            "success": False,
            "message": "Account locked due to 5 failed login attempts. Contact admin."
        }), 403

    if user["account_status"] != "Active":
        return jsonify({"success": False, "message": "Account is not active"}), 403

    if not check_password_hash(user["password_hash"], password):
        failed_attempts = (user["failed_login_attempts"] or 0) + 1

        if failed_attempts >= 5:
            query_db("""
                UPDATE UserAccount
                SET failed_login_attempts = %s,
                    account_status = 'Locked',
                    locked_until = NOW()
                WHERE user_id = %s
            """, (failed_attempts, user["user_id"]), fetch=False)

            return jsonify({
                "success": False,
                "message": "Account locked after 5 failed login attempts."
            }), 403

        query_db("""
            UPDATE UserAccount
            SET failed_login_attempts = %s
            WHERE user_id = %s
        """, (failed_attempts, user["user_id"]), fetch=False)

        return jsonify({
            "success": False,
            "message": f"Invalid email or password. Attempt {failed_attempts}/5"
        }), 401

    query_db("""
        UPDATE UserAccount
        SET failed_login_attempts = 0,
            locked_until = NULL
        WHERE user_id = %s
    """, (user["user_id"],), fetch=False)

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


def record_log(user_id, action_type, entity_type, entity_id, description):
    if not user_id:
        return
    query_db("""
        INSERT INTO ActivityLog
        (user_id, action_type, entity_type, entity_id, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, action_type, entity_type, entity_id, description), fetch=False)


@app.route("/api/admin/staff/<int:staff_id>", methods=["PUT"])
def update_staff(staff_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount ua
        JOIN HospitalStaff hs ON ua.user_id = hs.user_id
        SET ua.first_name = %s,
            ua.last_name = %s,
            ua.phone = %s
        WHERE hs.staff_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("phone"),
        staff_id
    ), fetch=False)

    query_db("""
        UPDATE HospitalStaff
        SET hospital_id = %s,
            staff_role = %s
        WHERE staff_id = %s
    """, (
        data.get("hospital_id"),
        data.get("staff_role"),
        staff_id
    ), fetch=False)

    record_log(
        data.get("admin_user_id"), "UPDATE", "HospitalStaff", staff_id, "Staff account updated"
    )

    return jsonify({"success": True, "message": "Staff updated successfully"})


@app.route("/api/admin/unlock-user/<int:user_id>", methods=["PUT"])
def unlock_user(user_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount
        SET failed_login_attempts = 0,
            account_status = 'Active',
            locked_until = NULL
        WHERE user_id = %s
    """, (user_id,), fetch=False)

    record_log(
        data.get("admin_user_id"), "UPDATE", "UserAccount", user_id, "User account unlocked"
    )

    return jsonify({"success": True, "message": "User account unlocked successfully"})


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

    record_log(
        data.get("admin_user_id"), "CREATE", "Hospital", hospital_id,
        f"Hospital created: {data.get('hospital_name')}"
    )

    return jsonify({"success": True, "hospital_id": hospital_id})


# =====================================================
# DONORS
# =====================================================
@app.route("/api/donors/by-user/<int:user_id>")
def get_donor_by_user(user_id):
    data = query_db("""
        SELECT d.donor_id, d.blood_type, d.health_status, d.weight_kg,
               d.medication_restricted, d.eligibility_status, d.last_donation_date,
               u.first_name, u.last_name, u.phone,
               CONCAT(u.first_name, ' ', u.last_name) AS full_name
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
        WHERE d.user_id = %s
    """, (user_id,))
    if not data:
        return jsonify({"success": False, "message": "Donor not found"}), 404
    return jsonify({"success": True, "data": data[0]})
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

@app.route("/api/donors/register", methods=["POST"])
def register_donor():
    data = request.json or {}

    required = ["first_name", "last_name", "email", "password", "phone", "blood_type", "weight_kg"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    phone = clean_phone(data.get("phone"))
    if phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid phone number. Must be a Lebanese number with exactly 8 digits "
                       "(e.g. 03123456 or +96103123456)"
        }), 400

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    weight = safe_float(data.get("weight_kg"))
    if weight is None:
        return jsonify({"success": False, "message": "Invalid weight value"}), 400

    age = safe_int(data.get("age"))
    if age is None or not (18 <= age <= 65):
        return jsonify({
            "success": False,
            "message": "Invalid age. Donors must be between 18 and 65 years old"
        }), 400

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
        generate_password_hash(data.get("password")),
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

    donor = query_db(
        "SELECT user_id FROM Donor WHERE donor_id = %s",
        (donor_id,)
    )
    if not donor:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    user_id = donor[0]["user_id"]

    # -------------------------
    # PHONE VALIDATION
    # -------------------------
    phone = clean_phone(data.get("phone"))
    if data.get("phone") and phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid Lebanese phone number (must be 8 digits)"
        }), 400

    if phone and phone_exists(phone, "Donor", exclude_user_id=user_id):
        return jsonify({
            "success": False,
            "message": "Phone number already registered to another donor"
        }), 409

    # -------------------------
    # UPDATE USER TABLE
    # -------------------------
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

    # -------------------------
    # NORMALIZE MEDICATION INPUT (IMPORTANT FIX)
    # -------------------------
    med_raw = data.get("medication_restricted")

    medication_restricted = False

    if isinstance(med_raw, bool):
        medication_restricted = med_raw

    elif isinstance(med_raw, (int, float)):
        medication_restricted = bool(med_raw)

    elif isinstance(med_raw, str):
        medication_restricted = med_raw.strip().lower() in [
            "true",
            "1",
            "yes",
            "medication restricted"   # 👈 YOUR UI VALUE (capital M handled via lower())
        ]

    # -------------------------
    # UPDATE DONOR TABLE
    # -------------------------
    query_db("""
        UPDATE Donor
        SET health_status         = %s,
            weight_kg             = %s,
            medication_restricted = %s
        WHERE donor_id = %s
    """, (
        data.get("health_status"),
        data.get("weight_kg"),
        medication_restricted,
        donor_id
    ), fetch=False)

    # -------------------------
    # RELOAD UPDATED DATA
    # -------------------------
    donor = query_db("""
        SELECT d.*, u.age
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
        WHERE d.donor_id = %s
    """, (donor_id,))[0]

    # -------------------------
    # ELIGIBILITY LOGIC
    # -------------------------
    eligible = True

    med = donor["medication_restricted"]
    if isinstance(med, str):
        med = med.strip().lower() in ["1", "true", "yes", "medication restricted"]
    else:
        med = bool(med)

    weight = donor.get("weight_kg")
    weight = float(weight) if weight is not None else None

    if med:
        eligible = False
    elif donor["health_status"] != "Healthy":
        eligible = False
    elif weight is not None and weight < 45:
        eligible = False

    # -------------------------
    # UPDATE ELIGIBILITY
    # -------------------------
    query_db("""
        UPDATE Donor
        SET eligibility_status = %s
        WHERE donor_id = %s
    """, (
        "Eligible" if eligible else "Ineligible",
        donor_id
    ), fetch=False)

    return jsonify({
        "success": True,
        "message": "Donor profile updated"
    })


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

    donor_id = data.get("donor_id")
    hospital_id = data.get("hospital_id")
    appointment_datetime = data.get("appointment_datetime")

    donor = query_db("""
        SELECT d.*, u.user_id, u.age
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
        WHERE d.donor_id = %s
    """, (donor_id,))

    if not donor:
        return jsonify({
            "success": False,
            "message": "Donor not found. The frontend may be sending user_id instead of donor_id."
        }), 404

    donor = donor[0]

    existing_appointment = query_db("""
        SELECT appointment_id
        FROM Appointment
        WHERE donor_id = %s
          AND status = 'Scheduled'
          AND appointment_datetime >= NOW()
        LIMIT 1
    """, (donor_id,))

    if existing_appointment:
        return jsonify({
            "success": False,
            "message": "You already have a scheduled donation appointment."
        }), 409

    if donor["eligibility_status"] != "Eligible":
        return jsonify({
            "success": False,
            "message": "Donor is not eligible to schedule a donation appointment."
        }), 403

    if donor["health_status"] != "Healthy":
        return jsonify({
            "success": False,
            "message": "Donor health status is not suitable for donation."
        }), 403

    if donor["medication_restricted"]:
        return jsonify({
            "success": False,
            "message": "Donor is temporarily deferred due to medication restriction."
        }), 403

    if donor["weight_kg"] is not None and float(donor["weight_kg"]) < 45:
        return jsonify({
            "success": False,
            "message": "Donor weight must be at least 45 kg."
        }), 403

    if donor["last_donation_date"]:
        last_date = donor["last_donation_date"]
        if isinstance(last_date, str):
            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
        days_since = (date.today() - last_date).days
        if days_since < 56:
            return jsonify({
                "success": False,
                "message": f"Donor must wait 56 days between donations. Only {days_since} days passed."
            }), 403

    appointment_id = query_db("""
        INSERT INTO Appointment
        (donor_id, hospital_id, appointment_datetime, status, eligibility_snapshot, notes)
        VALUES (%s, %s, %s, 'Scheduled', 'Eligible', %s)
    """, (
        donor_id,
        hospital_id,
        appointment_datetime,
        data.get("notes", "")
    ), fetch=False)

    query_db("""
        INSERT INTO Notification
        (user_id, message, type, is_read)
        VALUES (%s, %s, 'Appointment', FALSE)
    """, (
        donor["user_id"],
        "Donation appointment confirmed successfully."
    ), fetch=False)

    return jsonify({
        "success": True,
        "appointment_id": appointment_id,
        "message": "Donation appointment scheduled successfully."
    }), 201


# =====================================================
# RECIPIENTS
# =====================================================

@app.route("/api/recipients")
def get_recipients():
    return jsonify({
        "success": True,
        "data": query_db("SELECT * FROM vw_recipient_profiles ORDER BY recipient_id")
    })


@app.route("/api/recipients/register", methods=["POST"])
def register_recipient():
    data = request.json or {}

    required = ["first_name", "last_name", "email", "password", "phone", "blood_type"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    phone = clean_phone(data.get("phone"))
    if phone is None:
        return jsonify({
            "success": False,
            "message": "Invalid phone number. Must be a Lebanese number with exactly 8 digits "
                       "(e.g. 03123456 or +96103123456)"
        }), 400

    blood_type = clean_blood_type(data.get("blood_type"))
    if blood_type is None:
        return jsonify({
            "success": False,
            "message": f"Invalid blood type. Accepted values: {', '.join(sorted(VALID_BLOOD_TYPES))}"
        }), 400

    age = safe_int(data.get("age"))
    if age is None or not (18 <= age <= 120):
        return jsonify({
            "success": False,
            "message": "Invalid age. Recipients must be between 18 and 120 years old"
        }), 400

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
        generate_password_hash(data.get("password")),
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

        cursor.execute("SELECT status FROM BloodRequest WHERE request_id = %s", (request_id,))
        row = cursor.fetchone()

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

        request_info = query_db("""
            SELECT r.user_id
            FROM BloodRequest br
            JOIN Recipient r ON br.recipient_id = r.recipient_id
            WHERE br.request_id = %s
        """, (request_id,))

        if request_info:
            query_db("""
                INSERT INTO Notification (user_id, message, type, is_read)
                VALUES (%s, %s, 'Blood Request', FALSE)
            """, (
                request_info[0]["user_id"],
                "Your blood request has been approved and fulfilled."
            ), fetch=False)

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

        request_info = query_db("""
            SELECT r.user_id
            FROM BloodRequest br
            JOIN Recipient r ON br.recipient_id = r.recipient_id
            WHERE br.request_id = %s
        """, (request_id,))

        if request_info:
            query_db("""
                INSERT INTO Notification (user_id, message, type, is_read)
                VALUES (%s, %s, 'Blood Request', FALSE)
            """, (
                request_info[0]["user_id"],
                "Your blood request has been rejected."
            ), fetch=False)

        return jsonify({"success": True, "message": "Blood request rejected"})

    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 400

    finally:
        if conn:
            conn.close()


@app.route("/api/appointments/<int:appointment_id>/cancel", methods=["PUT"])
def cancel_appointment(appointment_id):
    appointment = query_db("""
        SELECT a.appointment_id, a.donor_id, d.user_id
        FROM Appointment a
        JOIN Donor d ON a.donor_id = d.donor_id
        WHERE a.appointment_id = %s
    """, (appointment_id,))

    if not appointment:
        return jsonify({"success": False, "message": "Appointment not found"}), 404

    appointment = appointment[0]

    query_db("""
        UPDATE Appointment
        SET status = 'Cancelled'
        WHERE appointment_id = %s AND status = 'Scheduled'
    """, (appointment_id,), fetch=False)

    query_db("""
        INSERT INTO Notification (user_id, message, type, is_read)
        VALUES (%s, %s, 'Appointment', FALSE)
    """, (
        appointment["user_id"],
        "Your donation appointment has been cancelled."
    ), fetch=False)

    return jsonify({"success": True, "message": "Appointment cancelled"})


@app.route("/api/staff/urgent-shortage", methods=["POST"])
def notify_urgent_shortage():
    data = request.json or {}

    # 1. Validate staff
    staff = query_db("""
        SELECT staff_id
        FROM HospitalStaff
        WHERE staff_id = %s
    """, (data.get("staff_id"),))

    if not staff:
        return jsonify({
            "success": False,
            "message": "Unauthorized staff access."
        }), 403

    # 2. Validate blood type
    blood_type = clean_blood_type(data.get("blood_type"))

    if blood_type is None:
        return jsonify({
            "success": False,
            "message": "Invalid blood type"
        }), 400

    # 3. Get eligible donors
    donors = query_db("""
        SELECT
            d.donor_id,
            d.user_id,
            u.first_name,
            u.account_status,
            d.eligibility_status
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
        WHERE d.blood_type = %s
          AND d.eligibility_status = 'Eligible'
          AND u.account_status = 'Active'
    """, (blood_type,))

    if not donors:
        return jsonify({
            "success": False,
            "message": f"No eligible donors found for {blood_type}"
        })

    # 4. Insert notifications
    inserted_count = 0

    for donor in donors:
        try:
            print("DONOR:", donor, flush=True)

            row_id = query_db("""
                INSERT INTO Notification
                (user_id, message, type, is_read)
                VALUES (%s, %s, %s, FALSE)
            """, (
                donor["user_id"],
                f"Urgent blood shortage alert for blood type {blood_type}. Please consider donating.",
                "Shortage"
            ), fetch=False)

            print("INSERT RESULT:", row_id, flush=True)

            if row_id:
                inserted_count += 1

        except Exception as e:
            print("INSERT ERROR:", str(e), flush=True)

    # 5. Response
    return jsonify({
        "success": True,
        "message": f"{inserted_count} notifications inserted",
        "donors_found": len(donors)
    })


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
    result = query_db("""
        UPDATE Notification
        SET is_read = TRUE
        WHERE notification_id = %s AND is_read = FALSE
    """, (notification_id,), fetch=False)

    if result == 0:
        return jsonify({"success": True, "message": "Already marked as read"})

    return jsonify({"success": True, "message": "Marked as read"})


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

@app.route("/api/donors")
def get_donors():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT
                d.donor_id,
                d.user_id,
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
            ORDER BY u.first_name, u.last_name
        """)
    })


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

    staff = query_db("""
        SELECT staff_id FROM HospitalStaff WHERE staff_id = %s
    """, (data.get("staff_id"),))

    if not staff:
        return jsonify({"success": False, "message": "Unauthorized staff access."}), 403

    donor_info = query_db("""
        SELECT blood_type FROM Donor WHERE donor_id = %s
    """, (data.get("donor_id"),))

    if not donor_info:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    blood_type = donor_info[0]["blood_type"]

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
        generate_password_hash(data.get("password")),
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

    record_log(
        data.get("admin_user_id"), "CREATE", "HospitalStaff", staff_id,
        f"Staff account created: {email}"
    )

    return jsonify({"success": True, "user_id": user_id, "staff_id": staff_id}), 201


@app.route("/api/admin/staff/<int:user_id>/status", methods=["PUT"])
def update_staff_status(user_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount
        SET account_status = %s
        WHERE user_id = %s AND role = 'HospitalStaff'
    """, (data.get("account_status"), user_id), fetch=False)

    record_log(
        data.get("admin_user_id"), "UPDATE", "HospitalStaff", user_id,
        f"Staff status updated to {data.get('account_status')}"
    )

    return jsonify({"success": True, "message": "Staff status updated"})


@app.route("/api/admin/staff/<int:staff_id>", methods=["DELETE"])
def delete_staff_account(staff_id):
    data = request.json or {}

    query_db("""
        DELETE u FROM UserAccount u
        JOIN HospitalStaff hs ON u.user_id = hs.user_id
        WHERE hs.staff_id = %s
    """, (staff_id,), fetch=False)

    record_log(
        data.get("admin_user_id"), "DELETE", "HospitalStaff", staff_id, "Staff account deleted"
    )

    return jsonify({"success": True, "message": "Staff deleted"})


# =====================================================
# MOH
# =====================================================

@app.route("/api/ministry/inventory-summary")
def ministry_inventory_summary():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT blood_type, component_type, status,
                   COUNT(*) AS unit_count,
                   SUM(quantity_ml) AS total_quantity_ml
            FROM BloodUnit
            GROUP BY blood_type, component_type, status
            ORDER BY blood_type, component_type, status
        """)
    })


@app.route("/api/ministry/hospital-summary")
def ministry_hospital_summary():
    return jsonify({
        "success": True,
        "data": query_db("""
            SELECT h.hospital_name, h.location, b.blood_type,
                   COUNT(*) AS unit_count,
                   SUM(b.quantity_ml) AS total_quantity_ml
            FROM BloodUnit b
            JOIN Hospital h ON b.hospital_id = h.hospital_id
            GROUP BY h.hospital_name, h.location, b.blood_type
            ORDER BY h.hospital_name, b.blood_type
        """)
    })


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
