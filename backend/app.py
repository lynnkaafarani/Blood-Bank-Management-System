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
# HELPERS
# =====================================================

def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)


def clean_phone(phone):
    if not phone:
        return None

    phone = phone.strip().replace(" ", "")

    if phone.startswith("+961"):
        phone = phone[4:]
    elif phone.startswith("0"):
        phone = phone[1:]

    if not phone.isdigit():
        return None

    if len(phone) != 8:
        return None

    return phone


VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

def clean_blood_type(bt):
    if not bt:
        return None
    bt = bt.strip().upper()
    if bt not in VALID_BLOOD_TYPES:
        return None
    return bt


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except:
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
        print("DB ERROR:", e)
        return None

    finally:
        if conn:
            conn.close()


# =====================================================
# ROOT
# =====================================================

@app.route("/")
def home():
    return jsonify({"message": "BBMS backend running"})


# =====================================================
# AUTH PLACEHOLDER (since frontend expects login)
# =====================================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}

    email = data.get("email")
    password = data.get("password")

    user = query_db("""
        SELECT user_id, first_name, last_name, email, role
        FROM UserAccount
        WHERE email = %s AND password_hash = %s
    """, (email, password))

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    user = user[0]

    return jsonify({
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "full_name": user["first_name"] + " " + user["last_name"],
            "email": user["email"],
            "role": user["role"]
        }
    })

# =====================================================
# DONORS
# =====================================================

@app.route("/api/donors", methods=["GET"])
def get_donors():
    rows = query_db("""
        SELECT 
            d.donor_id,
            d.user_id,
            d.blood_type,
            d.health_status,
            d.weight_kg,
            d.eligibility_status,
            u.first_name,
            u.last_name,
            u.email,
            u.phone
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
    """)
    return jsonify({"success": True, "data": rows})


@app.route("/api/donors/<int:donor_id>", methods=["GET"])
def get_donor_by_id(donor_id):
    row = query_db("""
        SELECT 
            d.donor_id,
            d.user_id,
            d.blood_type,
            d.health_status,
            d.weight_kg,
            d.eligibility_status,
            d.medication_restricted,
            u.first_name,
            u.last_name,
            u.email,
            u.phone
        FROM Donor d
        JOIN UserAccount u ON d.user_id = u.user_id
        WHERE d.donor_id = %s
    """, (donor_id,))

    if not row:
        return jsonify({"success": False, "message": "Not found"}), 404

    return jsonify({"success": True, "data": row[0]})


@app.route("/api/donors/<int:donor_id>", methods=["PUT"])
def update_donor(donor_id):
    data = request.json or {}

    query_db("""
        UPDATE UserAccount u
        JOIN Donor d ON u.user_id = d.user_id
        SET 
            u.first_name = %s,
            u.last_name = %s,
            u.phone = %s,
            d.health_status = %s,
            d.weight_kg = %s,
            d.medication_restricted = %s
        WHERE d.donor_id = %s
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("phone"),
        data.get("health_status"),
        data.get("weight_kg"),
        data.get("medication_restricted"),
        donor_id
    ), fetch=False)

    return jsonify({"success": True})


# =====================================================
# DONOR REGISTER
# =====================================================

@app.route("/api/donors/register", methods=["POST"])
def register_donor():
    data = request.json or {}

    email = data.get("email", "").strip().lower()
    phone = clean_phone(data.get("phone"))
    blood_type = clean_blood_type(data.get("blood_type"))
    weight = safe_float(data.get("weight_kg"))

    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email"}), 400

    if not phone:
        return jsonify({"success": False, "message": "Invalid phone"}), 400

    if not blood_type:
        return jsonify({"success": False, "message": "Invalid blood type"}), 400

    if weight is None:
        return jsonify({"success": False, "message": "Invalid weight"}), 400

    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name,last_name,age,gender,email,password_hash,phone,role)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Donor')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("age"),
        data.get("gender"),
        email,
        data.get("password"),
        phone
    ), fetch=False)

    donor_id = query_db("""
        INSERT INTO Donor
        (user_id,blood_type,health_status,weight_kg,medication_restricted,eligibility_status)
        VALUES (%s,%s,%s,%s,%s,'Eligible')
    """, (
        user_id,
        blood_type,
        data.get("health_status", "Healthy"),
        weight,
        data.get("medication_restricted", False)
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "donor_id": donor_id})


# =====================================================
# HOSPITALS
# =====================================================

@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    rows = query_db("""
        SELECT hospital_id, hospital_name, location, contact_info
        FROM Hospital
    """)
    return jsonify({"success": True, "data": rows})


# =====================================================
# APPOINTMENTS
# =====================================================

@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    rows = query_db("""
        SELECT a.*, h.hospital_name
        FROM Appointment a
        JOIN Hospital h ON a.hospital_id = h.hospital_id
    """)
    return jsonify({"success": True, "data": rows})


@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    data = request.json or {}

    appointment_id = query_db("""
        INSERT INTO Appointment
        (donor_id,hospital_id,appointment_datetime,eligibility_snapshot,notes,status)
        VALUES (%s,%s,%s,%s,%s,'Pending')
    """, (
        data.get("donor_id"),
        data.get("hospital_id"),
        data.get("appointment_datetime"),
        data.get("eligibility_snapshot"),
        data.get("notes")
    ), fetch=False)

    return jsonify({"success": True, "appointment_id": appointment_id})


# =====================================================
# HISTORY
# =====================================================

@app.route("/api/donors/<int:donor_id>/history", methods=["GET"])
def donor_history(donor_id):
    rows = query_db("""
        SELECT 
            dn.donation_id,
            dn.donation_date,
            bu.blood_type,
            bu.quantity_ml,
            h.hospital_name,
            bu.status
        FROM Donation dn
        JOIN BloodUnit bu ON dn.blood_unit_id = bu.blood_unit_id
        JOIN Hospital h ON bu.hospital_id = h.hospital_id
        WHERE dn.donor_id = %s
    """, (donor_id,))

    return jsonify({"success": True, "data": rows})


# =====================================================
# NOTIFICATIONS
# =====================================================

@app.route("/api/notifications/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    rows = query_db("""
        SELECT *
        FROM Notification
        WHERE user_id = %s
        ORDER BY notification_date DESC
    """, (user_id,))

    return jsonify({"success": True, "data": rows})


@app.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_notification(notification_id):
    query_db("""
        UPDATE Notification
        SET is_read = 1
        WHERE notification_id = %s
    """, (notification_id,), fetch=False)

    return jsonify({"success": True})


# =====================================================
# DONATION REGISTER (your existing feature)
# =====================================================

@app.route("/api/donations/register", methods=["POST"])
def register_donation():
    data = request.json or {}

    blood_type = clean_blood_type(data.get("blood_type"))

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
    conn.close()

    return jsonify({
        "success": True,
        "donation_id": result[5],
        "blood_unit_id": result[6]
    })


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)