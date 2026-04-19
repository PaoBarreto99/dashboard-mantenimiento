# app.py
# Dashboard de Mantenimiento - Streamlit
# Guardado local con CSV
# Ejecutar:
# pip install streamlit pandas plotly
# streamlit run app.py

import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

st.set_page_config(page_title="MaintDash", layout="wide")

FILE = "registros.csv"

# ---------------------------
# FUNCIONES
# ---------------------------
def cargar_datos():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    else:
        df = pd.DataFrame(columns=[
            "Fecha",
            "Equipo",
            "Tiempo Operativo",
            "Fallas",
            "Tiempo Reparacion"
        ])
        return df

def guardar_datos(df):
    df.to_csv(FILE, index=False)

def calcular_kpis(df):
    if df.empty:
        return 0,0,0,0,0

    total_operativo = df["Tiempo Operativo"].sum()
    total_fallas = df["Fallas"].sum()
    total_reparacion = df["Tiempo Reparacion"].sum()

    mtbf = total_operativo / total_fallas if total_fallas > 0 else total_operativo
    mttr = total_reparacion / total_fallas if total_fallas > 0 else 0
    disponibilidad = (
        total_operativo /
        (total_operativo + total_reparacion)
        * 100
    ) if total_operativo > 0 else 0

    return mtbf, mttr, total_fallas, total_operativo, disponibilidad

# ---------------------------
# CARGA
# ---------------------------
df = cargar_datos()

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.title("🔧 MaintDash")
menu = st.sidebar.radio("Menú", ["Dashboard", "Registros"])

# ---------------------------
# DASHBOARD
# ---------------------------
if menu == "Dashboard":

    st.title("Dashboard de Mantenimiento")
    st.caption("Indicadores clave de rendimiento")

    mtbf, mttr, fallas, operativo, disp = calcular_kpis(df)

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("MTBF", f"{mtbf:.2f} h")
    c2.metric("MTTR", f"{mttr:.2f} h")
    c3.metric("Total Fallas", int(fallas))
    c4.metric("Tiempo Operativo", f"{operativo:.2f} h")

    st.divider()

    if not df.empty:

        col1,col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df.groupby("Equipo")["Fallas"].sum().reset_index(),
                x="Equipo",
                y="Fallas",
                title="Fallas por Equipo"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.pie(
                values=[disp, 100-disp],
                names=["Disponible", "No Disponible"],
                title="Disponibilidad (%)"
            )
            st.plotly_chart(fig2, use_container_width=True)

        df["Fecha"] = pd.to_datetime(df["Fecha"])
        df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")

        evol = df.groupby("Mes")["Tiempo Operativo"].sum().reset_index()

        fig3 = px.line(
            evol,
            x="Mes",
            y="Tiempo Operativo",
            markers=True,
            title="Evolución Operativa"
        )

        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.info("No hay registros cargados.")

# ---------------------------
# REGISTROS
# ---------------------------
if menu == "Registros":

    st.title("Registros")

    with st.form("nuevo"):

        c1,c2 = st.columns(2)

        fecha = c1.date_input("Fecha", value=date.today())
        equipo = c2.text_input("Equipo")

        c3,c4,c5 = st.columns(3)

        tiempo = c3.number_input("Tiempo Operativo", 0.0, 9999.0, 40.0)
        fallas = c4.number_input("Fallas", 0, 999, 1)
        reparacion = c5.number_input("Tiempo Reparación", 0.0, 9999.0, 2.0)

        guardar = st.form_submit_button("Guardar")

        if guardar:

            nuevo = pd.DataFrame([{
                "Fecha": fecha,
                "Equipo": equipo,
                "Tiempo Operativo": tiempo,
                "Fallas": fallas,
                "Tiempo Reparacion": reparacion
            }])

            df = pd.concat([df, nuevo], ignore_index=True)
            guardar_datos(df)

            st.success("Registro guardado")
            st.rerun()

    st.divider()

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        if st.button("Eliminar todos los registros"):
            os.remove(FILE)
            st.success("Datos eliminados")
            st.rerun()
    else:
        st.info("Sin registros")