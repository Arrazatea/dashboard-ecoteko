
import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")

TIPO_CAMBIO = 20.5

# Estilos
st.markdown("""
<style>
    body, .main { background-color: #101820 !important; color: #F2AA4C !important; }
    .css-1d391kg, .stSidebar { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, h5, h6 { color: #F2AA4C !important; font-weight: bold; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .logo-container img { background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="logo-container"><img src="https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/LOGO.png" width="400"></div>', unsafe_allow_html=True)
st.markdown("# ⚡ Dashboard de Instalaciones Residenciales - Ecoteko")

# Selector de proyecto
tipo_proyecto = st.sidebar.radio("🔘 Selecciona el tipo de proyecto:", ["BT", "MT"])

# -------------------
# FUNCIONES
# -------------------
@st.cache_data
def load_data_bt():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.rename(columns={"Tipo de instalaciÃ³n": "Tipo de instalacion"}, inplace=True)
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df["Mes"] = df["Mes"].astype(str).str.strip().str.capitalize()
    df = df[df["Mes"].notna() & (df["Mes"] != "nan")]
    df["Cuadrilla"] = df.get("Cuadrilla", "Sin asignar").fillna("Sin asignar")
    for col in ["Costo de equipos", "Costo estructura", "Costo mano de obra"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    return df

@st.cache_data
def load_data_mt():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25MT.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.columns = df.columns.str.strip()
    df.columns = [unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode('utf-8') for c in df.columns]
    df = df[df["Mes"].notna()]
    for col in df.columns:
        if "Costo" in col or col in ["Electrico", "Logistica", "Miscelaneos", "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Cuadrilla"] = df.get("Cuadrilla", "Sin asignar").fillna("Sin asignar")
    return df

# -------------------
# DATOS Y FILTROS
# -------------------
df = load_data_bt() if tipo_proyecto == "BT" else load_data_mt()

moneda = st.sidebar.radio("💱 Moneda:", ["Pesos", "Dólares"])
factor = 1 if moneda == "Pesos" else 1 / TIPO_CAMBIO
IVA = 1.16 if tipo_proyecto == "MT" and st.sidebar.checkbox("💸 Aplicar IVA (excepto mano de obra)", True) else 1.0

# Filtros
meses = ["Todos"] + sorted(df["Mes"].dropna().unique())
cuadrillas = ["Todas"] + sorted(df["Cuadrilla"].dropna().unique())
potencias = ["Todas"] + sorted(df["Potencia de paneles"].dropna().unique())
clientes = ["Todos"] + sorted(df["Nombre del proyecto"].dropna().unique())
instalaciones = ["Todas"] + sorted(df.get("Tipo de instalacion", pd.Series()).dropna().unique())

meses_sel = st.sidebar.multiselect("📅 Meses:", meses, default=["Todos"])
cuadrillas_sel = st.sidebar.multiselect("👷 Cuadrillas:", cuadrillas, default=["Todas"])
potencias_sel = st.sidebar.multiselect("🔋 Potencia:", potencias, default=["Todas"])
clientes_sel = st.sidebar.multiselect("🏢 Cliente:", clientes, default=["Todos"])
instalaciones_sel = st.sidebar.multiselect("🏗️ Tipo de Instalación:", instalaciones, default=["Todas"])

df_filtrado = df.copy()
if "Todos" not in meses_sel:
    df_filtrado = df_filtrado[df_filtrado["Mes"].isin(meses_sel)]
if "Todas" not in cuadrillas_sel:
    df_filtrado = df_filtrado[df_filtrado["Cuadrilla"].isin(cuadrillas_sel)]
if "Todas" not in potencias_sel:
    df_filtrado = df_filtrado[df_filtrado["Potencia de paneles"].isin(potencias_sel)]
if "Todos" not in clientes_sel:
    df_filtrado = df_filtrado[df_filtrado["Nombre del proyecto"].isin(clientes_sel)]
if "Todas" not in instalaciones_sel and "Tipo de instalacion" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Tipo de instalacion"].isin(instalaciones_sel)]

# -------------------
# MÉTRICAS Y GRÁFICAS
# -------------------
if tipo_proyecto == "MT":
    rubros = ["Costo de equipos", "Costo estructura", "Electrico", "Logistica", "Miscelaneos",
              "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]
    total_costo = sum((df_filtrado[r] * IVA).sum() for r in rubros if r in df_filtrado.columns)
    total_costo += df_filtrado.get("Costo mano de obra", pd.Series(0)).sum()
else:
    total_costo = df_filtrado.get("Costo total", pd.Series(0)).sum()
total_costo *= factor

col1, col2, col3 = st.columns(3)
col1.metric("📌 Proyectos", df_filtrado["Nombre del proyecto"].nunique())
col2.metric(f"💰 Costo Total ({moneda})", f"${total_costo:,.0f}")
col3.metric("⚡ Potencia Total", f"{df_filtrado.get('Potencia del sistema', pd.Series(0)).sum():,.0f} W")

col4, col5, col6 = st.columns(3)
col4.metric("⚙️ Costo Prom. por Watt", f"${df_filtrado.get('COSTO POR WATT', pd.Series()).mean() * factor:,.2f}")
col5.metric("🔩 Paneles", int(df_filtrado.get('No. de Paneles', pd.Series(0)).sum()))
col6.metric("🏗️ Costo Prom. por Panel", f"${df_filtrado.get('Costo total de estructura por panel', pd.Series()).mean() * factor:,.2f}")

# Distribución de costos
if tipo_proyecto == "MT":
    rubros_mt = rubros + ["Costo mano de obra"]
    cost_data = pd.DataFrame({
        "Categoría": [r for r in rubros_mt if r in df_filtrado.columns],
        "Monto": [(df_filtrado[r] * (1 if r == "Costo mano de obra" else IVA)).sum() * factor for r in rubros_mt if r in df_filtrado.columns]
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

st.subheader("💰 Distribución de Costos")
st.plotly_chart(px.pie(cost_data, names="Categoría", values="Monto"))

# Gráfica por proyecto
if "Costo total de estructura por panel" in df_filtrado.columns:
    st.subheader("🏗️ Costo de Estructura por Panel por Proyecto")
    fig2 = px.bar(df_filtrado, x="Nombre del proyecto",
                  y=df_filtrado["Costo total de estructura por panel"] * factor,
                  color="Tipo de instalacion" if "Tipo de instalacion" in df_filtrado.columns else None)
    st.plotly_chart(fig2)

# Boxplot por tipo de instalación
if "COSTO POR WATT" in df_filtrado.columns and "Tipo de instalacion" in df_filtrado.columns:
    fig3 = px.box(df_filtrado, x="Tipo de instalacion",
                  y=df_filtrado["COSTO POR WATT"] * factor,
                  color="Tipo de instalacion")
    st.subheader("📦 Costo por Watt por Tipo de Instalación")
    st.plotly_chart(fig3)

# Promedio por cuadrilla
if all(col in df_filtrado.columns for col in ["Cuadrilla", "Costo total", "No. de Paneles"]):
    df_temp = df_filtrado[df_filtrado["No. de Paneles"] > 0].copy()
    df_temp["Costo total por panel"] = df_temp["Costo total"] / df_temp["No. de Paneles"]
    df_cuad = df_temp.groupby("Cuadrilla")["Costo total por panel"].mean().reset_index()
    df_cuad["Promedio"] = df_cuad["Costo total por panel"] * factor
    st.subheader("👷 Promedio de Costo Total por Panel por Cuadrilla")
    st.plotly_chart(px.bar(df_cuad, x="Cuadrilla", y="Promedio", title="Promedio por Cuadrilla"))
