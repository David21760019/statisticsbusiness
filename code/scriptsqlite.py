import sqlite3
import os

# Obtener ruta absoluta del archivo negocios.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "negocios.db")

def crear_tabla_usuarios():
    print(f"Creando base de datos en: {DB_FILE}")

    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        );
        """
    )

    conn.commit()
    conn.close()
    print("Tabla 'users' creada correctamente.")

if __name__ == "__main__":
    crear_tabla_usuarios()
