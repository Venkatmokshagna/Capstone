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
        
        print("Creating 'ai_water_analysis' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_water_analysis (
                id                 INT AUTO_INCREMENT PRIMARY KEY,
                village_id         INT,
                image_path         VARCHAR(255),
                drinkable          BOOLEAN,
                contamination_prob DECIMAL(4,3),
                confidence         DECIMAL(4,3),
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (village_id) REFERENCES villages(id)
            )
        """)
        print("- Created 'ai_water_analysis' successfully or already exists.")
            
        conn.commit()
        print("Schema updated successfully.")
            
        conn.close()
    except Exception as e:
        print(">>> ERROR <<<", e)

if __name__ == "__main__":
    update_schema()
