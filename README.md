# Voice AI Patient Registration System

A voice-powered patient registration backend and REST API. This system allows callers to interact with a conversational Voice AI agent (powered by Vapi) to complete standard U.S. patient registration over the phone. Registered patient details are validated, stored in a persistent NeonDB PostgreSQL database, and exposed via a REST API.

---

## 📞 Live Demo & Deployment

* **API Base URL:** `https://telephone-llm-call.vercel.app/`
* **Phone Number:** `+1 (213) 464 0359` *(+1 (213) 464 0359)*

---

## 🏗️ System Architecture

1. **Caller (Phone)** ↔ **Voice AI Agent (Vapi)**
2. **Voice AI Agent** ↔ **FastAPI Webhook (`POST /patients`)**
3. **FastAPI Webhook** ↔ **NeonDB (PostgreSQL Database)**
4. **REST API Client** ↔ **FastAPI Service Endpoints**

---

## 🚀 Tech Stack & Justifications

| Component | Technology | Justification |
| :--- | :--- | :--- |
| **Voice AI & Telephony** | Vapi AI | Handles real-time Speech-to-Text (STT), LLM conversational logic, and Text-to-Speech (TTS) with low latency. |
| **Backend Framework** | FastAPI (Python 3.12) | Lightweight, asynchronous framework with built-in Pydantic data validation and fast REST endpoint execution. |
| **Database** | NeonDB (PostgreSQL) | Serverless PostgreSQL database that provides persistent storage across serverless function reboots and deployments. |
| **Deployment** | Vercel | Serverless hosting providing fast response times and HTTPS endpoints for Vapi webhooks. |

---

## 🔑 Environment Variables

The application requires the following environment variable configured in your deployment or local `.env` file:

```env
DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"
```

---

## 🛠️ Local Setup & Development

1. **Clone the Repository:**
   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd <YOUR_REPOSITORY_DIRECTORY>
   ```

2. **Install Dependencies:**
   ```bash
   pip install fastapi uvicorn psycopg2-binary pydantic
   ```

3. **Set Up Environment Variables:**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL="postgresql://<USER>:<PASSWORD>@<HOST>/<DATABASE>?sslmode=require"
   ```

4. **Run Local Server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Test Health Endpoint:**
   Navigate to `http://localhost:8000/` or `http://localhost:8000/db`.

---

## 📡 REST API Reference

All API responses follow a consistent envelope structure:
```json
{
  "data": { ... },
  "error": null
}
```

### 1. Health Checks

#### `GET /`
* **Description:** Health check verifying the web service is running.
* **Response:**
  ```json
  {
    "data": {
      "status": "ok",
      "message": "Backend running"
    },
    "error": null
  }
  ```

#### `GET /db`
* **Description:** Verifies database connectivity.
* **Response:**
  ```json
  {
    "data": {
      "status": "ok",
      "date": ["2026-10-17"]
    },
    "error": null
  }
  ```

---

### 2. Patient Management Endpoints

#### `POST /patients`
* **Description:** Creates a new patient record. Accepts both standard JSON REST requests and nested tool-call webhooks sent by Vapi.
* **Request Body Example:**
  ```json
  {
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "sex": "Female",
    "phone_number": "5551234567",
    "email": "jane.doe@example.com",
    "address_line_1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "insurance_provider": "Blue Cross",
    "insurance_member_id": "BC123456789",
    "preferred_language": "English",
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "5559876543"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "data": {
      "patient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "first_name": "Jane",
      "last_name": "Doe",
      "date_of_birth": "1990-05-15",
      "created_at": "2026-10-17T12:00:00.000000",
      "updated_at": "2026-10-17T12:00:00.000000"
    },
    "error": null
  }
  ```

#### `GET /patients`
* **Description:** Lists all active patient records (excluding soft-deleted records).
* **Query Parameters (Optional):**
  * `last_name`: Filter by patient last name (case-insensitive).
  * `date_of_birth`: Filter by date of birth (`YYYY-MM-DD` or `MM/DD/YYYY`).
  * `phone_number`: Filter by 10-digit phone number.
* **Example:** `GET /patients?last_name=Doe&phone_number=5551234567`

#### `GET /patients/{patient_id}`
* **Description:** Retrieves a single patient by their unique `patient_id` (UUID).
* **Response:** Returns patient object or 404 error if not found / deleted.

#### `PUT /patients/{patient_id}`
* **Description:** Updates fields for an existing patient (supports partial updates). Updates the `updated_at` UTC timestamp.

#### `DELETE /patients/{patient_id}`
* **Description:** Soft-deletes a patient record by populating the `deleted_at` UTC timestamp without removing the record from table storage.

---

## 📋 Data Model Specification

| Field | Type | Required | Description / Rules |
| :--- | :--- | :--- | :--- |
| `patient_id` | UUID | Auto | Unique identifier |
| `first_name` | String | Yes | 1–50 characters |
| `last_name` | String | Yes | 1–50 characters |
| `date_of_birth` | String | Yes | Date string |
| `sex` | Enum | Yes | `Male`, `Female`, `Other`, `Decline to Answer` |
| `phone_number` | String | Yes | 10-digit U.S. phone number |
| `email` | String | No | Valid email address |
| `address_line_1` | String | Yes | Street address |
| `address_line_2` | String | No | Apt / Suite / Unit |
| `city` | String | Yes | City name |
| `state` | String | Yes | 2-letter U.S. state code |
| `zip_code` | String | Yes | 5-digit ZIP code |
| `insurance_provider` | String | No | Insurance company name |
| `insurance_member_id` | String | No | Member/subscriber ID |
| `preferred_language` | String | No | Default: `English` |
| `emergency_contact_name` | String | No | Full name |
| `emergency_contact_phone` | String | No | 10-digit phone number |
| `created_at` | Timestamp | Auto | UTC creation time |
| `updated_at` | Timestamp | Auto | UTC modification time |
| `deleted_at` | Timestamp | Auto | UTC soft-deletion time |

---

## ⚙️ Architectural Trade-offs & Known Limitations

1. **Database Migration (SQLite → NeonDB):** SQLite is ideal for quick local development, but file-based databases do not persist across Vercel serverless function container reboots. Migrating to NeonDB PostgreSQL ensures data persistence while retaining a lightweight architecture.
2. **Soft Deletes:** Patient records are retained in table storage with a `deleted_at` timestamp rather than hard-deleted, maintaining record history and auditability.
3. **Input Sanitization:** Basic validation and string normalization are performed on the server side (e.g. state code uppercase formatting, phone number digit cleaning) to ensure data cleanlines.
