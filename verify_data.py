import mysql.connector

def verify_data():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Nani1118@",    
            database="waterborne_db",
            port=3306,
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor(dictionary=True)
        
        print("Checking users table for test user...")
        cursor.execute("SELECT username, role, full_name, phone_number FROM users WHERE username = 'test_asha_1'")
        user = cursor.fetchone()
        
        if user:
            print(f"Found user: {user['username']}")
            print(f"- Full Name: {user['full_name']}")
            print(f"- Phone: {user['phone_number']}")
            print(f"- Role: {user['role']}")
        else:
            print("Test user not found.")
            
        conn.close()
    except Exception as e:
        print(">>> ERROR <<<", e)

if __name__ == "__main__":
    verify_data()
