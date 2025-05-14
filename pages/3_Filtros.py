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

    valor_minimo = st.number_input(
        "Valor mínimo (KPI/Vitals)", 
        min_value=0, 
        max_value=200, 
        value=st.session_state.get("valor_minimo", 50),
        key="valor_minimo"
    )
    valor_maximo = st.number_input(
        "Valor máximo (KPI/Vitals)", 
        min_value=0, 
        max_value=200, 
        value=st.session_state.get("valor_maximo", 150),
        key="valor_maximo"
    )

    # Verifique se a coluna existe
    if "Calc Lap Time [s]" not in df.columns or "Calc Lap Time [s]" not in df1.columns:
        st.error("A coluna 'Calc Lap Time [s]' não foi encontrada no DataFrame.")
        st.write("Colunas em df:", df.columns.tolist())
        st.write("Colunas em df1:", df1.columns.tolist())
        return

    # Filtro e gráfico - KPI
    df_filter = df[
        (df["Calc Lap Time [s]"] >= valor_minimo) & 
        (df["Calc Lap Time [s]"] <= valor_maximo)
    ]
    st.write("Linhas filtradas - KPI:", len(df_filter))
    if not df_filter.empty:
        fig1 = px.box(df_filter, x="Calc Lap Time [s]")
        st.plotly_chart(fig1, key="kpi_graph")
    else:
        st.warning("Nenhum dado correspondente ao filtro de KPI.")

    # Filtro e gráfico - Vitals
    df1_filter = df1[
        (df1["Calc Lap Time [s]"] >= valor_minimo) & 
        (df1["Calc Lap Time [s]"] <= valor_maximo)
    ]
    st.write("Linhas filtradas - Vitals:", len(df1_filter))
    if not df1_filter.empty:
        fig2 = px.box(df1_filter, x="Calc Lap Time [s]")
        st.plotly_chart(fig2, key="vitals_graph")
    else:
        st.warning("Nenhum dado correspondente ao filtro de Vitals.")

def filtrar_e_exibir_sessao(sessao):
    st.title("Filtragem - Race Session")
    
    valor_maximo = st.number_input(
        "Valor máximo (Race Time)", 
        min_value=0, 
        max_value=200, 
        value=st.session_state.get("valor_max_race", 110),
        key="valor_max_race"
    )

    if "Lap Tm (S)" not in sessao.columns:
        st.error("A coluna 'Lap Tm (S)' não foi encontrada.")
        st.write("Colunas disponíveis:", sessao.columns.tolist())
        return

    sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= valor_maximo]
    st.write("Linhas filtradas - Sessão:", len(sessao_filtrado))

    if not sessao_filtrado.empty:
        fig = px.box(sessao_filtrado, x="Lap Tm (S)")
        st.plotly_chart(fig)
    else:
        st.warning("Nenhum dado correspondente ao filtro de Race Session.")

filtrar_e_exibir_kpi(df, df1)
filtrar_e_exibir_sessao(sessao)
