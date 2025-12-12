"""
front.py actualizado con soporte JWT + autenticación + registro
Sin cambios drásticos en diseño.
"""

import streamlit as st
import requests
import pandas as pd
from PIL import Image
from typing import Optional, Tuple, Dict

# -----------------------------------------
# CONFIGURACIÓN BÁSICA
# -----------------------------------------
st.set_page_config(page_title="Mapa de Negocios - StatisticsBusiness", layout="wide")

API_AUTH = "http://localhost/api/auth"
API_BASE = "http://localhost/api/sqlite/negocio"

# ---- Guardamos token en sesión ----
if "token" not in st.session_state:
    st.session_state.token = None

if "modo_auth" not in st.session_state:
    st.session_state.modo_auth = "login"  # opciones: login | register


# -----------------------------------------
# CARGAR LOGO (si existe)
# -----------------------------------------
def mostrar_logo(path: str = "logo.png", width: int = 220) -> None:
    try:
        logo = Image.open(path)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=width)
    except FileNotFoundError:
        st.caption("")


mostrar_logo()

st.title("StatisticsBusiness — Buscador de Negocios por Ciudad")
st.markdown(
    "Consulta establecimientos por ciudad y colonia, visualiza su ubicación en el mapa "
    "y obtén una estimación básica de probabilidad de éxito."
)
st.divider()


# =====================================================
# 🔐 AUTH (LOGIN / REGISTRO)
# =====================================================

def login_usuario(username: str, password: str):
    try:
        r = requests.post(f"{API_AUTH}/login", json={"username": username, "password": password})
        return r.json(), r.status_code
    except:
        return {"error": "No se pudo conectar con la API"}, 500


def registrar_usuario(username: str, password: str):
    try:
        r = requests.post(f"{API_AUTH}/register", json={"username": username, "password": password})
        return r.json(), r.status_code
    except:
        return {"error": "No se pudo conectar con la API"}, 500


with st.sidebar:
    st.subheader("🔐 Autenticación")

    # --------------------------------------------------------------
    # FORMULARIO DE REGISTRO
    # --------------------------------------------------------------
    if st.session_state.modo_auth == "register" and st.session_state.token is None:
        st.info("Crear una nueva cuenta")

        username = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        password2 = st.text_input("Repetir contraseña:", type="password")

        if st.button("Registrarme"):
            if password != password2:
                st.error("Las contraseñas no coinciden.")
            else:
                data, status = registrar_usuario(username, password)
                if status == 201:
                    st.success("Registro exitoso. Ahora inicia sesión.")
                    st.session_state.modo_auth = "login"
                else:
                    st.error(str(data))

        if st.button("Ya tengo cuenta"):
            st.session_state.modo_auth = "login"

    # --------------------------------------------------------------
    # FORMULARIO DE LOGIN
    # --------------------------------------------------------------
    elif st.session_state.token is None:
        st.info("Iniciar sesión")

        username = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")

        if st.button("Ingresar"):
            data, status = login_usuario(username, password)
            if status == 200 and "token" in data:
                st.session_state.token = data["token"]
                st.success("Inicio de sesión exitoso 🎉")
            else:
                st.error(str(data))

        if st.button("Crear una cuenta"):
            st.session_state.modo_auth = "register"

    # --------------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------------
    else:
        st.success("Estás autenticado ✔")

        if st.button("Cerrar sesión"):
            st.session_state.token = None
            st.session_state.modo_auth = "login"
            st.info("Sesión cerrada.")


# No permitir usar la app sin login
if st.session_state.token is None:
    st.warning("Inicia sesión o regístrate para usar la aplicación.")
    st.stop()


# -----------------------------------------
# FUNCIÓN PARA CONSULTAR EL ENDPOINT
# -----------------------------------------
def consultar_api(ciudad_input: str,
                  nombre_input: Optional[str] = None,
                  asent_input: Optional[str] = None,
                  timeout: int = 10) -> Tuple[Dict, int]:

    url = f"{API_BASE}/buscar/{ciudad_input}"
    params = {}

    if nombre_input:
        params["nombre"] = nombre_input
    if asent_input:
        params["asent"] = asent_input

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)

        # Token expirado
        if response.status_code == 401:
            return {"error": "Token expirado o inválido. Vuelve a iniciar sesión."}, 401

        return response.json(), response.status_code
    except requests.RequestException as exc:
        return {"error": str(exc)}, 500
    except ValueError:
        return {"error": "Respuesta JSON inválida"}, 500


# -----------------------------------------
# SIDEBAR — filtros rápidos
# -----------------------------------------
with st.sidebar:
    st.header("Filtros de búsqueda")
    ciudad = st.text_input("Ciudad (hoja Excel):")
    nombre = st.text_input("Nombre del negocio:")
    asent = st.text_input("Colonia / asentamiento:")
    buscar = st.button("Buscar")
    st.markdown("---")


# 📌 Si no hay ciudad, aviso
if not ciudad:
    st.info("Introduce una ciudad en el panel lateral.")
    st.stop()


# -----------------------------------------
# RESULTADOS
# -----------------------------------------
if buscar:
    with st.spinner("Consultando API..."):
        data, status = consultar_api(ciudad, nombre, asent)

    if status != 200:
        st.error(f"Error ({status}): {data}")
        st.stop()

    try:
        df = pd.DataFrame(data)
    except Exception as exc:
        st.error(f"Error al procesar datos: {exc}")
        st.stop()

    st.success(f"Resultados encontrados: {len(df)}")

    col_map, col_tabla = st.columns([1.5, 1])

    # ---------------- MAPA ----------------
    with col_map:
        st.subheader("Mapa de resultados")
        if {"latitud", "longitud"}.issubset(df.columns):
            df_map = df.rename(columns={"latitud": "lat", "longitud": "lon"})
            df_map["lat"] = pd.to_numeric(df_map["lat"], errors="coerce")
            df_map["lon"] = pd.to_numeric(df_map["lon"], errors="coerce")
            df_clean = df_map.dropna(subset=["lat", "lon"])
            if df_clean.empty:
                st.info("No hay coordenadas válidas para mapa.")
            else:
                st.map(df_clean[["lat", "lon"]], size=3)

    # --------------- TABLA ----------------
    with col_tabla:
        st.subheader("Tabla y estadísticas")
        st.dataframe(df)

    st.divider()

    # --------------- PROBABILIDAD ----------------
    st.subheader(f"Probabilidad de éxito en colonia: {asent or '—'}")

    if asent and "nomb_asent" in df.columns:
        df_asent = df[df["nomb_asent"].astype(str).str.contains(asent, case=False, na=False)]

        if not df_asent.empty:
            total = len(df_asent)

            prob = 100 - (total / 6) * 80
            prob = max(5, min(prob, 100))

            st.metric(
                "Probabilidad estimada",
                f"{prob:.2f} %",
                delta=f"{total} negocios en la colonia"
            )

            st.write("### Negocios en la colonia")
            st.dataframe(df_asent)
        else:
            st.info("No hay negocios en esa colonia.")
    else:
        st.info("Escribe una colonia para calcular probabilidad.")

    st.divider()

    st.caption("StatisticsBusiness — análisis por concentración comercial.")
