import sqlite3
from pathlib import Path

def upgrade():
    db_path = Path("db/visitors.db")
    if not db_path.exists():
        print("Database not found at db/visitors.db")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check if the status column already exists
        cursor.execute("PRAGMA table_info(visitors)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'status' not in columns:
            # Add status column with default value 'active'
            cursor.execute("ALTER TABLE visitors ADD COLUMN status TEXT DEFAULT 'active'")
            # Update all existing records to have status 'active'
            cursor.execute("UPDATE visitors SET status = 'active' WHERE status IS NULL")
            conn.commit()
            print("Successfully added status column to visitors table")
        else:
            print("Status column already exists in visitors table")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
