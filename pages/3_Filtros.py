import streamlit as st
import plotly.express as px
import pandas as pd

# Carregar dados
df = pd.read_excel('performance.xlsx', header=4, skiprows=[5])
df.columns = df.columns.str.strip()
df = df.iloc[:, 6:]
first_col = df.columns[0]
df[first_col] = (
    df[first_col]
    .astype(str)
    .str.strip()
    .str.replace(',', '.', regex=False)
)
df[first_col] = pd.to_numeric(df[first_col], errors='coerce')
df[first_col] = df[first_col] / 1000
for col in df.columns[1:]:
    df[col] = (df[col])

df1 = pd.read_excel("vitals.xlsx", header=4, skiprows=[5])
df1.columns = df1.columns.str.strip()
df1 = df1.iloc[:, 6:]
first_col = df1.columns[0]
df1[first_col] = (
    df1[first_col]
    .astype(str)
    .str.strip()
    .str.replace(',', '.', regex=False)
)
df1[first_col] = pd.to_numeric(df1[first_col], errors='coerce')
df1[first_col] = df1[first_col] / 1000
for col in df1.columns[1:]:
    df1[col] = (df1[col])

sessao = pd.read_excel('sessao.xlsx')
pd.set_option('display.max_rows', None)

def filtrar_e_exibir_kpi(df, df1):
    st.title("Filtragem - KPI e Vitals")

    valor_minimo = st.number_input("Valor mínimo (KPI/Vitals)", min_value=0, max_value=200, value=50)
    valor_maximo = st.number_input("Valor máximo (KPI/Vitals)", min_value=0, max_value=200, value=150)

    # Filtro e gráfico - KPI
    df_filter = df[(df["Calc Lap Time [s]"] >= valor_minimo) & (df["Calc Lap Time [s]"] <= valor_maximo)]
    fig1 = px.box(df_filter, x="Calc Lap Time [s]")
    st.plotly_chart(fig1, key="kpi_graph")

    # Filtro e gráfico - Vitals
    df1_filter = df1[(df1["Calc Lap Time [s]"] >= valor_minimo) & (df1["Calc Lap Time [s]"] <= valor_maximo)]
    fig2 = px.box(df1_filter, x="Calc Lap Time [s]")
    st.plotly_chart(fig2, key="vitals_graph")


def filtrar_e_exibir_sessao(sessao):
    st.title("Filtragem - Race Session")
    valor_maximo = st.number_input("Valor máximo (Race Time)", min_value=0, max_value=200, value=110)
    sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= valor_maximo]
    fig = px.box(sessao_filtrado, x="Lap Tm (S)")
    st.plotly_chart(fig)
