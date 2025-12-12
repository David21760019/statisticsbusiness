"""
API Flask con JWT, Rate Limiting, SQLite y Excel
Todo en un solo archivo, lo más simple posible.
"""

from flask import Flask, jsonify, request
import sqlite3
import pandas as pd
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv

load_dotenv()

# ========================================================
# CONFIGURACIÓN
# ========================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "MI_SECRETO_SUPER_SEGURO")

ARCHIVO_EXCEL = "./code/datos.xlsx"
DB_FILE = "./code/negocios.db"
TABLE_NAME = "negocios"

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "100 per hour"],
    storage_uri="memory://"
)

# ========================================================
# JWT - GENERAR Y DECODIFICAR TOKENS
# ========================================================
def generar_token(user_id, username, role="user"):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(
        payload,
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    return token


def decodificar_token(token):
    try:
        return jwt.decode(
            token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return {"error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"error": "Token inválido"}

# ========================================================
# DECORADOR DE AUTENTICACIÓN
# ========================================================
def token_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):

        token = None

        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split()[1]
            except:
                return jsonify({"error": "Formato de token inválido"}), 401

        if not token:
            return jsonify({"error": "Token requerido"}), 401

        datos = decodificar_token(token)

        if "error" in datos:
            return jsonify({"error": datos["error"]}), 401

        return f(current_user=datos, *args, **kwargs)

    return decorador

# ========================================================
# CONEXIÓN A SQLITE
# ========================================================
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ========================================================
# RUTAS DE AUTENTICACIÓN
# ========================================================
@app.route("/api/auth/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    data = request.json

    username = data["username"]
    password = data["password"]

    conn = get_db()

    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Usuario registrado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.json

    username = data["username"]
    password = data["password"]

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()

    if not user:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = generar_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"]
    )

    return jsonify({"token": token})

# ========================================================
# RUTA SQL - BUSCAR NEGOCIOS
# ========================================================
@app.route("/api/sqlite/negocio/buscar/<ciudad>", methods=["GET"])
@token_requerido
@limiter.limit("20 per minute")
def buscar_sqlite(current_user, ciudad):

    nombre = request.args.get("nombre", "")
    asent = request.args.get("asent", "")

    conn = get_db()

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
        return jsonify({"mensaje": "No se encontraron resultados"}), 404

    return jsonify(resultados)

# ========================================================
# RUTA EXCEL - BUSCAR NEGOCIOS
# ========================================================
@app.route("/api/excel/negocio/buscar/<ciudad>")
@token_requerido
@limiter.limit("20 per minute")
def buscar_excel(current_user, ciudad):

    columnas = ["nom_estab", "longitud", "latitud", "nomb_asent"]

    try:
        df = pd.read_excel(ARCHIVO_EXCEL, sheet_name=ciudad)

        columnas_existentes = [c for c in columnas if c in df.columns]
        if not columnas_existentes:
            return jsonify({"error": "Columnas requeridas no existen"}), 400

        nombre = request.args.get("nombre")
        asent = request.args.get("asent")

        if nombre:
            df = df[df["nom_estab"].astype(str).str.contains(nombre, case=False, na=False)]

        if asent:
            df = df[df["nomb_asent"].astype(str).str.contains(asent, case=False, na=False)]

        if df.empty:
            return jsonify({"mensaje": "No se encontraron coincidencias"}), 404

        return jsonify(df[columnas_existentes].to_dict(orient="records"))

    except FileNotFoundError:
        return jsonify({"error": "Archivo Excel no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================================
# HOME
# ========================================================
@app.route("/")
def home():
    return "<h2>API funcionando con JWT + Rate Limiting en un solo archivo</h2>"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
