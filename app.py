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

ARCHIVO = "datos_mantenimiento.csv"

# ---------------------------------------------------
# ESTILO
# ---------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
    background: linear-gradient(180deg,#eef2ff,#f8fafc);
}

section[data-testid="stSidebar"] {
    display:none;
}

.block-container {
    max-width: 1600px;
    padding-top: 1rem;
}

.card {
    padding:24px;
    border-radius:18px;
    color:white;
    box-shadow:0 10px 24px rgba(0,0,0,.10);
}

.card1 { background: linear-gradient(135deg,#2563eb,#1d4ed8); }
.card2 { background: linear-gradient(135deg,#7c3aed,#6d28d9); }
.card3 { background: linear-gradient(135deg,#f59e0b,#d97706); }
.card4 { background: linear-gradient(135deg,#059669,#047857); }

.kpi-title {font-size:14px;}
.kpi-value {font-size:38px;font-weight:800;}

.filter-box {
    background: linear-gradient(135deg,#1e293b,#334155);
    padding:18px;
    border-radius:18px;
    margin-bottom:20px;
}

.section-title {
    font-size:28px;
    font-weight:800;
    color:#0f172a;
    margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# PANEL ADMIN SUBIR CSV
# ---------------------------------------------------
with st.expander("🔐 Administración / Actualizar Datos"):

    clave = st.text_input(
        "Contraseña",
        type="password"
    )

    if clave == "admin123":

        nuevo = st.file_uploader(
            "Subir nuevo CSV",
            type=["csv"]
        )

        if nuevo is not None:

            with open(ARCHIVO, "wb") as f:
                f.write(nuevo.getbuffer())

            st.success("CSV actualizado correctamente")
            st.rerun()

# ---------------------------------------------------
# CARGAR CSV
# ---------------------------------------------------
archivo = Path(ARCHIVO)

if not archivo.exists():
    st.error("No existe datos_mantenimiento.csv")
    st.stop()

df = pd.read_csv(
    archivo,
    sep=None,
    engine="python",
    encoding="utf-8-sig"
)

df.columns = df.columns.str.strip()

df["Fecha"] = pd.to_datetime(
    df["Fecha"],
    errors="coerce",
    dayfirst=True
)

df = df.dropna(subset=["Fecha"])

# ---------------------------------------------------
# FECHAS
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
# FILTROS
# ---------------------------------------------------
st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

f1,f2,f3,f4 = st.columns([2,2,2,1])

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
        ["Todos"] + list(df["Mes"].unique())
    )

with f3:
    equipo_sel = st.selectbox(
        "🏭 Equipo",
        ["Todos"] + sorted(df["Equipo"].unique())
    )

with f4:
    limpiar = st.button("🧹 Limpiar")

st.markdown("</div>", unsafe_allow_html=True)

if limpiar:
    año_sel = max(años)
    mes_sel = "Todos"
    equipo_sel = "Todos"

# ---------------------------------------------------
# FILTRO DATA
# ---------------------------------------------------
df_f = df[df["Año"] == año_sel].copy()

if mes_sel != "Todos":
    df_f = df_f[df_f["Mes"] == mes_sel]

if equipo_sel != "Todos":
    df_f = df_f[df_f["Equipo"] == equipo_sel]

# ---------------------------------------------------
# KPI
# ---------------------------------------------------
t_op = df_f["Tiempo Operativo (h)"].sum()
fallas = df_f["Fallas"].sum()
t_rep = df_f["Tiempo Reparación (h)"].sum()

mtbf = t_op / fallas if fallas > 0 else 0
mttr = t_rep / fallas if fallas > 0 else 0
disp = (mtbf / (mtbf + mttr))*100 if (mtbf + mttr)>0 else 0

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

for col,item in zip([c1,c2,c3,c4],cards):
    with col:
        st.markdown(f"""
        <div class="card {item[2]}">
        <div class="kpi-title">{item[0]}</div>
        <div class="kpi-value">{item[1]}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# GRAFICOS
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
        title="Fallas por Equipo",
        color="Equipo"
    )

    fig2.update_layout(height=420)
    st.plotly_chart(fig2,use_container_width=True)

# ---------------------------------------------------
# TABLA
# ---------------------------------------------------
st.markdown(
    "<div class='section-title'>Detalle de Registros</div>",
    unsafe_allow_html=True
)

mostrar = df_f.copy()
mostrar["Fecha"] = mostrar["Fecha"].dt.strftime("%d/%m/%Y")

st.dataframe(
    mostrar[[
        "Fecha",
        "Equipo",
        "Tiempo Operativo (h)",
        "Fallas",
        "Tiempo Reparación (h)"
    ]],
    use_container_width=True,
    hide_index=True
)