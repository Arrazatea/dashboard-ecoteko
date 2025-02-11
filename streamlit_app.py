import streamlit as st
import pandas as pd
import plotly.express as px

# 📂 Cargar el archivo CSV desde GitHub o localmente
@st.cache_data
def load_data():
    url = "https://github.com/Arrazatea/dashboard-ecoteko/edit/main/streamlit_app.py#:~:text=README.md-,ResumenEnero25,-.csv"  # ⚠ Cambia esto si el archivo está en GitHub
    return pd.read_csv(url)

df = load_data()

# 🛠 Convertir columnas numéricas
columns_to_clean = ["Costo de equipos", "Costo estructura", "Costo mano de obra", "Costo total", "Costo total de estructura por panel", "COSTO POR WATT"]
for col in columns_to_clean:
    df[col] = df[col].replace('[\$,]', '', regex=True).astype(float)

# 🎨 Configuración del Dashboard
st.title("📊 Dashboard de Instalaciones Fotovoltaicas - Ecoteko")

# 📌 **Filtros interactivos**
mes = st.selectbox("📅 Selecciona el Mes:", ["Todos"] + list(df["Mes"].unique()))
cuadrilla = st.selectbox("👷‍♂️ Selecciona la Cuadrilla:", ["Todas"] + list(df["Cuadrilla"].unique()))
potencia_panel = st.selectbox("🔋 Potencia de Panel:", ["Todas"] + list(df["Potencia de paneles"].unique()))
tipo_instalacion = st.selectbox("🏗️ Tipo de Instalación:", ["Todas"] + list(df["Tipo de instalación"].unique()))

# 🔍 Aplicar filtros
df_filtered = df.copy()
if mes != "Todos":
    df_filtered = df_filtered[df_filtered["Mes"] == mes]
if cuadrilla != "Todas":
    df_filtered = df_filtered[df_filtered["Cuadrilla"] == cuadrilla]
if potencia_panel != "Todas":
    df_filtered = df_filtered[df_filtered["Potencia de paneles"] == potencia_panel]
if tipo_instalacion != "Todas":
    df_filtered = df_filtered[df_filtered["Tipo de instalación"] == tipo_instalacion]

# 📊 **Gráfico 1: Distribución de Costos**
st.subheader("💰 Distribución de Costos en el Costo Total")
cost_distribution = pd.DataFrame({
    "Categoría": ["Equipos", "Estructura", "Mano de Obra"],
    "Porcentaje": [
        df_filtered["Costo de equipos"].sum(),
        df_filtered["Costo estructura"].sum(),
        df_filtered["Costo mano de obra"].sum()
    ]
})
fig1 = px.pie(cost_distribution, names="Categoría", values="Porcentaje", title="Distribución de Costos")
st.plotly_chart(fig1)

# 📊 **Gráfico 2: Costo total de estructura por panel**
st.subheader("🏗️ Costo Total de Estructura por Panel")
fig2 = px.bar(df_filtered, x="Nombre del proyecto", y="Costo total de estructura por panel", color="Tipo de instalación", title="Costo de Estructura por Panel")
st.plotly_chart(fig2)

# 📊 **Gráfico 3: Boxplot del Costo por Watt**
st.subheader("⚡ Análisis de Outliers en Costo por Watt")
fig3 = px.box(df_filtered, y="COSTO POR WATT", color="Tipo de instalación", title="Variabilidad del Costo por Watt")
st.plotly_chart(fig3)

# 📋 **Mostrar Tabla de Datos Filtrados**
st.subheader("📄 Datos Filtrados")
st.dataframe(df_filtered)
