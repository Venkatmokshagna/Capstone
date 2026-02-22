import mysql.connector
import sys

def check_db():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Nani1118@",
            port=3306,
            auth_plugin="mysql_native_password"
        )
        print(">>> Connection to MySQL successful.")
        
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE 'waterborne_db'")
        db = cursor.fetchone()
        if db:
            print(">>> Database 'waterborne_db' exists.")
            cursor.execute("USE waterborne_db")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(">>> Tables in 'waterborne_db':", [t[0] for t in tables])
        else:
            print(">>> Database 'waterborne_db' does NOT exist.")
            # I won't create it automatically yet, just report.
        
        conn.close()
    except Exception as e:
        print(">>> Error checking database:", e)
        sys.exit(1)

if __name__ == "__main__":
    check_db()
