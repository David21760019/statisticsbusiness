import streamlit as st
import requests
import pandas as pd

# -----------------------------------------
# CONFIGURACIÓN BÁSICA
# -----------------------------------------
st.set_page_config(page_title="Mapa de Negocios", layout="wide")

API_BASE = "http://localhost/api/excel/negocio"

st.title("📍 Buscador de Negocios por Ciudad con Mapa")


# -----------------------------------------
# INPUTS DEL USUARIO
# -----------------------------------------
ciudad = st.text_input("Ciudad (nombre de la hoja Excel):")

nombre = st.text_input("Nombre del negocio (opcional):")
asent = st.text_input("Asentamiento / Colonia (opcional):")

buscar = st.button("Buscar")


# -----------------------------------------
# FUNCIÓN PARA CONSULTAR EL ENDPOINT
# -----------------------------------------
def consultar_api(ciudad, nombre=None, asent=None):
    url = f"{API_BASE}/buscar/{ciudad}"

    params = {}
    if nombre:
        params["nombre"] = nombre
    if asent:
        params["asent"] = asent

    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500


# -----------------------------------------
# RESULTADOS
# -----------------------------------------
if buscar:
    if not ciudad:
        st.error("Debes escribir una ciudad (nombre de la hoja).")
        st.stop()

    st.info("Consultando API...")

    data, status = consultar_api(ciudad, nombre, asent)
    if status != 200:
        st.error(data)
        st.stop()

    df = pd.DataFrame(data)

    st.success(f"Resultados encontrados: {len(df)}")

    st.dataframe(df)

    # -------------------------
    # MOSTRAR EN MAPA
    # -------------------------
    if "latitud" in df.columns and "longitud" in df.columns:
        st.subheader("🗺️ Mapa de resultados")

        df_map = df.rename(columns={"latitud": "lat", "longitud": "lon"})

        st.map(df_map, size='size')

        # Lista de puntos con descripción
        st.subheader("📌 Marcadores:")
        for _, row in df.iterrows():
            st.write(f"**{row['nom_estab']}** — ({row['latitud']}, {row['longitud']})")

    else:
        st.warning("El resultado no contiene coordenadas para mostrar en el mapa.")

