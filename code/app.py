from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

archivo = "./code/datos.xlsx"

@app.route("/api/excel/negocio/<ciudad>")
def obtener_datos_excel(ciudad = None):
    columnas = ["nom_estab", "longitud", "latitud"]

    try:
        df = pd.read_excel(archivo, sheet_name=ciudad)

        columnas_existentes = [col for col in columnas if col in df.columns]
        columnas_no_encontradas = [col for col in columnas if col not in df.columns]

        if columnas_no_encontradas:
            print(f"⚠️ Columnas no encontradas: {columnas_no_encontradas}")

        if not columnas_existentes:
            return jsonify({"error": "No se encontraron las columnas solicitadas"}), 400

        resultado = df[columnas_existentes]
        return jsonify(resultado.to_dict(orient="records"))

    except FileNotFoundError:
        return jsonify({"error": f"No se encontró el archivo {archivo}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/excel/negociotipo/<ciudad>")
def obtener_negocio_tipo(ciudad=None):
    columnas = ["nom_estab", "longitud", "latitud"]

    try:
        # Leer hoja según la ciudad
        df = pd.read_excel(archivo, sheet_name=ciudad)

        # Validar columnas
        columnas_existentes = [col for col in columnas if col in df.columns]
        columnas_no_encontradas = [col for col in columnas if col not in df.columns]

        if columnas_no_encontradas:
            print(f"⚠️ Columnas no encontradas: {columnas_no_encontradas}")

        if not columnas_existentes:
            return jsonify({"error": "No se encontraron las columnas solicitadas"}), 400

        # --------------------------
        # FILTRO POR NOMBRE
        # --------------------------
        nombre = request.args.get("nombre", None)

        if nombre:
            df = df[df["nom_estab"].astype(str).str.contains(nombre, case=False, na=False)]

        # Si después del filtro no hay resultados
        if df.empty:
            return jsonify({"mensaje": "No se encontraron coincidencias"}), 404

        # Respuesta con columnas seleccionadas
        resultado = df[columnas_existentes]
        return jsonify(resultado.to_dict(orient="records"))

    except FileNotFoundError:
        return jsonify({"error": f"No se encontró el archivo {archivo}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return None
@app.route("/api/excel/negocio/buscar/<ciudad>")
def buscar_negocios(ciudad=None):
    columnas = ["nom_estab", "longitud", "latitud", "nomb_asent"]

    try:
        # Cargar hoja del Excel
        df = pd.read_excel(archivo, sheet_name=ciudad)

        # Validar columnas necesarias
        columnas_existentes = [col for col in columnas if col in df.columns]
        if not columnas_existentes:
            return jsonify({"error": "Las columnas necesarias no existen en esta hoja"}), 400

        # -----------------------------
        # Filtros recibidos por query
        # -----------------------------
        nombre = request.args.get("nombre")
        asent = request.args.get("asent")

        # Filtro por nombre del establecimiento
        if nombre:
            df = df[df["nom_estab"].astype(str).str.contains(nombre, case=False, na=False)]

        # Filtro por asentamiento / colonia
        if asent:
            df = df[df["nomb_asent"].astype(str).str.contains(asent, case=False, na=False)]

        # Si no hay coincidencias
        if df.empty:
            return jsonify({"mensaje": "No se encontraron coincidencias con los filtros proporcionados"}), 404

        # Respuesta final
        resultado = df[columnas_existentes]
        return jsonify(resultado.to_dict(orient="records"))

    except FileNotFoundError:
        return jsonify({"error": f"No se encontró el archivo {archivo}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def inicio():
    return "<h2>Servidor Flask funcionando correctamente</h2>"


if __name__ == "__main__":
    app.run(debug=True, port=5000)

