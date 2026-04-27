import sqlite3

def migrate():
    print("Starting migration...")
    conn = sqlite3.connect('instance/app.db')
    c = conn.cursor()
    
    # 1. Add gmail_thread_id column
    try:
        c.execute("ALTER TABLE email_ticket ADD COLUMN gmail_thread_id VARCHAR(200)")
        print("Added gmail_thread_id column.")
    except sqlite3.OperationalError as e:
        print("Column gmail_thread_id might already exist:", e)
        
    # 2. Create ticket_message table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ticket_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender VARCHAR(50) NOT NULL,
            body TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(ticket_id) REFERENCES email_ticket(id)
        )
    ''')
    print("Created ticket_message table.")
    
    # 3. Migrate data
    c.execute("SELECT COUNT(*) FROM ticket_message")
    if c.fetchone()[0] == 0:
        # Migrate data
        try:
            c.execute("SELECT id, body, created_at FROM email_ticket")
            rows = c.fetchall()
            for row in rows:
                ticket_id, body, created_at = row
                if body:
                    c.execute(
                        "INSERT INTO ticket_message (ticket_id, sender, body, created_at) VALUES (?, ?, ?, ?)",
                        (ticket_id, "customer", body, created_at)
                    )
            print(f"Migrated {len(rows)} messages.")
        except sqlite3.OperationalError as e:
            print("Error selecting body from email_ticket (maybe already dropped?):", e)
    else:
        print("Migration data already exists.")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
