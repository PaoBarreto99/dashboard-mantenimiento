# app.py
# Dashboard de Mantenimiento - Streamlit
# Ejecutar:
# pip install streamlit pandas plotly openpyxl
# streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Mantenimiento",
    page_icon="🔧",
    layout="wide"
)

# ---------------------------------------------------
# ESTILO VISUAL
# ---------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1600px;
}

h1 {
    font-size: 42px !important;
    font-weight: 800 !important;
    color: #111827;
}

.subtitle {
    font-size: 20px;
    color: #6b7280;
    margin-top: -10px;
    margin-bottom: 25px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #edf0f4;
    box-shadow: 0 2px 6px rgba(0,0,0,.03);
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
}

.kpi-value {
    font-size: 40px;
    font-weight: 800;
    color: #111827;
}

.kpi-unit {
    font-size: 18px;
    color: #6b7280;
}

.section-title {
    font-size: 30px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("🔧 MaintDash")
st.sidebar.write("Gestión de Mantenimiento")

st.sidebar.markdown("---")

archivo = st.sidebar.file_uploader(
    "📁 Subir Excel",
    type=["xlsx"]
)

if archivo is None:
    st.info("Subí el archivo datos_mantenimiento.xlsx desde la barra lateral.")
    st.stop()

# ---------------------------------------------------
# LEER EXCEL
# ---------------------------------------------------
df = pd.read_excel(archivo)

# ---------------------------------------------------
# VALIDAR COLUMNAS
# ---------------------------------------------------
columnas = [
    "Fecha",
    "Equipo",
    "Tiempo Operativo (h)",
    "Fallas",
    "Tiempo Reparación (h)"
]

for col in columnas:
    if col not in df.columns:
        st.error(f"Falta columna: {col}")
        st.stop()

# ---------------------------------------------------
# LIMPIEZA
# ---------------------------------------------------
df["Fecha"] = pd.to_datetime(df["Fecha"])
df["Año"] = df["Fecha"].dt.year
df["MesNum"] = df["Fecha"].dt.month

meses_txt = {
    1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
    7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"
}

df["Mes"] = df["MesNum"].map(meses_txt)

# ---------------------------------------------------
# FILTROS
# ---------------------------------------------------
años = sorted(df["Año"].unique())
año_sel = st.sidebar.selectbox("📅 Año", años)

meses = ["Todos"] + list(df["Mes"].unique())
mes_sel = st.sidebar.selectbox("📌 Mes", meses)

df_f = df[df["Año"] == año_sel]

if mes_sel != "Todos":
    df_f = df_f[df_f["Mes"] == mes_sel]

# ---------------------------------------------------
# KPI CALCULOS
# ---------------------------------------------------
tiempo_operativo = df_f["Tiempo Operativo (h)"].sum()
fallas = df_f["Fallas"].sum()
tiempo_rep = df_f["Tiempo Reparación (h)"].sum()

mtbf = tiempo_operativo / fallas if fallas > 0 else 0
mttr = tiempo_rep / fallas if fallas > 0 else 0
disp = mtbf / (mtbf + mttr) if (mtbf + mttr) > 0 else 0

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown("<h1>Dashboard de Mantenimiento</h1>", unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Indicadores clave de rendimiento</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------
# KPI CARDS
# ---------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class='card'>
        <div class='kpi-title'>MTBF</div>
        <div class='kpi-value'>{mtbf:.1f}
            <span class='kpi-unit'> horas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='card'>
        <div class='kpi-title'>MTTR</div>
        <div class='kpi-value'>{mttr:.1f}
            <span class='kpi-unit'> horas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class='card'>
        <div class='kpi-title'>TOTAL FALLAS</div>
        <div class='kpi-value'>{fallas}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class='card'>
        <div class='kpi-title'>T. OPERATIVO</div>
        <div class='kpi-value'>{tiempo_operativo:.0f}
            <span class='kpi-unit'> horas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------
# GRAFICOS SUPERIORES
# ---------------------------------------------------
g1, g2 = st.columns([1,2])

with g1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=disp * 100,
        number={"suffix": "%"},
        gauge={
            "axis": {"range":[0,100]},
            "bar": {"color":"#10b981"},
            "steps":[
                {"range":[0,75], "color":"#fee2e2"},
                {"range":[75,90], "color":"#fef3c7"},
                {"range":[90,100], "color":"#dcfce7"}
            ]
        }
    ))

    fig.update_layout(
        title="Disponibilidad",
        height=420
    )

    st.plotly_chart(fig, use_container_width=True)

with g2:
    fallas_eq = df_f.groupby("Equipo")["Fallas"].sum().reset_index()

    fig2 = px.bar(
        fallas_eq,
        x="Equipo",
        y="Fallas",
        title="Fallas por Equipo",
        color_discrete_sequence=["#2563eb"]
    )

    fig2.update_layout(height=420)

    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# EVOLUCION
# ---------------------------------------------------
st.markdown(
    "<div class='section-title'>Evolución de Indicadores</div>",
    unsafe_allow_html=True
)

df_y = df[df["Año"] == año_sel]

grupo = df_y.groupby("Mes").agg({
    "Tiempo Operativo (h)":"sum",
    "Fallas":"sum",
    "Tiempo Reparación (h)":"sum"
}).reset_index()

grupo["MTBF"] = grupo["Tiempo Operativo (h)"] / grupo["Fallas"]
grupo["MTTR"] = grupo["Tiempo Reparación (h)"] / grupo["Fallas"]
grupo["Disponibilidad"] = grupo["MTBF"] / (
    grupo["MTBF"] + grupo["MTTR"]
) * 100

x1, x2, x3 = st.columns(3)

with x1:
    fig3 = px.line(
        grupo,
        x="Mes",
        y="MTBF",
        markers=True,
        title=f"MTBF — {año_sel}"
    )
    fig3.update_layout(height=320)
    st.plotly_chart(fig3, use_container_width=True)

with x2:
    fig4 = px.line(
        grupo,
        x="Mes",
        y="MTTR",
        markers=True,
        title=f"MTTR — {año_sel}",
        color_discrete_sequence=["orange"]
    )
    fig4.update_layout(height=320)
    st.plotly_chart(fig4, use_container_width=True)

with x3:
    fig5 = px.line(
        grupo,
        x="Mes",
        y="Disponibilidad",
        markers=True,
        title=f"Disponibilidad — {año_sel}",
        color_discrete_sequence=["green"]
    )

    fig5.add_hline(y=90, line_dash="dash", line_color="green")
    fig5.add_hline(y=75, line_dash="dash", line_color="orange")

    fig5.update_layout(height=320)

    st.plotly_chart(fig5, use_container_width=True)
```
