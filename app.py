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
# ESTILO PREMIUM
# ---------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
    background: linear-gradient(180deg,#eef2ff,#f8fafc);
}

/* ocultar sidebar */
section[data-testid="stSidebar"] {
    display: none;
}

.block-container {
    max-width: 1600px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* TITULOS */
h1 {
    color: #0f172a !important;
    font-weight: 800 !important;
}

/* FILTROS */
.filter-box {
    background: linear-gradient(135deg,#1e293b,#334155);
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 10px 24px rgba(0,0,0,.12);
}

/* CARDS KPI */
.card {
    padding: 24px;
    border-radius: 18px;
    color: white;
    box-shadow: 0 10px 24px rgba(0,0,0,.10);
}

.card1 { background: linear-gradient(135deg,#2563eb,#1d4ed8); }
.card2 { background: linear-gradient(135deg,#7c3aed,#6d28d9); }
.card3 { background: linear-gradient(135deg,#f59e0b,#d97706); }
.card4 { background: linear-gradient(135deg,#059669,#047857); }

.kpi-title {
    font-size: 14px;
    opacity: .9;
}

.kpi-value {
    font-size: 38px;
    font-weight: 800;
    margin-top: 8px;
}

/* secciones */
.section-title {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    margin-top: 12px;
    margin-bottom: 10px;
}

/* eliminar espacios visuales extras */
[data-testid="stVerticalBlock"] > div:empty {
    display:none;
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
# FECHA ROBUSTA
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
# TITULO
# ---------------------------------------------------
st.title("Dashboard de Mantenimiento")

# ---------------------------------------------------
# FILTROS TOP
# ---------------------------------------------------
st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

f1, f2, f3 = st.columns([2,2,1])

años = sorted(df["Año"].unique())

with f1:
    año_sel = st.selectbox(
        "📅 Año",
        años,
        index=len(años)-1
    )

with f2:
    mes_sel = st.selectbox(
        "📌 Mes",
        ["Todos"] + list(df["Mes"].dropna().unique())
    )

with f3:
    limpiar = st.button("🧹 Borrar filtros", use_container_width=True)

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
# KPI CARDS
# ---------------------------------------------------
c1,c2,c3,c4 = st.columns(4)

cards = [
("MTBF", f"{mtbf:.1f}", "card1"),
("MTTR", f"{mttr:.1f}", "card2"),
("TOTAL FALLAS", f"{int(fallas)}", "card3"),
("DISPONIBILIDAD", f"{disp:.1f}%", "card4")
]

for col, item in zip([c1,c2,c3,c4], cards):
    with col:
        st.markdown(f"""
        <div class="card {item[2]}">
            <div class="kpi-title">{item[0]}</div>
            <div class="kpi-value">{item[1]}</div>
        </div>
        """, unsafe_allow_html=True)

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
                {"range":[0,75],"color":"#fecaca"},
                {"range":[75,90],"color":"#fde68a"},
                {"range":[90,100],"color":"#bbf7d0"}
            ]
        }
    ))

    fig.update_layout(
        height=420,
        title="Disponibilidad",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

with g2:
    fe = df_f.groupby("Equipo")["Fallas"].sum().reset_index()

    fig2 = px.bar(
        fe,
        x="Equipo",
        y="Fallas",
        title="Fallas por Equipo",
        color="Equipo",
        color_discrete_sequence=[
            "#2563eb","#7c3aed","#f59e0b","#059669","#dc2626"
        ]
    )

    fig2.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)"
    )

    st.plotly_chart(fig2, use_container_width=True)

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
        title=f"MTBF - {titulo}",
        color_discrete_sequence=["#2563eb"]
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)"
    )
    st.plotly_chart(fig3,use_container_width=True)

with x2:
    fig4 = px.line(
        grupo,
        x=eje,
        y="MTTR",
        markers=True,
        title=f"MTTR - {titulo}",
        color_discrete_sequence=["#f59e0b"]
    )
    fig4.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)"
    )
    st.plotly_chart(fig4,use_container_width=True)

with x3:
    fig5 = px.line(
        grupo,
        x=eje,
        y="Disponibilidad",
        markers=True,
        title=f"Disponibilidad - {titulo}",
        color_discrete_sequence=["#059669"]
    )
    fig5.add_hline(y=90,line_dash="dash")
    fig5.add_hline(y=75,line_dash="dash")
    fig5.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)"
    )
    st.plotly_chart(fig5,use_container_width=True)