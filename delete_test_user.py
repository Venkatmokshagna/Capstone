import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Nani1118@",
    database="waterborne_db",
    port=3306,
    auth_plugin="mysql_native_password"
)
cursor = conn.cursor()
cursor.execute("DELETE FROM users WHERE username = 'test_asha_1'")
conn.commit()
print(f"Deleted {cursor.rowcount} row(s).")
conn.close()
