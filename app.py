import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Mantenimiento",
    page_icon="🔧",
    layout="wide"
)

# ---------------------------------------------------
# CSS PRO
# ---------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
    background-color: #f8fafc;
}

.block-container {
    padding-top: 1rem;
    max-width: 1600px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#1e3a8a,#2563eb);
    color: white;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.card {
    background: white;
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #edf0f4;
    box-shadow: 0 4px 14px rgba(0,0,0,.05);
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
}

.kpi-value {
    font-size: 38px;
    font-weight: 800;
    color: #111827;
}

.section-title {
    font-size: 28px;
    font-weight: 800;
    margin-top: 15px;
}

small {
    color:#6b7280;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARGAR CSV INTELIGENTE
# ---------------------------------------------------
archivo = Path("datos_mantenimiento.csv")

if not archivo.exists():
    st.error("No se encontró datos_mantenimiento.csv en el repositorio.")
    st.stop()

try:
    df = pd.read_csv(
        archivo,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )
except Exception as e:
    st.error(f"Error leyendo CSV: {e}")
    st.stop()

# limpiar encabezados
df.columns = (
    df.columns
    .str.strip()
    .str.replace("\ufeff", "", regex=False)
)

# normalizar nombres
rename_map = {}

for col in df.columns:
    c = col.lower().strip()

    if c == "fecha":
        rename_map[col] = "Fecha"

    elif c == "equipo":
        rename_map[col] = "Equipo"

    elif "operativo" in c:
        rename_map[col] = "Tiempo Operativo (h)"

    elif c == "fallas":
        rename_map[col] = "Fallas"

    elif "reparación" in c or "reparacion" in c:
        rename_map[col] = "Tiempo Reparación (h)"

df = df.rename(columns=rename_map)

# validar
cols = [
    "Fecha",
    "Equipo",
    "Tiempo Operativo (h)",
    "Fallas",
    "Tiempo Reparación (h)"
]

faltantes = [c for c in cols if c not in df.columns]

if faltantes:
    st.error(f"Faltan columnas: {faltantes}")
    st.write("Columnas detectadas:", list(df.columns))
    st.stop()

# ---------------------------------------------------
# FECHAS
# ---------------------------------------------------
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df = df.dropna(subset=["Fecha"])

df["Año"] = df["Fecha"].dt.year
df["MesNum"] = df["Fecha"].dt.month

meses = {
1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"
}

df["Mes"] = df["MesNum"].map(meses)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("🔧 MaintDash")
st.sidebar.markdown("### Gestión Inteligente")

años = sorted(df["Año"].unique())
año_sel = st.sidebar.selectbox(
    "📅 Año",
    años,
    index=len(años)-1
)

mes_sel = st.sidebar.selectbox(
    "📌 Mes",
    ["Todos"] + list(df["Mes"].dropna().unique())
)

# ---------------------------------------------------
# FILTRO
# ---------------------------------------------------
df_f = df[df["Año"] == año_sel].copy()

if mes_sel != "Todos":
    df_f = df_f[df_f["Mes"] == mes_sel]

# ---------------------------------------------------
# KPI
# ---------------------------------------------------
t_op = df_f["Tiempo Operativo (h)"].sum()
fallas = df_f["Fallas"].sum()
t_rep = df_f["Tiempo Reparación (h)"].sum()

mtbf = t_op / fallas if fallas > 0 else 0
mttr = t_rep / fallas if fallas > 0 else 0
disp = (mtbf / (mtbf + mttr))*100 if (mtbf + mttr) > 0 else 0

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("Dashboard de Mantenimiento")
st.caption("KPIs operativos y confiabilidad")

# ---------------------------------------------------
# KPIS
# ---------------------------------------------------
c1,c2,c3,c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">MTBF</div>
        <div class="kpi-value">{mtbf:.1f}</div>
        <small>Horas entre fallas</small>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">MTTR</div>
        <div class="kpi-value">{mttr:.1f}</div>
        <small>Horas reparación</small>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">TOTAL FALLAS</div>
        <div class="kpi-value">{int(fallas)}</div>
        <small>Eventos registrados</small>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">DISPONIBILIDAD</div>
        <div class="kpi-value">{disp:.1f}%</div>
        <small>Eficiencia operacional</small>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------
# GRAFICOS SUPERIORES
# ---------------------------------------------------
g1,g2 = st.columns([1,2])

with g1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=disp,
        number={"suffix":"%"},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":"#10b981"},
            "steps":[
                {"range":[0,75],"color":"#fee2e2"},
                {"range":[75,90],"color":"#fef3c7"},
                {"range":[90,100],"color":"#dcfce7"}
            ]
        }
    ))
    fig.update_layout(height=420,title="Disponibilidad")
    st.plotly_chart(fig,use_container_width=True)

with g2:
    fe = df_f.groupby("Equipo")["Fallas"].sum().reset_index()

    fig2 = px.bar(
        fe,
        x="Equipo",
        y="Fallas",
        title="Fallas por Equipo",
        color_discrete_sequence=["#2563eb"]
    )

    fig2.update_layout(height=420)
    st.plotly_chart(fig2,use_container_width=True)

# ---------------------------------------------------
# EVOLUCION
# ---------------------------------------------------
st.markdown(
    "<div class='section-title'>Evolución de Indicadores</div>",
    unsafe_allow_html=True
)

df_y = df[df["Año"] == año_sel].copy()

if mes_sel != "Todos":
    df_y = df_y[df_y["Mes"] == mes_sel]

grupo = df_y.groupby(["MesNum","Mes"]).agg({
    "Tiempo Operativo (h)":"sum",
    "Fallas":"sum",
    "Tiempo Reparación (h)":"sum"
}).reset_index()

grupo["MTBF"] = grupo["Tiempo Operativo (h)"] / grupo["Fallas"]
grupo["MTTR"] = grupo["Tiempo Reparación (h)"] / grupo["Fallas"]
grupo["Disponibilidad"] = (
    grupo["MTBF"] / (grupo["MTBF"] + grupo["MTTR"])
) * 100

grupo = grupo.sort_values("MesNum")

titulo = mes_sel if mes_sel != "Todos" else str(año_sel)

x1,x2,x3 = st.columns(3)

with x1:
    fig3 = px.line(
        grupo,
        x="Mes",
        y="MTBF",
        markers=True,
        title=f"MTBF - {titulo}"
    )
    st.plotly_chart(fig3,use_container_width=True)

with x2:
    fig4 = px.line(
        grupo,
        x="Mes",
        y="MTTR",
        markers=True,
        title=f"MTTR - {titulo}",
        color_discrete_sequence=["orange"]
    )
    st.plotly_chart(fig4,use_container_width=True)

with x3:
    fig5 = px.line(
        grupo,
        x="Mes",
        y="Disponibilidad",
        markers=True,
        title=f"Disponibilidad - {titulo}",
        color_discrete_sequence=["green"]
    )
    fig5.add_hline(y=90,line_dash="dash")
    fig5.add_hline(y=75,line_dash="dash")
    st.plotly_chart(fig5,use_container_width=True)