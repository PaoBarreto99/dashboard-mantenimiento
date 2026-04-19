# app.py
# ==========================================================
# MaintDash PRO - Dashboard de Mantenimiento
# Streamlit + Plotly + CSV Local
# Ejecutar:
# pip install streamlit pandas plotly
# streamlit run app.py
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="MaintDash PRO",
    page_icon="🔧",
    layout="wide"
)

FILE = "registros.csv"

# ----------------------------------------------------------
# ESTILOS
# ----------------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
.block-container {
    padding-top: 1rem;
}
div[data-testid="metric-container"] {
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}
.sidebar .sidebar-content {
    background: #0f172a;
}
h1, h2, h3 {
    color:#0f172a;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# FUNCIONES
# ----------------------------------------------------------
def cargar():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    return pd.DataFrame(columns=[
        "Fecha",
        "Equipo",
        "Tiempo Operativo",
        "Fallas",
        "Tiempo Reparacion"
    ])

def guardar(df):
    df.to_csv(FILE, index=False)

def preparar(df):
    if df.empty:
        return df
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    df["Dia"] = df["Fecha"].dt.day
    return df

def kpis(df):
    if df.empty:
        return 0,0,0,0,0

    op = df["Tiempo Operativo"].sum()
    fall = df["Fallas"].sum()
    rep = df["Tiempo Reparacion"].sum()

    mtbf = op / fall if fall > 0 else op
    mttr = rep / fall if fall > 0 else 0
    disp = (op / (op + rep))*100 if op > 0 else 0

    return mtbf, mttr, fall, op, disp

# ----------------------------------------------------------
# CARGA
# ----------------------------------------------------------
df = preparar(cargar())

# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------
st.sidebar.markdown("## 🔧 MaintDash")
st.sidebar.caption("Gestión de Mantenimiento")

menu = st.sidebar.radio(
    "Menú",
    ["Dashboard", "Registros"]
)

# ----------------------------------------------------------
# REGISTROS
# ----------------------------------------------------------
if menu == "Registros":

    st.title("📋 Registros de Mantenimiento")
    st.caption("Agregá registros para alimentar el dashboard.")

    with st.form("nuevo"):

        c1,c2 = st.columns(2)

        fecha = c1.date_input("Fecha", date.today())
        equipo = c2.text_input("Equipo")

        c3,c4,c5 = st.columns(3)

        tiempo = c3.number_input("Tiempo Operativo (h)", 0.0, 9999.0, 40.0)
        fallas = c4.number_input("Fallas", 0, 999, 1)
        reparacion = c5.number_input("Tiempo Reparación (h)", 0.0, 9999.0, 2.0)

        submit = st.form_submit_button("💾 Guardar Registro")

        if submit:
            nuevo = pd.DataFrame([{
                "Fecha": fecha,
                "Equipo": equipo,
                "Tiempo Operativo": tiempo,
                "Fallas": fallas,
                "Tiempo Reparacion": reparacion
            }])

            df2 = pd.concat([df, nuevo], ignore_index=True)
            guardar(df2)
            st.success("Registro guardado.")
            st.rerun()

    st.divider()

    if not df.empty:
        st.subheader("Historial")
        st.dataframe(df, use_container_width=True)

        if st.button("🗑 Eliminar todos los registros"):
            os.remove(FILE)
            st.success("Datos eliminados.")
            st.rerun()

# ----------------------------------------------------------
# DASHBOARD
# ----------------------------------------------------------
if menu == "Dashboard":

    st.title("📊 Dashboard de Mantenimiento")
    st.caption("Indicadores clave de rendimiento")

    if df.empty:
        st.warning("No hay registros cargados.")
        st.stop()

    # FILTROS
    c1,c2 = st.columns(2)

    años = sorted(df["Año"].unique())
    año = c1.selectbox("Año", años)

    meses = ["Todos"] + list(range(1,13))
    mes = c2.selectbox("Mes", meses)

    dff = df[df["Año"] == año]

    if mes != "Todos":
        dff = dff[dff["Mes"] == mes]

    # KPIS
    mtbf, mttr, fall, op, disp = kpis(dff)

    k1,k2,k3,k4 = st.columns(4)

    k1.metric("MTBF", f"{mtbf:.1f} h")
    k2.metric("MTTR", f"{mttr:.1f} h")
    k3.metric("Total Fallas", int(fall))
    k4.metric("Disponibilidad", f"{disp:.1f}%")

    st.divider()

    # PRIMERA FILA
    a,b = st.columns(2)

    with a:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=disp,
            title={'text': "Disponibilidad"},
            gauge={'axis': {'range': [0,100]}}
        ))
        st.plotly_chart(gauge, use_container_width=True)

    with b:
        fallas_equipo = dff.groupby("Equipo")["Fallas"].sum().reset_index()

        fig = px.bar(
            fallas_equipo,
            x="Equipo",
            y="Fallas",
            title="Fallas por Equipo"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------
    # SI ES ANUAL => GRAFICOS MENSUALES
    # ------------------------------------------------------
    if mes == "Todos":

        resumen = []

        for m in range(1,13):
            temp = df[(df["Año"] == año) & (df["Mes"] == m)]

            mtbf_m, mttr_m, _, _, disp_m = kpis(temp)

            resumen.append({
                "Mes": m,
                "MTBF": mtbf_m,
                "MTTR": mttr_m,
                "Disponibilidad": disp_m
            })

        evo = pd.DataFrame(resumen)

        c1,c2 = st.columns(2)

        with c1:
            fig = px.line(
                evo,
                x="Mes",
                y="MTBF",
                markers=True,
                title="Evolución MTBF"
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.line(
                evo,
                x="Mes",
                y="MTTR",
                markers=True,
                title="Evolución MTTR"
            )
            st.plotly_chart(fig, use_container_width=True)

        fig = px.line(
            evo,
            x="Mes",
            y="Disponibilidad",
            markers=True,
            title="Evolución Disponibilidad"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------
    # SI FILTRA MES => DISPONIBILIDAD DIARIA
    # ------------------------------------------------------
    else:

        resumen = []

        for d in sorted(dff["Dia"].unique()):
            temp = dff[dff["Dia"] == d]
            _, _, _, _, disp_d = kpis(temp)

            resumen.append({
                "Día": d,
                "Disponibilidad": disp_d
            })

        diario = pd.DataFrame(resumen)

        fig = px.line(
            diario,
            x="Día",
            y="Disponibilidad",
            markers=True,
            title="Disponibilidad diaria"
        )

        st.plotly_chart(fig, use_container_width=True)