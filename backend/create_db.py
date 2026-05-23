import pymysql
import json
from pathlib import Path

def create_db():
    # Load settings.json directly to avoid complex imports
    config_path = Path(__file__).resolve().parent / "config" / "settings.json"
    if not config_path.exists():
        print("settings.json not found")
        return
        
    data = json.loads(config_path.read_text(encoding="utf-8"))
    db_url = data.get("database_url", "mysql+pymysql://root:root@127.0.0.1:3306/visionid_ai?charset=utf8mb4")
    
    # Parse connection string: mysql+pymysql://root:root@127.0.0.1:3306/visionid_ai?charset=utf8mb4
    parts = db_url.split("://")[1].split("@")
    user_pass = parts[0].split(":")
    user = user_pass[0]
    password = user_pass[1]
    
    host_port_db = parts[1].split("/")[0].split(":")
    host = host_port_db[0]
    port = 3306
    if len(host_port_db) > 1:
        port = int(host_port_db[1])
    
    db_name = parts[1].split("/")[1].split("?")[0]
    
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{db_name}' ensured.")
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_db()
