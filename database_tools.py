# database_tools.py
import sqlite3
import os
import pandas as pd  # Pastikan pandas sudah terinstal
from typing import List, Dict, Any, Optional

# Database file path (diubah ke nama database baru)
DB_PATH = "football_data.db"

def init_database():
    """
    Inisialisasi database dengan data sepak bola dari file CSV.
    Fungsi ini akan memuat file-file yang ditentukan dalam 'csv_files_to_load'.
    """
    
    # --- PERUBAHAN UTAMA DI SINI ---
    # Daftar file CSV yang akan dimuat.
    # Hanya muat 3 file yang Anda tentukan.
    csv_files_to_load = {
        "players": "players.csv",
        "clubs": "clubs.csv",
        "player_valuations": "player_valuations.csv"
    }
    # ---------------------------------
    
    conn = sqlite3.connect(DB_PATH)
    
    loaded_files = []
    errors = []

    print(f"Memulai inisialisasi database di {DB_PATH}...")
    print("Membaca file CSV dan memuat ke database...")

    for table_name, file_name in csv_files_to_load.items():
        try:
            # Periksa apakah file CSV ada
            if os.path.exists(file_name):
                # Baca file CSV 10 data pertama 
                df = pd.read_csv(file_name, nrows=10)
                
                # Muat dataframe ke tabel SQLite
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                
                loaded_files.append(file_name)
                print(f"   [OK] Berhasil memuat {file_name} ke tabel '{table_name}'.")
            else:
                # Laporkan jika file tidak ditemukan
                error_msg = f"File {file_name} tidak ditemukan."
                errors.append(error_msg)
                print(f"   [SKIPPED] Peringatan: {error_msg} Tabel '{table_name}' dilewati.")

        except Exception as e:
            # Laporkan error lain
            error_msg = f"Gagal memuat {file_name}: {e}"
            errors.append(error_msg)
            print(f"   [ERROR] {error_msg}")

    conn.commit()
    conn.close()
    
    if not loaded_files:
        return f"Database GAGAL diinisialisasi. Tidak ada file CSV yang ditemukan. Errors: {', '.join(errors)}"
    
    success_msg = f"Database football berhasil diinisialisasi. Berhasil memuat: {', '.join(loaded_files)}."
    if errors:
        success_msg += f" Gagal/dilewati: {', '.join(errors)}."
    
    print("Inisialisasi database selesai.")
    return success_msg

def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute an SQL query and return the results as a list of dictionaries
    (Fungsi ini tidak berubah dari file asli)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [{k: row[k] for k in row.keys()} for row in rows]
        else:
            result = [{"affected_rows": cursor.rowcount}]
            conn.commit()
            
        conn.close()
        return result
    
    except sqlite3.Error as e:
        return [{"error": str(e)}]

def get_table_schema() -> Dict[str, List[Dict[str, str]]]:
    """
    Get the schema of all tables in the database
    (Fungsi ini tidak berubah dari file asli)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "pk": bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        return schema
    
    except sqlite3.Error as e:
        return {"error": str(e)}

# Function to be used as a tool in the LangGraph agent
def text_to_sql(sql_query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the database
    (Fungsi ini tidak berubah dari file asli)
    """
    if not os.path.exists(DB_PATH):
        print("Database tidak ditemukan, menjalankan init_database()...")
        init_database()
    
    try:
        results = execute_sql_query(sql_query)
        return {
            "query": sql_query,
            "results": results
        }
    except Exception as e:
        return {
            "query": sql_query,
            "results": [{"error": str(e)}]
        }

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the database schema to help with query construction
    (Fungsi ini tidak berubah dari file asli)
    """
    if not os.path.exists(DB_PATH):
        print("Database tidak ditemukan, menjalankan init_database()...")
        init_database()
    
    schema = get_table_schema()
    
    sample_data = {}
    for table_name in schema.keys():
        if isinstance(table_name, str):
            try:
                sample_data[table_name] = execute_sql_query(f"SELECT * FROM {table_name} LIMIT 3")
            except:
                pass
    
    return {
        "schema": schema,
        "sample_data": sample_data
    }

# Script to create the database when run directly
if __name__ == "__main__":
    print("Menjalankan database_tools.py sebagai script utama...")
    print(init_database())