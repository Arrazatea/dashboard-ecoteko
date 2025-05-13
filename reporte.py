import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
from io import BytesIO

st.set_page_config(page_title="Dashboard Ecoteko", layout="wide")
TIPO_CAMBIO = 20.5

def normalize_columns(df):
    df.columns = df.columns.str.strip()
    df.columns = [unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('utf-8') for col in df.columns]
    return df

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

@st.cache_data
def load_data(tipo):
    url = f"https://raw.githubusercontent.com/Arrazatea/dashboard-ecoteko/refs/heads/main/ReporteAbril25{tipo}.csv"
    df = pd.read_csv(url, encoding="latin1")
    df = normalize_columns(df)
    df.rename(columns={"Tipo de instalacion": "Tipo de instalacion"}, inplace=True)
    df = df[df["Mes"].notna()]
    for col in df.columns:
        if "Costo" in col or col in ["Electrico", "Logistica", "Logistica", "Miscelaneos", "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Cuadrilla"] = df.get("Cuadrilla", "Sin asignar").fillna("Sin asignar")
    return df

st.sidebar.markdown("## 🧭 Tipo de Proyecto")
tipo_proyecto = st.sidebar.radio("Selecciona:", ["BT", "MT"])

df = load_data(tipo_proyecto)

moneda = st.sidebar.radio("💱 Moneda:", ["Pesos", "Dólares"])
factor = 1 if moneda == "Pesos" else 1 / TIPO_CAMBIO

if tipo_proyecto == "MT":
    aplicar_iva = st.sidebar.checkbox("💸 Aplicar IVA (excepto mano de obra)", value=True)
    IVA = 1.16 if aplicar_iva else 1.0
else:
    IVA = 1.0

# Filtros
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

if tipo_proyecto == "MT":
    rubros = ["Costo de equipos", "Costo estructura", "Electrico", "Logistica", "Miscelaneos",
              "Tramites", "Verificacion", "Herramienta", "Otros", "Capacitores"]
    rubros_existentes = [r for r in rubros if r in df_filtrado.columns]
    total_costo = sum((df_filtrado[r] * IVA).sum() for r in rubros_existentes)
    if "Costo mano de obra" in df_filtrado.columns:
        total_costo += df_filtrado["Costo mano de obra"].sum()
else:
    total_costo = df_filtrado.get("Costo total", pd.Series(0)).sum()

total_costo *= factor

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("📌 Proyectos", df_filtrado["Nombre del proyecto"].nunique())
col2.metric(f"💰 Costo Total ({moneda})", f"${total_costo:,.0f}")
col3.metric("⚡ Potencia Total", f"{df_filtrado['Potencia del sistema'].sum():,.0f} W")

col4, col5, col6 = st.columns(3)
col4.metric("⚙️ Costo Prom. por Watt", f"${df_filtrado.get('COSTO POR WATT', pd.Series()).mean() * factor:,.2f}")
col5.metric("🔩 Paneles", int(df_filtrado.get("No. de Paneles", pd.Series(0)).sum()))
col6.metric("🏗️ Costo Prom. por Panel", f"${df_filtrado.get('Costo total de estructura por panel', pd.Series()).mean() * factor:,.2f}")

# Exportar a Excel
st.sidebar.markdown("## 📤 Exportar Datos")
if st.sidebar.button("📥 Descargar Excel"):
    output = BytesIO()
    df_filtrado.to_excel(output, index=False)
    st.download_button("📄 Descargar archivo Excel", output.getvalue(), file_name="datos_filtrados.xlsx", mime="application/vnd.ms-excel")

# Gráficas
if tipo_proyecto == "MT":
    rubros_mt = rubros_existentes + ["Costo mano de obra"]
    cost_data = pd.DataFrame({
        "Categoría": [col for col in rubros_mt if col in df_filtrado.columns],
        "Monto": [(df_filtrado[col] * (1 if col == "Costo mano de obra" else IVA)).sum() * factor for col in rubros_mt if col in df_filtrado.columns]
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

if "Costo total de estructura por panel" in df_filtrado.columns and "Nombre del proyecto" in df_filtrado.columns:
    fig2 = px.bar(df_filtrado, x="Nombre del proyecto",
                  y=df_filtrado["Costo total de estructura por panel"] * factor,
                  color="Tipo de instalacion" if "Tipo de instalacion" in df_filtrado.columns else None,
                  title="Costo de Estructura por Panel")
    st.subheader("🏗️ Costo de Estructura por Panel")
    st.plotly_chart(fig2)

if "COSTO POR WATT" in df_filtrado.columns and "Tipo de instalacion" in df_filtrado.columns:
    fig3 = px.box(df_filtrado, x="Tipo de instalacion",
                  y=df_filtrado["COSTO POR WATT"] * factor,
                  color="Tipo de instalacion",
                  title="Variabilidad del Costo por Watt")
    st.subheader("📦 Costo por Watt por Tipo de Instalación")
    st.plotly_chart(fig3)
