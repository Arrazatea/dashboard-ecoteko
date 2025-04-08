import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")

# --- Cargar datos desde GitHub
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/reporte_proyectos.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    df['Fecha instalación'] = pd.to_datetime(df['Fecha instalación'], errors='coerce')
    df['Mes'] = df['Fecha instalación'].dt.month_name()

    # Traducir tipo de proyecto
    tipo_dict = {
        1: 'Full EPC',
        2: 'Paneles BT',
        3: 'Polarizados',
        4: 'Baterías',
        5: 'Paneles MT'
    }
    df['Tipo Proyecto Nombre'] = df['Tipo de Proyecto'].map(tipo_dict)

    # Costos base
    df['Costo Base'] = df[['Costo de Material', 'Costo de Equipos', 'Mano de Obra']].sum(axis=1)

    # Otros costos no inventariables
    columnas_extra = df.columns.difference([
        'ID Proyecto', 'Nombre Cliente', 'Tipo de Proyecto', 'Tipo Proyecto Nombre',
        'No. de Módulos', 'Potencia', 'Fecha instalación', 'Mes',
        'Costo de Material', 'Costo de Equipos', 'Mano de Obra', 'Costo Base'
    ])
    df['Compras No Inventariables'] = df[columnas_extra].select_dtypes(include='number').sum(axis=1)

    # Totales
    df['Costo Total'] = df['Costo Base'] + df['Compras No Inventariables']
    df['Costo Total USD'] = df['Costo Total'] / 20.5
    df['Costo por Watt'] = np.where(df['Potencia'] > 0, df['Costo Total'] / df['Potencia'], np.nan)
    df['Costo por Panel'] = np.where(df['No. de Módulos'] > 0, df['Costo Total'] / df['No. de Módulos'], np.nan)
    df['Potencia por Panel'] = np.where(df['No. de Módulos'] > 0, df['Potencia'] / df['No. de Módulos'], np.nan)

    return df

df = load_data()

# --- Estilos CSS + Logo
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

# --- Filtros
st.sidebar.title("⚙️ Filtros")

TIPO_CAMBIO = 20.5
moneda = st.sidebar.radio("💱 Seleccionar Moneda:", ["Pesos", "Dólares"])
meses = st.sidebar.multiselect("📅 Selecciona los Meses:", ["Todos"] + list(df["Mes"].dropna().unique()), default=["Todos"])

cuadrilla_col = [c for c in df.columns if "Cuadrilla" in c]
cuadrilla_col = cuadrilla_col[0] if cuadrilla_col else None
cuadrillas = st.sidebar.multiselect("👷 Selecciona las Cuadrillas:", ["Todas"] + list(df[cuadrilla_col].dropna().unique()) if cuadrilla_col else ["Todas"], default=["Todas"])

potencias = st.sidebar.multiselect("🔋 Potencia de Panel:", ["Todas"] + sorted(df['Potencia por Panel'].dropna().unique()), default=["Todas"])
tipos = st.sidebar.multiselect("🏗️ Tipo de Instalación:", ["Todas"] + list(df["Tipo Proyecto Nombre"].dropna().unique()), default=["Todas"])
clientes = st.sidebar.multiselect("🏢 Selecciona Cliente:", ["Todos"] + list(df["Nombre Cliente"].dropna().unique()), default=["Todos"])

# --- Aplicar filtros
df_filtered = df.copy()

if "Todos" not in meses:
    df_filtered = df_filtered[df_filtered["Mes"].isin(meses)]
if "Todas" not in cuadrillas and cuadrilla_col:
    df_filtered = df_filtered[df_filtered[cuadrilla_col].isin(cuadrillas)]
if "Todas" not in potencias:
    df_filtered = df_filtered[df_filtered["Potencia por Panel"].isin(potencias)]
if "Todas" not in tipos:
    df_filtered = df_filtered[df_filtered["Tipo Proyecto Nombre"].isin(tipos)]
if "Todos" not in clientes:
    df_filtered = df_filtered[df_filtered["Nombre Cliente"].isin(clientes)]

# --- KPIs
st.markdown("## 📊 Indicadores Clave")
factor_cambio = 1 if moneda == "Pesos" else 1 / TIPO_CAMBIO

col1, col2, col3 = st.columns(3)
col1.metric("📌 Total de Proyectos", df_filtered["Nombre Cliente"].nunique())
col2.metric(f"💰 Costo Total ({moneda})", f"${(df_filtered['Costo Total'].sum() * factor_cambio):,.0f}")
col3.metric("⚡ Potencia Total Instalada", f"{df_filtered['Potencia'].sum():,.0f} W")

col4, col5, col6 = st.columns(3)
col4.metric(f"⚙️ Costo Prom. por Watt ({moneda})", f"${(df_filtered['Costo por Watt'].mean() * factor_cambio):,.2f}")
col5.metric("🔩 Número de Paneles", int(df_filtered['No. de Módulos'].sum()))
col6.metric(f"🏗️ Costo Prom. por Panel ({moneda})", f"${(df_filtered['Costo por Panel'].mean() * factor_cambio):,.2f}")

# --- Gráficos
st.subheader(f"📈 Costo por Watt por Proyecto")
fig1 = px.bar(df_filtered, x="Nombre Cliente", y=df_filtered["Costo por Watt"] * factor_cambio, color="Tipo Proyecto Nombre", title=f"Costo por Watt ({moneda})")
st.plotly_chart(fig1)

st.subheader(f"📊 Variabilidad del Costo por Watt")
fig2 = px.box(df_filtered, x="Tipo Proyecto Nombre", y=df_filtered["Costo por Watt"] * factor_cambio, color="Tipo Proyecto Nombre", title=f"Distribución por Tipo de Instalación ({moneda})")
st.plotly_chart(fig2)

st.subheader(f"📊 Distribución de Costos")
costos = {
    "Material": df_filtered['Costo de Material'].sum() * factor_cambio,
    "Equipos": df_filtered['Costo de Equipos'].sum() * factor_cambio,
    "Mano de Obra": df_filtered['Mano de Obra'].sum() * factor_cambio,
    "Otros": df_filtered['Compras No Inventariables'].sum() * factor_cambio
}
fig3 = px.pie(names=costos.keys(), values=costos.values(), title=f"Distribución de Costos en {moneda}")
st.plotly_chart(fig3)

st.subheader(f"🏗️ Costos por Tipo de Instalación")
grouped = df_filtered.groupby("Tipo Proyecto Nombre")[["Costo de Material", "Costo de Equipos", "Mano de Obra", "Compras No Inventariables"]].sum().reset_index()
melted = grouped.melt(id_vars="Tipo Proyecto Nombre", var_name="Categoría", value_name="Monto")
melted["Monto"] *= factor_cambio
fig4 = px.bar(melted, x="Tipo Proyecto Nombre", y="Monto", color="Categoría", title=f"Costos Totales por Tipo ({moneda})")
st.plotly_chart(fig4)

st.subheader(f"📐 Costo de Estructura por Panel")
df_filtered["Costo por Panel Base"] = df_filtered["Costo Base"] / df_filtered["No. de Módulos"]
fig5 = px.bar(df_filtered, x="Nombre Cliente", y=df_filtered["Costo por Panel Base"] * factor_cambio, color="Tipo Proyecto Nombre", title=f"Costo Base por Panel ({moneda})")
st.plotly_chart(fig5)
