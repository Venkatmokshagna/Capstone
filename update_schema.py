import mysql.connector

def update_schema():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Nani1118@",    
            database="waterborne_db",
            port=3306,
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor()
        
        # Add full_name and phone_number columns
        print("Adding columns to 'users' table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) AFTER id")
            print("- Added 'full_name'")
        except Exception as e:
            print(f"- 'full_name' might already exist: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) AFTER role")
            print("- Added 'phone_number'")
        except Exception as e:
            print(f"- 'phone_number' might already exist: {e}")
            
        conn.commit()
        print("Schema updated successfully.")
        
        # Verify
        cursor.execute("DESCRIBE users")
        print("\nCurrent 'users' table schema:")
        for row in cursor.fetchall():
            print(row)
            
        conn.close()
    except Exception as e:
        print(">>> ERROR <<<", e)

if __name__ == "__main__":
    update_schema()
