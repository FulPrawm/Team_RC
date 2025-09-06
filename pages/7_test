import streamlit as st
import pandas as pd
import plotly.express as px

# Upload do arquivo
st.title("Gráfico de Dispersão por Carro")
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Ler os dados ignorando as 2 primeiras linhas
    df = pd.read_excel(uploaded_file, skiprows=1)

    # Renomear colunas para facilitar
    df.columns = [str(c) for c in df.columns]

    # Selecionar colunas relevantes
    col_carro = df.columns[1]   # Coluna B
    col_volta = df.columns[4]   # Coluna E
    colunas_y = df.columns[6:]  # Colunas a partir da G

    st.write("### Prévia dos dados:")
    st.dataframe(df[[col_carro, col_volta] + list(colunas_y[:5])])  # mostrar só algumas colunas

    # Escolha da variável Y
    ycol = st.selectbox("Selecione a variável para o eixo Y", colunas_y)

    # Gráfico de dispersão
    fig = px.scatter(
        df,
        x=col_volta,
        y=ycol,
        color=col_carro,
        title=f"Dispersão de {ycol} por Volta e Carro",
        labels={col_volta: "Voltas", ycol: ycol, col_carro: "Carro"},
    )
    st.plotly_chart(fig, use_container_width=True)
