import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------- CARGAR DATOS ----------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("reporte_proyectos.csv")
    df['Fecha instalación'] = pd.to_datetime(df['Fecha instalación'], errors='coerce')
    df['Mes'] = df['Fecha instalación'].dt.month_name()

    df['Tipo Proyecto Nombre'] = df['Tipo de Proyecto'].map({
        1: 'Full EPC',
        2: 'Paneles BT',
        3: 'Polarizados',
        4: 'Baterías',
        5: 'Paneles MT'
    })

    df['Costo Base'] = df[['Costo de Material', 'Costo de Equipos', 'Mano de Obra']].sum(axis=1)
    cols_basicas = ['ID Proyecto', 'Nombre Cliente', 'Tipo de Proyecto', 'Tipo Proyecto Nombre',
                    'No. de Módulos', 'Potencia', 'Fecha instalación', 'Mes',
                    'Costo de Material', 'Costo de Equipos', 'Mano de Obra', 'Costo Base']
    extra = df.columns.difference(cols_basicas)
    df['Compras No Inventariables'] = df[extra].select_dtypes(include='number').sum(axis=1)
    df['Costo Total'] = df['Costo Base'] + df['Compras No Inventariables']
    df['Costo Total USD'] = df['Costo Total'] / 20.5
    df['Costo por Watt'] = np.where(df['Potencia'] > 0, df['Costo Total'] / df['Potencia'], np.nan)
    df['Costo por Panel'] = np.where(df['No. de Módulos'] > 0, df['Costo Total'] / df['No. de Módulos'], np.nan)
    df['Potencia por Panel'] = np.where(df['No. de Módulos'] > 0, df['Potencia'] / df['No. de Módulos'], np.nan)
    return df

df = cargar_datos()

# ---------- FILTROS ----------
st.sidebar.header("⚙️ Filtros")

moneda = st.sidebar.radio("Seleccionar Moneda:", ["Pesos", "Dólares"])
meses = st.sidebar.multiselect("📅 Selecciona los Meses:", options=df['Mes'].dropna().unique(), default=df['Mes'].dropna().unique())

# Validación: Cuadrilla
if "Tamaño total Cuadrilla(s)" in df.columns:
    cuadrilla_col = "Tamaño total Cuadrilla(s)"
else:
    cuadrilla_col = None
    st.sidebar.warning("⚠️ La columna 'Tamaño total Cuadrilla(s)' no existe en los datos.")

# Filtros adicionales
cuadrillas = st.sidebar.multiselect("👷 Selecciona las Cuadrillas:", options=df[cuadrilla_col].dropna().unique() if cuadrilla_col else [], default=df[cuadrilla_col].dropna().unique() if cuadrilla_col else [])
potencias = st.sidebar.multiselect("🔋 Potencia de Panel:", options=sorted(df['Potencia por Panel'].dropna().unique()), default=sorted(df['Potencia por Panel'].dropna().unique()))
tipos = st.sidebar.multiselect("🏗️ Tipo de Instalación:", options=df['Tipo Proyecto Nombre'].dropna().unique(), default=df['Tipo Proyecto Nombre'].dropna().unique())
clientes = st.sidebar.multiselect("🏢 Selecciona Cliente:", options=df['Nombre Cliente'].dropna().unique(), default=df['Nombre Cliente'].dropna().unique())

# ---------- APLICAR FILTROS ----------
df_filtros = df[
    (df['Mes'].isin(meses)) &
    (df['Tipo Proyecto Nombre'].isin(tipos)) &
    (df['Nombre Cliente'].isin(clientes))
]

if cuadrilla_col:
    df_filtros = df_filtros[df_filtros[cuadrilla_col].isin(cuadrillas)]

df_filtros = df_filtros[df_filtros['Potencia por Panel'].isin(potencias)]

# ---------- KPIs ----------
st.title("⚡ Dashboard de Instalaciones Residenciales - Ecoteko")
st.subheader("📊 Indicadores Clave")

col1, col2, col3 = st.columns(3)
col1.metric("📌 Total de Proyectos", len(df_filtros))
col2.metric("📈 Potencia Total Instalada", f"{df_filtros['Potencia'].sum():,.0f} W")

if moneda == "Pesos":
    col3.metric("💰 Costo Total", f"${df_filtros['Costo Total'].sum():,.0f}")
    costo_watt = df_filtros['Costo Total'].sum() / df_filtros['Potencia'].sum()
    costo_panel = df_filtros['Costo Total'].sum() / df_filtros['No. de Módulos'].sum()
else:
    col3.metric("💰 Costo Total (USD)", f"${df_filtros['Costo Total USD'].sum():,.0f}")
    costo_watt = df_filtros['Costo Total USD'].sum() / df_filtros['Potencia'].sum()
    costo_panel = df_filtros['Costo Total USD'].sum() / df_filtros['No. de Módulos'].sum()

col4, col5 = st.columns(2)
col4.metric("⚙️ Costo Promedio por Watt", f"${costo_watt:,.2f}")
col5.metric("🔩 Costo Promedio por Panel", f"${costo_panel:,.2f}")

# ---------- GRAFICAS ----------
st.subheader("📉 Costo por Watt por Proyecto")
fig = px.bar(df_filtros, x="Nombre Cliente", y="Costo por Watt", color="Tipo Proyecto Nombre",
             labels={"Costo por Watt": "Costo por Watt (MXN)"}, title="Costo por Watt por Proyecto")
st.plotly_chart(fig)

st.subheader("📊 Distribución del Costo por Watt por Tipo")
fig_box = px.box(df_filtros, x="Tipo Proyecto Nombre", y="Costo por Watt", points="all", title="Boxplot de Costo por Watt")
st.plotly_chart(fig_box)

st.subheader("🧾 Distribución de Costos")
costos = {
    "Material": df_filtros['Costo Material'].sum(),
    "Equipos": df_filtros['Costo Equipos'].sum(),
    "Mano de Obra": df_filtros['Costo Mano de Obra'].sum(),
    "Otros (No Inventariables)": df_filtros['Compras No Inventariables'].sum()
}
fig_pie = px.pie(names=costos.keys(), values=costos.values(), title="Distribución del Costo Total")
st.plotly_chart(fig_pie)

st.subheader("📊 Costo Total por Tipo de Instalación")
df_grouped = df_filtros.groupby("Tipo Proyecto Nombre")[["Costo Material", "Costo Equipos", "Costo Mano de Obra", "Compras No Inventariables"]].sum().reset_index()
df_grouped_melt = df_grouped.melt(id_vars="Tipo Proyecto Nombre", var_name="Categoría", value_name="Costo")
fig_stack = px.bar(df_grouped_melt, x="Tipo Proyecto Nombre", y="Costo", color="Categoría", title="Costos por Tipo de Proyecto (Apilado)")
st.plotly_chart(fig_stack)

st.subheader("📐 Costo de Estructura por Panel")
df_filtros["Costo por Panel Individual"] = df_filtros["Costo Base"] / df_filtros["No. de Módulos"]
fig_panel = px.scatter(df_filtros, x="Nombre Cliente", y="Costo por Panel Individual", color="Tipo Proyecto Nombre",
                       title="Costo por Panel Base (Material + Mano de Obra + Equipos)")
st.plotly_chart(fig_panel)
