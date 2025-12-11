from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_FILE = "negocios.db"
TABLE_NAME = "negocios"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/sqlite/negocio/buscar/<ciudad>", methods=["GET"])
def buscar_negocios(ciudad=None):
    """
    Versión simplificada para buscar negocios por ciudad.
    """
    try:
        # Obtener parámetros de filtro
        nombre = request.args.get("nombre", "")
        asent = request.args.get("asent", "")
        
        conn = get_db_connection()
        
        # Construir consulta dinámica
        query = f"""
            SELECT nom_estab, longitud, latitud, nomb_asent, ciudad
            FROM {TABLE_NAME}
            WHERE ciudad = ? 
        """
        params = [ciudad]
        
        if nombre:
            query += " AND nom_estab LIKE ?"
            params.append(f"%{nombre}%")
            
        if asent:
            query += " AND nomb_asent LIKE ?"
            params.append(f"%{asent}%")
        
        cursor = conn.execute(query, params)
        resultados = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        if not resultados:
            return jsonify({
                "mensaje": "No se encontraron resultados",
                "ciudad": ciudad,
                "filtros": {"nombre": nombre, "asent": asent}
            }), 404
            
        return jsonify({
            "total": len(resultados),
            "resultados": resultados
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sqlite/negocio/buscar/<ciudad>", methods=["GET"])
def buscar_negocios(ciudad=None):
    """
    Versión simplificada para buscar negocios por ciudad.
    """
    try:
        # Obtener parámetros de filtro
        nombre = request.args.get("nombre", "")
        asent = request.args.get("asent", "")
        
        conn = get_db_connection()
        
        # Construir consulta dinámica
        query = f"""
            SELECT nom_estab, longitud, latitud, nomb_asent, ciudad
            FROM {TABLE_NAME}
            WHERE ciudad = ? 
        """
        params = [ciudad]
        
        if nombre:
            query += " AND nom_estab LIKE ?"
            params.append(f"%{nombre}%")
            
        if asent:
            query += " AND nomb_asent LIKE ?"
            params.append(f"%{asent}%")
        
        cursor = conn.execute(query, params)
        resultados = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        if not resultados:
            return jsonify({
                "mensaje": "No se encontraron resultados",
                "ciudad": ciudad,
                "filtros": {"nombre": nombre, "asent": asent}
            }), 404
            
        return jsonify({
            "total": len(resultados),
            "resultados": resultados
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)