import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Gráfico de Dispersão por Carro")

uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])
if not uploaded_file:
    st.info("Envie o arquivo Excel (mesmo formato que você usou).")
else:
    # lê: linha 1 = cabeçalho (header), pular a linha 2
    df = pd.read_excel(uploaded_file, header=0, skiprows=[1])

    # colunas conforme sua especificação
    col_carro = df.columns[1]   # coluna B: piloto / carro
    col_volta = df.columns[4]   # coluna E: volta
    colunas_y = df.columns[6:]  # colunas a partir da G (possíveis métricas)

    # limpar nome do piloto (remover tudo depois da vírgula)
    df[col_carro] = df[col_carro].astype(str).str.split(",").str[0].str.strip()

    # extrair número da volta (ex: "Lap 1" -> 1)
    df[col_volta] = pd.to_numeric(
        df[col_volta].astype(str).str.extract(r"(\d+)", expand=False),
        errors="coerce"
    )

    # filtrar voltas até 110% da melhor
    if "Calc Lap Time [s]" in df.columns:
        df["Calc Lap Time [s]"] = pd.to_numeric(
            df["Calc Lap Time [s]"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )
        best_lap = df["Calc Lap Time [s]"].min()
        cutoff = best_lap * 1.10
        df = df[df["Calc Lap Time [s]"] <= cutoff]

    # lista de colunas disponíveis para escolha (volta + métricas)
    colunas_disponiveis = [col_volta] + list(colunas_y)
    if "Calc Lap Time [s]" in df.columns:
        colunas_disponiveis = ["Calc Lap Time [s]"] + colunas_disponiveis

    # selects para escolher os eixos
    xcol = st.selectbox("Escolha a coluna para o eixo X", colunas_disponiveis)
    ycol = st.selectbox("Escolha a coluna para o eixo Y", colunas_disponiveis)

    # converter X e Y para numérico
    for c in [xcol, ycol]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")

    # limpar linhas inválidas
    df_plot = df.dropna(subset=[xcol, ycol]).copy()

    if df_plot.empty:
        st.warning("Depois da limpeza/filtro, não há dados numéricos suficientes para plotar.")
    else:
        # mapa de cores fixo por piloto
        color_map = {
            "Felipe Fraga": "yellow",
            "Ricardo Zonta": "red",
            "Gaetano Di Mauro": "blue",
            "Bruno Baptista": "gray"
        }

        # gráfico com linha de tendência colorida por piloto
        fig = px.scatter(
            df_plot,
            x=xcol,
            y=ycol,
            color=col_carro,
            color_discrete_map=color_map,
            title=f"Dispersão: {xcol} x {ycol}",
            labels={xcol: xcol, ycol: ycol, col_carro: "Piloto"},
            trendline="ols",
            trendline_scope="trace"
        )

        fig.update_traces(marker=dict(size=8), selector=dict(mode="markers"))

        st.plotly_chart(fig, use_container_width=True)
