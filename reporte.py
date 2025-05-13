import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")

TIPO_CAMBIO = 20.5

# --- Funciones para cargar datos ---

@st.cache_data
def load_data_bt():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25BT.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.rename(columns={"Tipo de instalaciÃ³n": "Tipo de instalacion"}, inplace=True)
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df["Mes"] = df["Mes"].astype(str).str.strip().str.capitalize()
    df = df[df["Mes"].notna() & (df["Mes"] != "nan")]
    if "Cuadrilla" in df.columns:
        df["Cuadrilla"] = df["Cuadrilla"].fillna("Sin asignar").astype(str).str.strip()
    else:
        df["Cuadrilla"] = "Sin asignar"
    for col in ["Costo de equipos", "Costo estructura", "Costo mano de obra"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    return df

@st.cache_data
def load_data_mt():
    url2 = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25MT.csv"
    df = pd.read_csv(url2, encoding="latin1")
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df.rename(columns={"Tipo de instalaciÃ³n": "Tipo de instalacion"}, inplace=True)
    df = df[df["Mes"].notna()]
    for col in df.columns:
        if "Costo" in col or col in ["Electrico", "Logística", "Miscelaneos", "Trámites", "Verificacion", "Herramienta", "Otros", "Capacitores"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Cuadrilla"] = df["Cuadrilla"].fillna("Sin asignar")
    return df


# --- Interfaz de usuario ---
st.sidebar.markdown("## 🧭 Seleccionar tipo de proyecto")
tipo_proyecto = st.sidebar.radio("Tipo de Proyecto:", ["BT", "MT"])

if tipo_proyecto == "BT":
    df = load_data_bt()
    factor = 1 if st.sidebar.radio("💱 Moneda:", ["Pesos", "Dólares"]) == "Pesos" else 1 / TIPO_CAMBIO
else:
    df = load_data_mt()
    aplicar_iva = st.sidebar.checkbox("💸 Aplicar IVA (excepto mano de obra)", value=True)
    IVA = 1.16 if aplicar_iva else 1.0
    factor = 1  # MT ya está sin IVA, trabajamos en pesos

# --- Filtros comunes ---
meses = sorted(df["Mes"].dropna().unique())
cuadrillas = sorted(df["Cuadrilla"].dropna().unique())
proyectos = sorted(df["Nombre del proyecto"].dropna().unique())

meses_sel = st.sidebar.multiselect("📅 Meses:", ["Todos"] + meses, default=["Todos"])
cuadrillas_sel = st.sidebar.multiselect("👷 Cuadrillas:", ["Todas"] + cuadrillas, default=["Todas"])
clientes_sel = st.sidebar.multiselect("🏢 Cliente:", ["Todos"] + proyectos, default=["Todos"])

df_filtrado = df.copy()
if "Todos" not in meses_sel:
    df_filtrado = df_filtrado[df_filtrado["Mes"].isin(meses_sel)]
if "Todas" not in cuadrillas_sel:
    df_filtrado = df_filtrado[df_filtrado["Cuadrilla"].isin(cuadrillas_sel)]
if "Todos" not in clientes_sel:
    df_filtrado = df_filtrado[df_filtrado["Nombre del proyecto"].isin(clientes_sel)]

# --- Cálculos para métricas ---
if tipo_proyecto == "MT":
    total_costo = (
        df_filtrado["Costo de equipos"] * IVA +
        df_filtrado["Costo estructura"] * IVA +
        df_filtrado["Electrico"] * IVA +
        df_filtrado["Logística"] * IVA +
        df_filtrado["Miscelaneos"] * IVA +
        df_filtrado["Trámites"] * IVA +
        df_filtrado["Verificacion"] * IVA +
        df_filtrado["Herramienta"] * IVA +
        df_filtrado["Otros"] * IVA +
        df_filtrado["Capacitores"] * IVA +
        df_filtrado["Costo mano de obra"]  # sin IVA
    ).sum()
else:
    total_costo = df_filtrado["Costo total"].sum() * factor

proyectos = df_filtrado["Nombre del proyecto"].nunique()
potencia_total = df_filtrado["Potencia del sistema"].sum()
paneles_total = df_filtrado["No. de Paneles"].sum()
cpw_prom = df_filtrado["COSTO POR WATT"].mean() * factor if "COSTO POR WATT" in df_filtrado.columns else 0
cpp_prom = df_filtrado["Costo total de estructura por panel"].mean() * factor if "Costo total de estructura por panel" in df_filtrado.columns else 0

# --- Mostrar métricas ---
col1, col2, col3 = st.columns(3)
col1.metric("📌 Proyectos", proyectos)
col2.metric("💰 Costo Total", f"${total_costo:,.0f}")
col3.metric("⚡ Potencia Total", f"{potencia_total:,.0f} W")

col4, col5, col6 = st.columns(3)
col4.metric("⚙️ Costo Prom. por Watt", f"${cpw_prom:,.2f}")
col5.metric("🔩 Paneles", int(paneles_total))
col6.metric("🏗️ Costo Prom. por Panel", f"${cpp_prom:,.2f}")

# --- Visualizaciones básicas ---
if tipo_proyecto == "MT":
    columnas_costos = ["Costo de equipos", "Costo estructura", "Electrico", "Logística", "Miscelaneos", 
                       "Trámites", "Verificacion", "Herramienta", "Otros", "Capacitores", "Costo mano de obra"]
    cost_data = pd.DataFrame({
        "Categoría": columnas_costos,
        "Monto": [(df_filtrado[c] * (1.0 if c == "Costo mano de obra" else IVA)).sum() for c in columnas_costos]
    })
else:
    cost_data = pd.DataFrame({
        "Categoría": ["Equipos", "Estructura", "Mano de Obra"],
        "Monto": [
            df_filtrado["Costo de equipos"].sum() * factor,
            df_filtrado["Costo estructura"].sum() * factor,
            df_filtrado["Costo mano de obra"].sum() * factor
        ]
    })

fig1 = px.pie(cost_data, names="Categoría", values="Monto", title="Distribución de Costos")
st.plotly_chart(fig1)
