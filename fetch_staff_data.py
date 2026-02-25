import mysql.connector

def fetch_all_staff():
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
        
        print("Fetching all users with roles 'asha_worker' or 'volunteer'...")
        cursor.execute("SELECT id, username, full_name, phone_number, role FROM users WHERE role IN ('asha_worker', 'volunteer')")
        users = cursor.fetchall()
        
        print(f"\n{'ID':<5} | {'Username':<15} | {'Full Name':<20} | {'Phone':<15} | {'Role':<15}")
        print("-" * 80)
        for u in users:
            print(f"{u['id']:<5} | {u['username']:<15} | {str(u['full_name']):<20} | {str(u['phone_number']):<15} | {u['role']:<15}")
            
        conn.close()
    except Exception as e:
        print(">>> ERROR <<<", e)

if __name__ == "__main__":
    fetch_all_staff()
