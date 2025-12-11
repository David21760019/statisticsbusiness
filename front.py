"""
front.py

Frontend en Streamlit para consultar la API de "StatisticsBusiness",
mostrar resultados en tabla y mapa, y estimar probabilidad de éxito.
Incluye logo y diseño más presentable.
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

API_BASE = "http://localhost/api/sqlite/negocio"  # ajusta si tu API está en otra ruta

# -----------------------------------------
# CARGAR LOGO (si existe)
# -----------------------------------------
def mostrar_logo(path: str = "logo.png", width: int = 220) -> None:
    try:
        logo = Image.open(path)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=width, use_container_width=False)
    except FileNotFoundError:
        # No mostrar error visible, solo omitir el logo si no está
        st.caption("")

mostrar_logo()

st.title("StatisticsBusiness — Buscador de Negocios por Ciudad")

st.markdown(
    "Consulta establecimientos por ciudad y colonia, visualiza su ubicación en el mapa "
    "y obtén una estimación básica de probabilidad de éxito."
)

st.divider()

# -----------------------------------------
# FUNCIÓN PARA CONSULTAR EL ENDPOINT
# -----------------------------------------
def consultar_api(ciudad_input: str,
                  nombre_input: Optional[str] = None,
                  asent_input: Optional[str] = None,
                  timeout: int = 10) -> Tuple[Dict, int]:
    """
    Consulta la API para obtener negocios filtrados por ciudad,
    nombre opcional y asentamiento opcional.
    Retorna (json_response, status_code).
    """
    url = f"{API_BASE}/buscar/{ciudad_input}"
    params = {}
    if nombre_input:
        params["nombre"] = nombre_input
    if asent_input:
        params["asent"] = asent_input

    try:
        response = requests.get(url, params=params, timeout=timeout)
        # Si la API devuelve JSON legítimo, devolvemos el json y el status
        return response.json(), response.status_code
    except requests.RequestException as exc:
        return {"error": str(exc)}, 500
    except ValueError:
        # Error al parsear JSON
        return {"error": "Respuesta de la API no es JSON válido."}, 500

# -----------------------------------------
# SIDEBAR — filtros rápidos
# -----------------------------------------
with st.sidebar:
    st.header("Filtros")
    ciudad = st.text_input("Ciudad (nombre de la hoja Excel):")
    nombre = st.text_input("Nombre del negocio (opcional):")
    asent = st.text_input("Asentamiento / Colonia (opcional):")
    buscar = st.button("Buscar")
    st.markdown("---")
    st.caption("Asegúrate de que el nombre de la hoja esté correctamente escrito.")

# Si el usuario no usa el sidebar (por compatibilidad), también dejamos inputs en la página
if not ciudad:
    # Mostrar inputs alternativos en la página principal (útil si alguien olvida el sidebar)
    st.info("Introduce la ciudad en la barra lateral para realizar la búsqueda.")

# -----------------------------------------
# RESULTADOS
# -----------------------------------------
if buscar:
    if not ciudad:
        st.error("Debes escribir una ciudad (nombre de la hoja).")
        st.stop()

    with st.spinner("Consultando API..."):
        data, status = consultar_api(ciudad, nombre, asent)

    if status != 200:
        # Mostrar mensaje amigable si la API devuelve error
        st.error(f"Error al consultar la API (status {status}): {data}")
        st.stop()

    # Intentamos convertir la respuesta en DataFrame
    try:
        df = pd.DataFrame(data)
    except Exception as exc:
        st.error(f"No se pudo convertir la respuesta en tabla: {exc}")
        st.stop()

    st.success(f"Resultados encontrados: {len(df)}")

    # Mostrar dos columnas: mapa y tabla/detalles
    col_map, col_tabla = st.columns([1.5, 1])

    # -------------------------
    # MOSTRAR EN MAPA
    # -------------------------
    with col_map:
        st.subheader("Mapa de resultados")
        if {"latitud", "longitud"}.issubset(df.columns):
            df_map = df.rename(columns={"latitud": "lat", "longitud": "lon"})
            # st.map espera columnas 'lat' y 'lon' como float
            try:
                df_map["lat"] = pd.to_numeric(df_map["lat"], errors="coerce")
                df_map["lon"] = pd.to_numeric(df_map["lon"], errors="coerce")
                df_map_clean = df_map.dropna(subset=["lat", "lon"])
                if df_map_clean.empty:
                    st.info("Los datos no contienen coordenadas válidas para mostrar en el mapa.")
                else:
                    st.map(df_map_clean[["lat", "lon"]], size = 3)
            except Exception as exc:
                st.error(f"No se pudo preparar el mapa: {exc}")
        else:
            st.info("Los resultados no incluyen columnas 'latitud' y 'longitud'.")

    # -----------------------------------------
    # TABLA Y ESTADÍSTICAS
    # -----------------------------------------
    with col_tabla:
        st.subheader("Tabla y estadísticas rápidas")
        st.dataframe(df, use_container_width=True)

        # Mostrar conteo por tipo o categoría si existe la columna
        if "giro" in df.columns:
            conteo = df["giro"].value_counts().rename_axis("giro").reset_index(name="count")
            st.markdown("**Negocios por giro**")
            st.table(conteo)

    st.divider()

    # -----------------------------------------
    # PORCENTAJE DE ÉXITO (por colonia/asentamiento)
    # -----------------------------------------
    st.subheader(f"Probabilidad de éxito en la colonia: {asent or '—'}")

    if asent:
        # normalizar a str y buscar coincidencias (case-insensitive)
        if "nomb_asent" not in df.columns:
            st.info("La tabla no contiene la columna 'nomb_asent' para calcular la probabilidad por colonia.")
        else:
            df_asent = df[df["nomb_asent"].astype(str).str.contains(asent, case=False, na=False)]

            if df_asent.empty:
                st.info(f"No se encontraron negocios en la colonia '{asent}'.")
            else:
                total_asent = len(df_asent)

                # Fórmula de probabilidad (la que ya tenías), con límites
                prob_exito = 100 - (total_asent / 6) * 80
                prob_exito = max(prob_exito, 5)
                prob_exito = min(prob_exito, 100)

                st.metric(
                    label="Probabilidad estimada de éxito",
                    value=f"{prob_exito:.2f} %",
                    delta=f"{total_asent} negocios en la colonia",
                )

                st.write(
                    f"La colonia **{asent}** tiene **{total_asent}** negocios. "
                    "A mayor concentración de establecimientos, la competencia aumenta "
                    "y la probabilidad estimada disminuye."
                )

                st.write("### 📄 Negocios encontrados en la colonia")
                st.dataframe(df_asent, use_container_width=True)
    else:
        st.info("Escribe un asentamiento para obtener la probabilidad estimada de éxito.")

    st.divider()
    st.caption("StatisticsBusiness • Visualización rápida para análisis local — no sustituye un estudio de mercado completo.")
