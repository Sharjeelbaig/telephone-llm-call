import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Query
from utils.initialize_db import initialize_db

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

if DATABASE_URL:
    try:
        initialize_db(psycopg2, DATABASE_URL)
    except Exception as e:
        print(f"Warning: Failed to initialize database on startup: {e}")

app = FastAPI(title="Voice AI Patient Registration API", version="1.0.0")

def envelope(data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
    return {"data": data, "error": error}

@app.get("/")
def health_check():
    return envelope(data={"status": "ok", "message": "Backend running"})

@app.get("/db")
def db_health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_DATE;")
        date = cursor.fetchone()
        conn.close()
        return envelope(data={"status": "ok", "date": list(date.values())})
    except Exception as e:
        return envelope(error=f"DB connection failed: {str(e)}")

@app.post("/patients", status_code=201)
async def create_patient(request: Request):
    raw = await request.json()
    payload = raw

    if "message" in raw and "toolCalls" in raw["message"]:
        try:
            calls = raw["message"]["toolCalls"]
            payload = calls["function"]["arguments"] if isinstance(calls, list) else calls["function"]["arguments"]
        except Exception:
            payload = raw

    fields = [
        "first_name", "last_name", "date_of_birth", "sex", "phone_number",
        "email", "address_line_1", "address_line_2", "city", "state", "zip_code",
        "insurance_provider", "insurance_member_id", "preferred_language",
        "emergency_contact_name", "emergency_contact_phone"
    ]
    for f in fields:
        payload.setdefault(f, None)

    now = datetime.utcnow().isoformat()
    payload["patient_id"] = payload.get("patient_id") or str(uuid.uuid4())
    payload["preferred_language"] = payload.get("preferred_language") or "English"
    payload["created_at"] = now
    payload["updated_at"] = now

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (
            patient_id, first_name, last_name, date_of_birth, sex,
            phone_number, email, address_line_1, address_line_2,
            city, state, zip_code, insurance_provider,
            insurance_member_id, preferred_language,
            emergency_contact_name, emergency_contact_phone,
            created_at, updated_at
        ) VALUES (
            %(patient_id)s, %(first_name)s, %(last_name)s, %(date_of_birth)s, %(sex)s,
            %(phone_number)s, %(email)s, %(address_line_1)s, %(address_line_2)s,
            %(city)s, %(state)s, %(zip_code)s, %(insurance_provider)s,
            %(insurance_member_id)s, %(preferred_language)s,
            %(emergency_contact_name)s, %(emergency_contact_phone)s,
            %(created_at)s, %(updated_at)s
        )
    ''', payload)
    conn.commit()
    conn.close()

    return envelope(data=payload)

@app.get("/patients")
def list_patients(
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM patients WHERE deleted_at IS NULL"
    params = []

    if last_name:
        query += " AND LOWER(last_name) = LOWER(%s)"
        params.append(last_name)
    if date_of_birth:
        query += " AND date_of_birth = %s"
        params.append(date_of_birth)
    if phone_number:
        clean_phone = "".join(filter(str.isdigit, phone_number))[-10:]
        query += " AND phone_number = %s"
        params.append(clean_phone)

    cursor.execute(query, params)
    patients = cursor.fetchall()
    conn.close()
    return envelope(data=[dict(p) for p in patients])

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = %s AND deleted_at IS NULL", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    if patient:
        return envelope(data=dict(patient))
    return envelope(error="Patient not found")

@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, patient: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    patient["patient_id"] = patient_id
    patient["updated_at"] = datetime.utcnow().isoformat()
    
    fields = [
        "first_name", "last_name", "date_of_birth", "sex", "phone_number",
        "email", "address_line_1", "address_line_2", "city", "state", "zip_code",
        "insurance_provider", "insurance_member_id", "preferred_language",
        "emergency_contact_name", "emergency_contact_phone"
    ]
    for f in fields:
        patient.setdefault(f, None)

    cursor.execute('''
        UPDATE patients SET
            first_name = COALESCE(%(first_name)s, first_name),
            last_name = COALESCE(%(last_name)s, last_name),
            date_of_birth = COALESCE(%(date_of_birth)s, date_of_birth),
            sex = COALESCE(%(sex)s, sex),
            phone_number = COALESCE(%(phone_number)s, phone_number),
            email = COALESCE(%(email)s, email),
            address_line_1 = COALESCE(%(address_line_1)s, address_line_1),
            address_line_2 = COALESCE(%(address_line_2)s, address_line_2),
            city = COALESCE(%(city)s, city),
            state = COALESCE(%(state)s, state),
            zip_code = COALESCE(%(zip_code)s, zip_code),
            insurance_provider = COALESCE(%(insurance_provider)s, insurance_provider),
            insurance_member_id = COALESCE(%(insurance_member_id)s, insurance_member_id),
            preferred_language = COALESCE(%(preferred_language)s, preferred_language),
            emergency_contact_name = COALESCE(%(emergency_contact_name)s, emergency_contact_name),
            emergency_contact_phone = COALESCE(%(emergency_contact_phone)s, emergency_contact_phone),
            updated_at = %(updated_at)s
        WHERE patient_id = %(patient_id)s AND deleted_at IS NULL
    ''', patient)
    conn.commit()
    conn.close()

    return envelope(data={"message": "Updated successfully", "patient_id": patient_id})

@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE patients SET deleted_at = %s WHERE patient_id = %s AND deleted_at IS NULL
    ''', (now, patient_id))
    conn.commit()
    conn.close()

    return envelope(data={"message": "Soft deleted", "patient_id": patient_id})