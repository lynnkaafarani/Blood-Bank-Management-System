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
# DONOR REGISTER (FIXED)
# =====================================================

@app.route("/api/donors/register", methods=["POST"])
def register_donor():
    data = request.json or {}

    email = data.get("email", "").strip().lower()
    phone = clean_phone(data.get("phone"))
    blood_type = clean_blood_type(data.get("blood_type"))
    weight = safe_float(data.get("weight_kg"))

    # VALIDATION
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email"}), 400

    if not phone:
        return jsonify({"success": False, "message": "Invalid phone number"}), 400

    if not blood_type:
        return jsonify({"success": False, "message": "Invalid blood type"}), 400

    if weight is None:
        return jsonify({"success": False, "message": "Invalid weight"}), 400

    # DUPLICATES (FIXED NORMALIZATION ISSUE)
    if query_db("SELECT user_id FROM UserAccount WHERE email=%s", (email,)):
        return jsonify({"success": False, "message": "Email exists"}), 400

    if query_db("SELECT user_id FROM UserAccount WHERE phone=%s", (phone,)):
        return jsonify({"success": False, "message": "Phone exists"}), 400

    # CREATE USER
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

    if not user_id:
        return jsonify({"success": False, "message": "User creation failed"}), 500

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
# RECIPIENT REGISTER
# =====================================================

@app.route("/api/recipients/register", methods=["POST"])
def register_recipient():
    data = request.json or {}

    email = data.get("email", "").strip().lower()
    phone = clean_phone(data.get("phone"))
    blood_type = clean_blood_type(data.get("blood_type"))

    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email"}), 400

    if not phone:
        return jsonify({"success": False, "message": "Invalid phone"}), 400

    if not blood_type:
        return jsonify({"success": False, "message": "Invalid blood type"}), 400

    user_id = query_db("""
        INSERT INTO UserAccount
        (first_name,last_name,age,gender,email,password_hash,phone,role)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Recipient')
    """, (
        data.get("first_name"),
        data.get("last_name"),
        data.get("age"),
        data.get("gender"),
        email,
        data.get("password"),
        phone
    ), fetch=False)

    if not user_id:
        return jsonify({"success": False, "message": "User creation failed"}), 500

    recipient_id = query_db("""
        INSERT INTO Recipient
        (user_id,blood_type,medical_condition)
        VALUES (%s,%s,%s)
    """, (
        user_id,
        blood_type,
        data.get("medical_condition", "")
    ), fetch=False)

    return jsonify({"success": True, "user_id": user_id, "recipient_id": recipient_id})


# =====================================================
# BLOOD UNIT
# =====================================================

@app.route("/api/blood-units", methods=["POST"])
def add_blood_unit():
    data = request.json or {}

    blood_type = clean_blood_type(data.get("blood_type"))

    if not blood_type:
        return jsonify({"success": False, "message": "Invalid blood type"}), 400

    blood_unit_id = query_db("""
        INSERT INTO BloodUnit
        (hospital_id,donor_id,blood_type,component_type,quantity_ml,donation_date,expiry_date,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Available')
    """, (
        data.get("hospital_id"),
        data.get("donor_id"),
        blood_type,
        data.get("component_type", "Whole Blood"),
        data.get("quantity_ml"),
        data.get("donation_date"),
        data.get("expiry_date")
    ), fetch=False)

    return jsonify({"success": True, "blood_unit_id": blood_unit_id})


# =====================================================
# DONATION
# =====================================================

@app.route("/api/donations/register", methods=["POST"])
def register_donation():
    data = request.json or {}

    blood_type = clean_blood_type(data.get("blood_type"))

    if not blood_type:
        return jsonify({"success": False, "message": "Invalid blood type"}), 400

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
            "success": True,
            "donation_id": result[5],
            "blood_unit_id": result[6]
        })

    finally:
        if conn:
            conn.close()


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)git status