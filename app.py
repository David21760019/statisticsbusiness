from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

archivo = "datos.xlsx"

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

@app.route("/api/exel/negocio/tipo/<tipo>")
def obtener_tipo_negocio():
    
    return None
@app.route("/")
def inicio():
    return "<h2>Servidor Flask funcionando correctamente 🚀</h2>"


if __name__ == "__main__":
    app.run(debug=True, port=5000)

