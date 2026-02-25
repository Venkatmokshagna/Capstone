import mysql.connector
import os

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Nani1118@",    
            database="waterborne_db",
            port=3306,
            auth_plugin="mysql_native_password"
        )
        return conn
    except Exception as e:
        print(">>> DB ERROR <<<", e)
        return None

def inspect_schema():
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("DESCRIBE users")
    print("Columns in 'users' table:")
    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]})")
    conn.close()

if __name__ == "__main__":
    inspect_schema()
