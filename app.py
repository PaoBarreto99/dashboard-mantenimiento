import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Mantenimiento 🔧",
    page_icon="🔧",
    layout="wide"
)

# ---------------------------------------------------
# CSS
# ---------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
    background-color: #f8fafc;
}

section[data-testid="stSidebar"] {
    display: none;
}

.block-container {
    max-width: 1600px;
    padding-top: 1rem;
}

.card {
    background: grey;
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #edf0f4;
    box-shadow: 0 4px 14px rgba(0,0,0,.05);
}


.filter-box {
    background: white;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #edf0f4;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# LEER CSV
# ---------------------------------------------------
archivo = Path("datos_mantenimiento.csv")

if not archivo.exists():
    st.error("No se encontró datos_mantenimiento.csv")
    st.stop()

df = pd.read_csv(
    archivo,
    sep=None,
    engine="python",
    encoding="utf-8-sig"
)

df.columns = df.columns.str.strip()

# ---------------------------------------------------
# FECHA ROBUSTA (SOLUCION ERROR)
# ---------------------------------------------------
df["Fecha"] = pd.to_datetime(
    df["Fecha"],
    errors="coerce",
    dayfirst=True
)

df = df.dropna(subset=["Fecha"])

# ---------------------------------------------------
# FECHAS AUX
# ---------------------------------------------------
df["Año"] = df["Fecha"].dt.year
df["MesNum"] = df["Fecha"].dt.month
df["Dia"] = df["Fecha"].dt.day

meses = {
1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"
}

df["Mes"] = df["MesNum"].map(meses)

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("Dashboard de Mantenimiento")
st.caption("KPIs operativos y confiabilidad")

# ---------------------------------------------------
# FILTROS ARRIBA
# ---------------------------------------------------
st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

f1,f2,f3 = st.columns([2,2,1])

años = sorted(df["Año"].unique())

with f1:
    año_sel = st.selectbox("📅 Año", años, index=len(años)-1)

with f2:
    mes_sel = st.selectbox(
        "📌 Mes",
        ["Todos"] + list(df["Mes"].unique())
    )

with f3:
    limpiar = st.button("🧹 Borrar filtros")

st.markdown("</div>", unsafe_allow_html=True)

if limpiar:
    año_sel = max(años)
    mes_sel = "Todos"

# ---------------------------------------------------
# FILTRO DATA
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
# CARDS
# ---------------------------------------------------
c1,c2,c3,c4 = st.columns(4)

cards = [
("MTBF", f"{mtbf:.1f}"),
("MTTR", f"{mttr:.1f}"),
("TOTAL FALLAS", f"{int(fallas)}"),
("DISPONIBILIDAD", f"{disp:.1f}%")
]

for col, item in zip([c1,c2,c3,c4], cards):
    with col:
        st.markdown(f"""
        <div class="card">
        <div class="kpi-title">{item[0]}</div>
        <div class="kpi-value">{item[1]}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------
# TOP GRAFICOS
# ---------------------------------------------------
g1,g2 = st.columns([1,2])

with g1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=disp,
        number={"suffix":"%"},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":"green"}
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
        title="Fallas por Equipo"
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

if mes_sel != "Todos":

    grupo = df_f.groupby("Dia").agg({
        "Tiempo Operativo (h)":"sum",
        "Fallas":"sum",
        "Tiempo Reparación (h)":"sum"
    }).reset_index()

    grupo["MTBF"] = grupo["Tiempo Operativo (h)"] / grupo["Fallas"]
    grupo["MTTR"] = grupo["Tiempo Reparación (h)"] / grupo["Fallas"]
    grupo["Disponibilidad"] = (
        grupo["MTBF"] / (grupo["MTBF"] + grupo["MTTR"])
    )*100

    eje = "Dia"
    titulo = f"{mes_sel} {año_sel}"

else:

    grupo = df_f.groupby(["MesNum","Mes"]).agg({
        "Tiempo Operativo (h)":"sum",
        "Fallas":"sum",
        "Tiempo Reparación (h)":"sum"
    }).reset_index()

    grupo["MTBF"] = grupo["Tiempo Operativo (h)"] / grupo["Fallas"]
    grupo["MTTR"] = grupo["Tiempo Reparación (h)"] / grupo["Fallas"]
    grupo["Disponibilidad"] = (
        grupo["MTBF"] / (grupo["MTBF"] + grupo["MTTR"])
    )*100

    grupo = grupo.sort_values("MesNum")

    eje = "Mes"
    titulo = str(año_sel)

x1,x2,x3 = st.columns(3)

with x1:
    fig3 = px.line(
        grupo,
        x=eje,
        y="MTBF",
        markers=True,
        title=f"MTBF - {titulo}"
    )
    st.plotly_chart(fig3,use_container_width=True)

with x2:
    fig4 = px.line(
        grupo,
        x=eje,
        y="MTTR",
        markers=True,
        title=f"MTTR - {titulo}"
    )
    st.plotly_chart(fig4,use_container_width=True)

with x3:
    fig5 = px.line(
        grupo,
        x=eje,
        y="Disponibilidad",
        markers=True,
        title=f"Disponibilidad - {titulo}"
    )
    fig5.add_hline(y=90,line_dash="dash")
    fig5.add_hline(y=75,line_dash="dash")
    st.plotly_chart(fig5,use_container_width=True)