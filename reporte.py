import streamlit as st
import pandas as pd
import plotly.express as px

# 📌 Debe ser lo primero de Streamlit
st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")

# 📂 Cargar CSV
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteFebrero25.csv"
    df = pd.read_csv(url, encoding="latin1")
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()
    return df

df = load_data()


# 🛠 Limpiar nombres de columnas
df.columns = df.columns.str.strip()

# 💱 **Tipo de Cambio**
TIPO_CAMBIO = 20.5

# 🎨 **Configuración del Dashboard**
#st.set_page_config(page_title="Dashboard Residencial Ecoteko", layout="wide")

# **Estilos CSS Personalizados para Modo Oscuro**
st.markdown("""
    <style>
        body, .main {
            background-color: #101820 !important;
            color: #F2AA4C !important;
        }

        .css-1d391kg, .stSidebar {
            background-color: #1A1A1A !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #F2AA4C !important;
            font-weight: bold;
        }

        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .logo-container img {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# 📌 **Agregar Logo Centrado con Mayor Tamaño**
logo_url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/LOGO.png"
st.markdown(f'<div class="logo-container"><img src="{logo_url}" width="400"></div>', unsafe_allow_html=True)

# 📌 **Título del Dashboard**
st.markdown("# ⚡ Dashboard de Instalaciones Residenciales - Ecoteko")

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
instalaciones_seleccionadas = st.sidebar.multiselect("🏗️ Tipo de Instalacion:", ["Todas"] + list(df["Tipo de instalacion"].unique()), default=["Todas"])

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

# 📌 **KPIs Principales**
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
    potencia_total = df_filtered["Potencia del sistema"].sum()
    st.metric(label="⚡ Potencia Total Instalada", value=f"{potencia_total} W")

col4, col5, col6 = st.columns(3)

with col4:
    costo_promedio_watt = df_filtered["COSTO POR WATT"].mean() * factor_cambio
    st.metric(label=f"⚡ Costo Promedio por Watt ({moneda})", value=f"${costo_promedio_watt:,.2f}")

with col5:
    paneles_instalados = (df_filtered["No. de Paneles"].sum())
    st.metric(label=f"⚡ Número de paneles" , value=f"{paneles_instalados:,.0f}")

with col6:
    costo_promedio_panel = df_filtered["Costo total de estructura por panel"].mean() * factor_cambio
    st.metric(label=f"🏗️ Costo Promedio por Panel ({moneda})", value=f"${costo_promedio_panel:,.2f}")

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
    color_discrete_sequence=["#4682B4", "#FF9999", "#66B3FF"]
)

# 📊 **Gráfico 2: Costos por Tipo de Instalación**
df_grouped = df_filtered.groupby("Tipo de instalacion")[["Costo de equipos", "Costo estructura", "Costo mano de obra"]].sum().reset_index()

fig2 = px.bar(
    df_grouped.melt(id_vars=["Tipo de instalacion"], value_vars=["Costo de equipos", "Costo estructura", "Costo mano de obra"]),
    x="Tipo de instalacion",
    y="value",
    color="variable",
    title=f"Distribución de Costos por Tipo de Instalación ({moneda})"
)

# 📊 **Gráfico 3: Costo Total de Estructura por Panel**
fig3 = px.bar(
    df_filtered, 
    x="Nombre del proyecto", 
    y=df_filtered["Costo total de estructura por panel"] * factor_cambio, 
    color="Tipo de instalacion", 
    title=f"Costo de Estructura por Panel ({moneda})"
)

# 📊 **Gráfico 4: Costo por Watt de cada Instlación**
fig4 = px.bar(
    df_filtered, 
    x="Nombre del proyecto", 
    y=df_filtered["COSTO POR WATT"] * factor_cambio, 
    color="Tipo de instalación", 
    title=f"Costo por Watt ({moneda})"
)

# 📊 **Boxplot del Costo por Watt**
fig5 = px.box(
    df_filtered, 
    y=df_filtered["COSTO POR WATT"] * factor_cambio, 
    x="Tipo de instalación", 
    color="Tipo de instalacion", 
    title=f"Variabilidad del Costo por Watt ({moneda})"
)

# 📌 **Organizar gráficos en columnas**
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"💰 Distribución de Costos ({moneda})")
    st.plotly_chart(fig1)

with col2:
    st.subheader(f"🏗️ Costos por Tipo de Instalación ({moneda})")
    st.plotly_chart(fig2)

st.subheader(f"🏗️ Costo de Estructura por Panel ({moneda})")
st.plotly_chart(fig3)

st.subheader(f"🏗️ Costo por Watt ({moneda})")
st.plotly_chart(fig4)
