import sqlite3

def create_database():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            fullname TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT,
            status TEXT,
            institution TEXT,
            language_proficiency TEXT,
            course TEXT,
            active_batch TEXT,
            preferred_time TEXT,
            exam_preference TEXT,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            state TEXT,
            district TEXT,
            consent INTEGER NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
