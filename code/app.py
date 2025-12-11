"""
API Flask para consultar negocios desde un archivo Excel y devolver
resultados filtrados por ciudad, nombre y asentamiento.
"""

from flask import Flask, jsonify, request
import pandas as pd
import sqlite3

app = Flask(__name__)

ARCHIVO = "./code/datos.xlsx"
DB_FILE = "./code/negocios.db"
TABLE_NAME = "negocios"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/sqlite/negocio/buscar/<ciudad>", methods=["GET"])
def buscar_negocios_sqlite(ciudad=None):
    """
    Versión para SQL para buscar negocios por ciudad.
    """
    try:
        nombre = request.args.get("nombre", "")
        asent = request.args.get("asent", "")
        
        conn = get_db_connection()
        
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
        

@app.route("/api/excel/negocio/buscar/<ciudad>")
def buscar_negocios(ciudad=None):
    """
    Busca negocios dentro de una hoja del archivo Excel especificada por la ciudad.
    
    """

    columnas = ["nom_estab", "longitud", "latitud", "nomb_asent"]

    try:
        df = pd.read_excel(ARCHIVO, sheet_name=ciudad)

        columnas_existentes = [
            col for col in columnas if col in df.columns
        ]
        if not columnas_existentes:
            return (
                jsonify(
                    {"error": "Las columnas necesarias no existen en esta hoja"}
                ),
                400,
            )


        nombre = request.args.get("nombre")
        asent = request.args.get("asent")

        if nombre:
            df = df[
                df["nom_estab"]
                .astype(str)
                .str.contains(nombre, case=False, na=False)
            ]

        if asent:
            df = df[
                df["nomb_asent"]
                .astype(str)
                .str.contains(asent, case=False, na=False)
            ]

        if df.empty:
            return (
                jsonify(
                    {
                        "mensaje": "No se encontraron coincidencias con los filtros proporcionados"
                    }
                ),
                404,
            )

        resultado = df[columnas_existentes]
        return jsonify(resultado.to_dict(orient="records"))

    except FileNotFoundError:
        return jsonify({"error": f"No se encontró el archivo {ARCHIVO}"}), 404

    except Exception as exc: 
        return jsonify({"error": str(exc)}), 500


@app.route("/")
def inicio():
    return "<h2>Flask funcionando </h2>"



if __name__ == "__main__":
    app.run(debug=True, port=5000)
