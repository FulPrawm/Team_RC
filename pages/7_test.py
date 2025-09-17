import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Gráfico de Dispersão por Carro (Lap x Métrica)")

uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])
if not uploaded_file:
    st.info("Envie o arquivo Excel (mesmo formato que você usou).")
else:
    # lê: linha 1 = cabeçalho (header), pular a linha 2
    df = pd.read_excel(uploaded_file, header=0, skiprows=[1])

    # colunas conforme sua especificação
    col_carro = df.columns[1]   # coluna B: piloto / carro
    col_volta = df.columns[4]   # coluna E: volta
    colunas_y = df.columns[6:]  # colunas a partir da G (possíveis Ys)

    # 1) limpar nome do piloto (remover tudo depois da vírgula)
    df[col_carro] = df[col_carro].astype(str).str.split(",").str[0].str.strip()

    # 2) extrair número da volta (ex: "Lap 1" -> 1)
    df[col_volta] = pd.to_numeric(
        df[col_volta].astype(str).str.extract(r"(\d+)", expand=False),
        errors="coerce"
    )

    # 3) filtrar voltas válidas até 110% do tempo mais rápido
    if "Calc Lap Time [s]" in df.columns:
        df["Calc Lap Time [s]"] = pd.to_numeric(
            df["Calc Lap Time [s]"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )
        best_lap = df["Calc Lap Time [s]"].min()
        cutoff = best_lap * 1.10
        df = df[df["Calc Lap Time [s]"] <= cutoff]

    # escolha da coluna Y
    ycol = st.selectbox("Escolha a coluna para o eixo Y", list(colunas_y))

    # converter Y para número (troca vírgula por ponto e força numeric)
    df[ycol] = pd.to_numeric(df[ycol].astype(str).str.replace(",", ".", regex=False), errors="coerce")

    # remover linhas sem x ou y numérico (não queremos pontos inválidos)
    df_plot = df.dropna(subset=[col_volta, ycol]).copy()

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

        # gráfico com linha de tendência da mesma cor de cada piloto
        fig = px.scatter(
            df_plot,
            x=col_volta,
            y=ycol,
            color=col_carro,
            color_discrete_map=color_map,
            title=f"Dispersão de {ycol} por Volta e Carro",
            labels={col_volta: "Volta", ycol: ycol, col_carro: "Piloto"},
            trendline="ols",
            trendline_scope="trace"
        )

        # estética
        fig.update_traces(marker=dict(size=8), selector=dict(mode="markers"))
        fig.update_layout(xaxis=dict(title="Volta", tickmode="linear", dtick=1))

        st.plotly_chart(fig, use_container_width=True)
