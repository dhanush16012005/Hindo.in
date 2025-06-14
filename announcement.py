import sqlite3
import os

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Path to the SQLite database
db_path = os.path.join('instance', 'hindo.db')

def create_announcements_table():
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the announcements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS studentcourse (
            id INTEGER NOT NULL,
            fullname TEXT NOT NULL,
            course TEXT NOT NULL,
            batch_id TEXT NOT NULL
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Announcements table created successfully.")

if __name__ == '__main__':
    create_announcements_table()
