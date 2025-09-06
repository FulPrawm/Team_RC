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

    # mostrar nomes únicos dos pilotos detectados (apenas para conferência)
    st.write("Pilotos detectados (após limpeza):", df[col_carro].unique().tolist())

    # escolha da coluna Y
    ycol = st.selectbox("Escolha a coluna para o eixo Y", list(colunas_y))

    # converter Y para número (troca vírgula por ponto e força numeric)
    df[ycol] = pd.to_numeric(df[ycol].astype(str).str.replace(",", ".", regex=False), errors="coerce")

    # remover linhas sem x ou y numérico (não queremos pontos inválidos)
    df_plot = df.dropna(subset=[col_volta, ycol]).copy()

    if df_plot.empty:
        st.warning("Depois da limpeza, não há dados numéricos suficientes para plotar.")
    else:
        # mapa de cores fixo por piloto (os nomes devem bater exatamente após a limpeza)
        color_map = {
            "Felipe Fraga": "yellow",
            "Ricardo Zonta": "red",
            "Gaetano Di Mauro": "blue",
            "Bruno Baptista": "gray"
        }

        # tentar criar scatter com trendline por série (trendline_scope='trace')
        try:
            fig = px.scatter(
                df_plot,
                x=col_volta,
                y=ycol,
                color=col_carro,
                color_discrete_map=color_map,
                title=f"Dispersão de {ycol} por Volta e Carro",
                labels={col_volta: "Volta", ycol: ycol, col_carro: "Piloto"},
                trendline="ols",
                trendline_scope="trace",
                trendline_color_override="black"  # trendline em preto para visibilidade
            )
        except Exception as e:
            # fallback: sem trendline, e avisa o usuário
            st.warning("Não foi possível calcular a linha de tendência (biblioteca ausente). Exibindo sem trendline.")
            fig = px.scatter(
                df_plot,
                x=col_volta,
                y=ycol,
                color=col_carro,
                color_discrete_map=color_map,
                title=f"Dispersão de {ycol} por Volta e Carro",
                labels={col_volta: "Volta", ycol: ycol, col_carro: "Piloto"},
            )

        # ordenar por volta para melhorar visual e trendline
        fig.update_traces(marker=dict(size=8), selector=dict(mode="markers"))
        fig.update_layout(xaxis=dict(title="Volta", tickmode="linear", dtick=1))

        st.plotly_chart(fig, use_container_width=True)

        # opcional: mostrar uma tabela curta com os dados que foram efetivamente plotados
        st.write("Amostra dos dados usados no gráfico:")
        st.dataframe(df_plot[[col_carro, col_volta, ycol]].head(50))
