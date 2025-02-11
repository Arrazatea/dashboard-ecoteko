import streamlit as st
import pandas as pd
import plotly.express as px

# 📂 Cargar el archivo CSV desde GitHub
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/ResumenEnero25.csv"
    return pd.read_csv(url)

df = load_data()

# 🛠 Limpiar nombres de columnas
df.columns = df.columns.str.strip()

# 💱 **Tipo de Cambio**
TIPO_CAMBIO = 20.5

# 🎨 **Configuración del Dashboard**
st.title("📊 Dashboard de Instalaciones Fotovoltaicas - Ecoteko")

# 📌 **Sidebar con Filtros**
st.sidebar.title("⚙️ Filtros")

# 💰 **Filtro para moneda**
moneda = st.sidebar.radio("💱 Seleccionar Moneda:", ["Pesos", "Dólares"])

# 📅 **Filtro de Mes (Múltiples Opciones)**
meses_seleccionados = st.sidebar.multiselect("📅 Selecciona los Meses:", ["Todos"] + list(df["Mes"].unique()), default=["Todos"])

# 👷‍♂️ **Filtro de Cuadrilla (Múltiples Opciones)**
cuadrillas_seleccionadas = st.sidebar.multiselect("👷‍♂️ Selecciona las Cuadrillas:", ["Todas"] + list(df["Cuadrilla"].unique()), default=["Todas"])

# 🔋 **Filtro de Potencia de Panel**
potencias_seleccionadas = st.sidebar.multiselect("🔋 Potencia de Panel:", ["Todas"] + list(df["Potencia de paneles"].unique()), default=["Todas"])

# 🏗️ **Filtro de Tipo de Instalación**
instalaciones_seleccionadas = st.sidebar.multiselect("🏗️ Tipo de Instalación:", ["Todas"] + list(df["Tipo de instalación"].unique()), default=["Todas"])

# 🏢 **Filtro de Cliente (Nombre del Proyecto)**
clientes_seleccionados = st.sidebar.multiselect("🏢 Selecciona Cliente:", ["Todos"] + list(df["Nombre del proyecto"].unique()), default=["Todos"])

# 🔍 **Aplicar filtros**
df_filtered = df.copy()

if "Todos" not in meses_seleccionados:
    df_filtered = df_filtered[df_filtered["Mes"].isin(meses_seleccionados)]
if "Todas" not in cuadrillas_seleccionadas:
    df_filtered = df_filtered[df_filtered["Cuadrilla"].isin(cuadrillas_seleccionadas)]
if "Todas" not in potencias_seleccionadas:
    df_filtered = df_filtered[df_filtered["Potencia de paneles"].isin(potencias_seleccionadas)]
if "Todas" not in instalaciones_seleccionadas:
    df_filtered = df_filtered[df_filtered["Tipo de instalación"].isin(instalaciones_seleccionadas)]
if "Todos" not in clientes_seleccionados:
    df_filtered = df_filtered[df_filtered["Nombre del proyecto"].isin(clientes_seleccionados)]

# 📌 **KPIs Principales (Aplicando Filtros y Moneda)**
st.markdown("## 📊 Indicadores Clave")

factor_cambio = 1 if moneda == "Pesos" else 1 / TIPO_CAMBIO

col1, col2, col3 = st.columns(3)

with col1:
    total_proyectos = df_filtered["Nombre del proyecto"].nunique()
    st.metric(label="📌 Total de Proyectos", value=total_proyectos)

with col2:
    costo_total = df_filtered["Costo total"].sum() * factor_cambio
    st.metric(label=f"💰 Costo Total ({moneda})", value=f"${costo_total:,.0f}")

with col3:
    potencia_total = df_filtered["Potencia de paneles"].sum()
    st.metric(label="⚡ Potencia Total Instalada", value=f"{potencia_total} kW")

col4, col5 = st.columns(2)

with col4:
    costo_promedio_panel = df_filtered["Costo total de estructura por panel"].mean() * factor_cambio
    st.metric(label=f"📉 Costo Promedio por Panel ({moneda})", value=f"${costo_promedio_panel:,.2f}")

with col5:
    costo_promedio_watt = df_filtered["COSTO POR WATT"].mean() * factor_cambio
    st.metric(label=f"⚡ Costo Promedio por Watt ({moneda})", value=f"${costo_promedio_watt:,.2f}")

# 📊 **Gráfico 1: Distribución de Costos**
cost_distribution = pd.DataFrame({
    "Categoría": ["Equipos", "Estructura", "Mano de Obra"],
    "Monto": [
        df_filtered["Costo de equipos"].sum() * factor_cambio,
        df_filtered["Costo estructura"].sum() * factor_cambio,
        df_filtered["Costo mano de obra"].sum() * factor_cambio
    ]
})

fig1 = px.pie(
    cost_distribution, 
    names="Categoría", 
    values="Monto", 
    title=f"Distribución de Costos en {moneda}",
    color_discrete_sequence=["#4682B4", "#FF9999", "#66B3FF"],
    hover_data={"Monto": ":,.2f"}  # 🔹 Mostrar monto en tooltip
)
fig1.update_traces(textinfo="percent+label", hovertemplate="Categoría=%{label}<br>Monto=%{value:,.2f}")

# 📊 **Gráfico 2: Costo total de estructura por panel**
fig2 = px.bar(
    df_filtered, 
    x="Nombre del proyecto", 
    y=df_filtered["Costo total de estructura por panel"] * factor_cambio, 
    color="Tipo de instalación", 
    title=f"Costo de Estructura por Panel en {moneda}"
)
fig2.update_xaxes(tickangle=-45)

# 📊 **Gráfico 3: Boxplot del Costo por Watt con Línea de Media por Tipo de Instalación**
fig3 = px.box(
    df_filtered, 
    y=df_filtered["COSTO POR WATT"] * factor_cambio, 
    x="Tipo de instalación", 
    color="Tipo de instalación", 
    title=f"Variabilidad del Costo por Watt en {moneda}"
)

# 📌 **Añadir línea de media específica para cada tipo de instalación**
media_por_tipo = df_filtered.groupby("Tipo de instalación")["COSTO POR WATT"].mean() * factor_cambio

for tipo, media in media_por_tipo.items():
    fig3.add_hline(
        y=media, 
        line_dash="dot", 
        annotation_text=f"Media {tipo}: {media:.2f}",
        annotation_position="top right"
    )

# 📌 **Organizar gráficos en columnas**
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"💰 Distribución de Costos ({moneda})")
    st.plotly_chart(fig1)

with col2:
    st.subheader(f"🏗️ Costo Total de Estructura por Panel ({moneda})")
    st.plotly_chart(fig2)

# 📊 **Mostrar Boxplot en pantalla completa**
st.subheader(f"⚡ Análisis de Outliers en Costo por Watt ({moneda})")
st.plotly_chart(fig3)

# 📋 **Mostrar Tabla de Datos Filtrados con Edición**
st.subheader("📄 Datos Filtrados")
st.data_editor(df_filtered, height=400, use_container_width=True)
