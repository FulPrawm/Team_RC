import streamlit as st
import plotly.express as px

def filtrar_e_exibir_kpi(df, df1):
    st.title("Filtragem - KPI e Vitals")

    valor_minimo = st.number_input("Valor mínimo (KPI/Vitals)", min_value=0, max_value=200, value=50)
    valor_maximo = st.number_input("Valor máximo (KPI/Vitals)", min_value=0, max_value=200, value=150)

    # Filtro e gráfico - KPI
    if "Calc Lap Time [s]" in df.columns:
        df_filter = df[(df["Calc Lap Time [s]"] >= valor_minimo) & (df["Calc Lap Time [s]"] <= valor_maximo)]
        fig1 = px.box(df_filter, x="Calc Lap Time [s]")
        st.plotly_chart(fig1, key="kpi_graph")

    # Filtro e gráfico - Vitals
    if "Calc Lap Time [s]" in df1.columns:
        df1_filter = df1[(df1["Calc Lap Time [s]"] >= valor_minimo) & (df1["Calc Lap Time [s]"] <= valor_maximo)]
        fig2 = px.box(df1_filter, x="Calc Lap Time [s]")
        st.plotly_chart(fig2, key="vitals_graph")


def filtrar_e_exibir_sessao(sessao):
    st.title("Filtragem - Race Session")

    valor_maximo = st.number_input("Valor máximo (Race Time)", min_value=0, max_value=200, value=110)
    
    if "Lap Tm (S)" in sessao.columns:
        sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= valor_maximo]
        fig = px.box(sessao_filtrado, x="Lap Tm (S)")
        st.plotly_chart(fig)
