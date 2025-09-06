import streamlit as st
import pandas as pd
import plotly.express as px

# Upload do arquivo
st.title("Gráfico de Dispersão por Carro")
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Ler os dados: linha 1 = header, linha 2 = pular
    df = pd.read_excel(uploaded_file, header=0, skiprows=[1])

    # Selecionar colunas relevantes
    col_carro = df.columns[1]   # Coluna B = carro/piloto
    col_volta = df.columns[4]   # Coluna E = volta
    colunas_y = df.columns[6:]  # Colunas a partir da G

    # Limpar nome do piloto (remover tudo depois da vírgula)
    df[col_carro] = df[col_carro].astype(str).str.split(",").str[0]

    # Mapa de cores fixo por piloto
    color_map = {
        "Felipe Fraga": "yellow",
        "Ricardo Zonta": "red",
        "Gaetano Di Mauro": "blue",
        "Bruno Baptista": "gray"
    }

    st.write("### Prévia dos dados:")
    st.dataframe(df[[col_carro, col_volta] + list(colunas_y[:5])])

    # Escolha da variável Y
    ycol = st.selectbox("Selecione a variável para o eixo Y", colunas_y)

    # Gráfico de dispersão com linha de tendência
    fig = px.scatter(
        df,
        x=col_volta,
        y=ycol,
        color=col_carro,
        color_discrete_map=color_map,
        trendline="ols",
        title=f"Dispersão de {ycol} por Volta e Carro",
        labels={col_volta: "Voltas", ycol: ycol, col_carro: "Carro"},
    )
    st.plotly_chart(fig, use_container_width=True)
