import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuración de página ---
st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")
TIPO_CAMBIO = 20.5

# --- Estilo visual y logo ---
st.markdown("""
<style>
    body, .main { background-color: #101820 !important; color: #F2AA4C !important; }
    .css-1d391kg, .stSidebar { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, h5, h6 { color: #F2AA4C !important; font-weight: bold; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .logo-container img { background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

logo_url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/LOGO.png"
st.markdown(f'<div class="logo-container"><img src="{logo_url}" width="400"></div>', unsafe_allow_html=True)
st.markdown("# ⚡ Dashboard de Instalaciones Residenciales - Ecoteko")

# --- Funciones de carga de datos ---
@st.cache_data
def load_data_bt():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25BT.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.rename(columns={"Tipo de instalaciÃ³n": "Tipo de instalacion"}, inplace=True)
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df["Mes"] = df["Mes"].astype(str).str.strip().str.capitalize()
    df = df[df["Mes"].notna() & (df["Mes"] != "nan")]
    df["Cuadrilla"] = df.get("Cuadrilla", "Sin asignar").fillna("Sin asignar").astype(str).str.strip()
    for col in ["Costo de equipos", "Costo estructura", "Costo mano de obra"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    return df

@st.cache_data
def load_data_mt():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25MT.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df.rename(columns={"Tipo de instalacion": "Tipo de instalacion"}, inplace=True)
    df = df[df["Mes"].notna()]
    for col in df.columns:
        if "Costo" in col or col in ["Electrico", "Logistica", "Miscelaneos", "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Cuadrilla"] = df.get("Cuadrilla", "Sin asignar").fillna("Sin asignar")
    return df

# --- Selector BT/MT ---
st.sidebar.markdown("## 🧭 Tipo de Proyecto")
tipo_proyecto = st.sidebar.radio("Selecciona:", ["BT", "MT"])

if tipo_proyecto == "BT":
    df = load_data_bt()
    factor = 1 if st.sidebar.radio("💱 Moneda:", ["Pesos", "Dólares"]) == "Pesos" else 1 / TIPO_CAMBIO
else:
    df = load_data_mt()
    aplicar_iva = st.sidebar.checkbox("💸 Aplicar IVA (excepto mano de obra)", value=True)
    IVA = 1.16 if aplicar_iva else 1.0
    factor = 1

# --- Filtros comunes ---
meses_sel = st.sidebar.multiselect("📅 Meses:", ["Todos"] + sorted(df["Mes"].dropna().unique()), default=["Todos"])
cuadrillas_sel = st.sidebar.multiselect("👷 Cuadrillas:", ["Todas"] + sorted(df["Cuadrilla"].dropna().unique()), default=["Todas"])
potencias_sel = st.sidebar.multiselect("🔋 Potencia:", ["Todas"] + sorted(df["Potencia de paneles"].dropna().unique()), default=["Todas"])
clientes_sel = st.sidebar.multiselect("🏢 Cliente:", ["Todos"] + sorted(df["Nombre del proyecto"].dropna().unique()), default=["Todos"])

if "Tipo de instalacion" in df.columns:
    instalaciones = sorted(df["Tipo de instalacion"].dropna().unique())
    instalaciones_sel = st.sidebar.multiselect("🏗️ Tipo de Instalación:", ["Todas"] + instalaciones, default=["Todas"])
else:
    instalaciones_sel = ["Todas"]

df_filtrado = df.copy()
if "Todos" not in meses_sel:
    df_filtrado = df_filtrado[df_filtrado["Mes"].isin(meses_sel)]
if "Todas" not in cuadrillas_sel:
    df_filtrado = df_filtrado[df_filtrado["Cuadrilla"].isin(cuadrillas_sel)]
if "Todas" not in potencias_sel:
    df_filtrado = df_filtrado[df_filtrado["Potencia de paneles"].isin(potencias_sel)]
if "Todas" not in instalaciones_sel and "Tipo de instalacion" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Tipo de instalacion"].isin(instalaciones_sel)]
if "Todos" not in clientes_sel:
    df_filtrado = df_filtrado[df_filtrado["Nombre del proyecto"].isin(clientes_sel)]

# --- Cálculo de métricas ---
if tipo_proyecto == "MT":
    rubros = ["Costo de equipos", "Costo estructura", "Electrico", "Logistica", "Miscelaneos",
              "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]
    rubros_existentes = [r for r in rubros if r in df_filtrado.columns]
    total_costo = sum((df_filtrado[r] * IVA).sum() for r in rubros_existentes)
    if "Costo mano de obra" in df_filtrado.columns:
        total_costo += df_filtrado["Costo mano de obra"].sum()
else:
    total_costo = df_filtrado["Costo total"].sum() * factor

col1, col2, col3 = st.columns(3)
col1.metric("📌 Proyectos", df_filtrado["Nombre del proyecto"].nunique())
col2.metric("💰 Costo Total", f"${total_costo:,.0f}")
col3.metric("⚡ Potencia Total", f"{df_filtrado['Potencia del sistema'].sum():,.0f} W")

col4, col5, col6 = st.columns(3)
col4.metric("⚙️ Costo Prom. por Watt", f"${df_filtrado['COSTO POR WATT'].mean() * factor:,.2f}")
col5.metric("🔩 Paneles", int(df_filtrado["No. de Paneles"].sum()))
col6.metric("🏗️ Costo Prom. por Panel", f"${df_filtrado['Costo total de estructura por panel'].mean() * factor:,.2f}")

# --- Gráficas ---
if tipo_proyecto == "MT":
    rubros_mt = rubros_existentes + ["Costo mano de obra"]
    cost_data = pd.DataFrame({
        "Categoría": rubros_mt,
        "Monto": [(df_filtrado[col] * (1 if col == "Costo mano de obra" else IVA)).sum() for col in rubros_mt if col in df_filtrado.columns]
    })
else:
    cost_data = pd.DataFrame({
        "Categoría": ["Equipos", "Estructura", "Mano de Obra"],
        "Monto": [
            df_filtrado.get("Costo de equipos", pd.Series(0)).sum() * factor,
            df_filtrado.get("Costo estructura", pd.Series(0)).sum() * factor,
            df_filtrado.get("Costo mano de obra", pd.Series(0)).sum() * factor
        ]
    })

fig1 = px.pie(cost_data, names="Categoría", values="Monto", title="Distribución de Costos")
st.subheader("💰 Distribución de Costos")
st.plotly_chart(fig1)

if "Costo total de estructura por panel" in df_filtrado.columns:
    fig2 = px.bar(df_filtrado, x="Nombre del proyecto", y=df_filtrado["Costo total de estructura por panel"] * factor,
                  color="Tipo de instalacion", title="Costo de Estructura por Panel")
    st.subheader("🏗️ Costo de Estructura por Panel")
    st.plotly_chart(fig2)

if "COSTO POR WATT" in df_filtrado.columns:
    fig3 = px.box(df_filtrado, x="Tipo de instalacion", y=df_filtrado["COSTO POR WATT"] * factor,
                  color="Tipo de instalacion", title="Variabilidad del Costo por Watt")
    st.subheader("📦 Costo por Watt por Tipo de Instalación")
    st.plotly_chart(fig3)
