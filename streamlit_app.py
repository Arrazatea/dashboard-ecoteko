import streamlit as st
import pandas as pd
import plotly.express as px

# 📂 Cargar el archivo CSV desde GitHub
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/main/ResumenEnero25.csv"
    return pd.read_csv(url)

df = load_data()

# 🛠 Convertir columnas numéricas
columns_to_clean = ["Costo de equipos", "Costo estructura", "Costo mano de obra", "Costo total", "Costo total de estructura por panel", "COSTO POR WATT"]
for col in columns_to_clean:
    df[col] = df[col].replace('[\$,]', '', regex=True).astype(float)

# 🎨 Configuración del Dashboard
st.title("📊 Dashboard de Instalaciones Fotovoltaicas - Ecoteko")

# 📌 **Sidebar con Filtros**
st.sidebar.title("⚙️ Filtros")
mes = st.sidebar.selectbox("📅 Selecciona el Mes:", ["Todos"] + list(df["Mes"].unique()))
cuadrilla = st.sidebar.selectbox("👷‍♂️ Selecciona la Cuadrilla:", ["Todas"] + list(df["Cuadrilla"].unique()))
potencia_panel = st.sidebar.selectbox("🔋 Potencia de Panel:", ["Todas"] + list(df["Potencia de paneles"].unique()))
tipo_instalacion = st.sidebar.selectbox("🏗️ Tipo de Instalación:", ["Todas"] + list(df["Tipo de instalación"].unique()))

# 🔍 **Aplicar filtros**
df_filtered = df.copy()
if mes != "Todos":
    df_filtered = df_filtered[df_filtered["Mes"] == mes]
if cuadrilla != "Todas":
    df_filtered = df_filtered[df_filtered["Cuadrilla"] == cuadrilla]
if potencia_panel != "Todas":
    df_filtered = df_filtered[df_filtered["Potencia de paneles"] == potencia_panel]
if tipo_instalacion != "Todas":
    df_filtered = df_filtered[df_filtered["Tipo de instalación"] == tipo_instalacion]

# 📌 **KPIs Principales (Aplicando Filtros)**
st.markdown("## 📊 Indicadores Clave")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_proyectos = df_filtered["Nombre del proyecto"].nunique()
    st.metric(label="📌 Total de Proyectos", value=total_proyectos)

with col2:
    costo_total = df_filtered["Costo total"].sum()
    st.metric(label="💰 Costo Total Instalaciones", value=f"${costo_total:,.0f}")

with col3:
    costo_promedio_panel = df_filtered["Costo total de estructura por panel"].mean()
    st.metric(label="📉 Costo Promedio por Panel", value=f"${costo_promedio_panel:,.2f}")

with col4:
    potencia_total = df_filtered["Potencia de paneles"].sum()
    st.metric(label="⚡ Potencia Total Instalada", value=f"{potencia_total} kW")

# 📊 **Gráfico 1: Distribución de Costos Mejorado**
cost_distribution = pd.DataFrame({
    "Categoría": ["Equipos", "Estructura", "Mano de Obra"],
    "Porcentaje": [
        df_filtered["Costo de equipos"].sum(),
        df_filtered["Costo estructura"].sum(),
        df_filtered["Costo mano de obra"].sum()
    ]
})
fig1 = px.pie(
    cost_distribution, 
    names="Categoría", 
    values="Porcentaje", 
    title="Distribución de Costos",
    color_discrete_sequence=["#4682B4", "#FF9999", "#66B3FF"]
)

# 📊 **Gráfico 2: Costo total de estructura por panel (Eje X mejorado)**
fig2 = px.bar(
    df_filtered, 
    x="Nombre del proyecto", 
    y="Costo total de estructura por panel", 
    color="Tipo de instalación", 
    title="Costo de Estructura por Panel"
)
fig2.update_xaxes(tickangle=-45)  # 🔹 Rotar etiquetas para mejor lectura

# 📊 **Gráfico 3: Boxplot del Costo por Watt**
fig3 = px.box(df_filtered, y="COSTO POR WATT", color="Tipo de instalación", title="Variabilidad del Costo por Watt")

# 📌 **Organizar gráficos en columnas**
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Distribución de Costos")
    st.plotly_chart(fig1)

with col2:
    st.subheader("🏗️ Costo Total de Estructura por Panel")
    st.plotly_chart(fig2)

# 📊 **Mostrar Boxplot en pantalla completa**
st.subheader("⚡ Análisis de Outliers en Costo por Watt")
st.plotly_chart(fig3)

# 📌 **Mapa de Ubicación de Proyectos (si hay coordenadas)**
if "Latitud" in df_filtered.columns and "Longitud" in df_filtered.columns:
    st.subheader("🗺️ Ubicación de Proyectos")
    st.map(df_filtered[["Latitud", "Longitud"]])

# 📋 **Mostrar Tabla de Datos Filtrados con Edición**
st.subheader("📄 Datos Filtrados")
st.data_editor(df_filtered, height=400, use_container_width=True)
