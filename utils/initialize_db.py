def initialize_db(psycopg2, database_url: str):
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            sex TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT,
            address_line_1 TEXT NOT NULL,
            address_line_2 TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            insurance_provider TEXT,
            insurance_member_id TEXT,
            preferred_language TEXT DEFAULT 'English',
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        );
    ''')
    conn.commit()
    conn.close()