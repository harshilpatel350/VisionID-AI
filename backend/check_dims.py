import pymysql
import json
from pathlib import Path

def check_faces():
    config_path = Path(__file__).resolve().parent / "config" / "settings.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    db_url = data.get("database_url")
    
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
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM persons")
        person_count = cursor.fetchone()[0]
        print(f"Total persons: {person_count}")
        
        cursor.execute("SELECT embedding_dim, COUNT(*) FROM face_embeddings GROUP BY embedding_dim")
        dims = cursor.fetchall()
        for dim, count in dims:
            print(f"Dimension {dim}: {count} embeddings")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_faces()
