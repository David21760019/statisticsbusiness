"""
Script para extraer datos de todas las hojas de un archivo Excel
y guardarlos estructurados dentro de una base SQLite.

Requisitos:
    pip install pandas openpyxl
"""

import pandas as pd
import sqlite3

# ============================
# CONFIGURACIÓN
# ============================
EXCEL_FILE = "datos.xlsx"
SQLITE_DB = "negocios.db"
TABLE_NAME = "negocios"

# Columnas objetivo para estandarizar
COLUMNS_BASE = ["ciudad", "nom_estab", "latitud", "longitud", "nomb_asent"]


def excel_to_sqlite():
    """Lee todas las hojas del Excel y las guarda en SQLite."""

    # Leer TODAS las hojas del Excel
    print("🔍 Leyendo todas las hojas...")
    hojas = pd.read_excel(EXCEL_FILE, sheet_name=None)

    registros = []

    # Recorrer cada hoja (ciudad)
    for ciudad, df in hojas.items():
        print(f"📄 Procesando hoja: {ciudad}")

        # Normalizar columnas
        df.columns = df.columns.str.strip()

        columnas_encontradas = [
            c for c in ["nom_estab", "latitud", "longitud", "nomb_asent"]
            if c in df.columns
        ]

        if not columnas_encontradas:
            print(f"⚠ La hoja '{ciudad}' no tiene columnas requeridas, se omite.")
            continue

        # Crear un DataFrame estándar
        df_temp = df[columnas_encontradas].copy()
        df_temp["ciudad"] = ciudad  # agregar columna ciudad

        registros.append(df_temp)

    # Si no hay datos, terminar
    if not registros:
        print("❌ No se encontraron datos válidos en ninguna hoja.")
        return

    # Unir todo en un solo DataFrame
    df_final = pd.concat(registros, ignore_index=True)

    # Ordenar las columnas
    df_final = df_final.reindex(columns=COLUMNS_BASE)

    print(f"📦 Total de registros listos para exportar: {len(df_final)}")

    # ============================
    # EXPORTAR A SQLITE
    # ============================
    conn = sqlite3.connect(SQLITE_DB)
    df_final.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()

    print("✅ Exportación completada con éxito.")
    print(f"📁 Base creada: {SQLITE_DB}")
    print(f"🗂 Tabla: {TABLE_NAME}")


if __name__ == "__main__":
    excel_to_sqlite()
