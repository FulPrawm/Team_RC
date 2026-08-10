import streamlit as st

# Header image and title
st.image('header.png', use_container_width=True)
st.title('Instruções')
st.subheader('Dados por Ano e Sessão')

# Main data filtering information
st.info(
    "Nas páginas de Dados de Corrida, Dados de Treino, Análise da Etapa e Análise da Temporada, "
    "o **Filtro** está sempre ativo e é controlado por dois sliders:\n"
    "- **Volta mais rápida da sessão (%):** mantém apenas as voltas dentro dessa porcentagem "
    "acima da volta mais rápida da sessão (padrão: 3%).\n"
    "- **Volta mais rápida de cada piloto (%):** mantém apenas as voltas dentro dessa porcentagem "
    "acima da volta mais rápida de cada piloto (padrão: 3%).\n\n"
    "A Volta 1 é sempre excluída da análise."
)

# Clarifying how 'Race' and 'Practice' pages differ
st.info(
    "**Nota sobre as páginas 'Dados de Corrida' vs. 'Dados de Treino':**\n"
    "- As visualizações são as mesmas nas duas páginas.\n"
    "- A diferença está no método de agregação dos dados:\n"
    "    - **Dados de Corrida:** os tempos de volta e velocidades são calculados pela média das voltas válidas.\n"
    "    - **Dados de Treino:** são usados apenas os melhores tempos e maiores velocidades de cada piloto."
)

# General description of the dashboard
st.markdown("""
### Visão Geral
Este painel fornece dados de desempenho de várias sessões de corrida, organizados por **ano** e tipo de sessão.

Antes de acessar os dados de Corrida ou Treino, o usuário deve selecionar o **ano** desejado na barra lateral.

Cada série de corrida tem uma página dedicada. Dados de uma série não podem ser analisados pela página de outra série.
""")

# Summary of the types of session analysis
st.subheader("Critérios de Análise da Sessão")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Sessões de Corrida")
    st.markdown("- Dados processados usando **tempo médio** e **velocidade média** por piloto/equipe/fabricante.")
    st.markdown("- Buscam refletir o ritmo geral de corrida e a consistência.")

with col2:
    st.markdown("#### Sessões de Treino")
    st.markdown("- Dados processados usando o **melhor tempo** e a **maior velocidade** de cada piloto/equipe/fabricante.")
    st.markdown("- Buscam refletir o desempenho máximo em volta/setor único.")

# Optional section for explaining the charts
with st.expander("Como interpretar os gráficos"):
    st.write("- Todos os gráficos são baseados nos dados fornecidos pelo provedor de cronometragem da categoria (Chronon, no caso da Stock Car).")
    st.write("- Os gaps são exibidos em deltas de tempo relativos à sessão.")
    st.write("- Linhas, cores, boxes e pontos representam pilotos individuais ou agrupamentos de dados.")

# Section for the Watch page
st.subheader("Página Watch")
st.info(
    "A página **Watch** fornece informações em tempo real sobre as sessões do final de semana e permite editar os horários das sessões diretamente pela página, sem acessar o código.\n"
    "- **Dia e Hora Atuais:** mostra a data e a hora atuais.\n"
    "- **Cronograma das Sessões:** horários de início e fim de cada sessão (editáveis).\n"
    "- **Tempo Decorrido e Tempo Restante:** acompanha há quanto tempo uma sessão está em andamento e quanto tempo falta.\n"
    "- **Informações da Próxima Sessão:** exibe a próxima sessão, sua duração e a contagem regressiva até o início."
)

st.markdown("""
### Visão Geral
A página Watch ajuda a manter você atualizado sobre o cronograma de corridas do final de semana. Você pode saber rapidamente:
- Qual sessão está em andamento no momento.
- Há quanto tempo ela está em andamento.
- Quando a próxima sessão vai começar.
- A duração total de cada sessão.
- Contagens regressivas para as próximas sessões.
- Editar os horários das sessões diretamente pela página.
""")

# Section for the MoTeC Graphs page
st.subheader("Página MoTeC Graphs")
st.info(
    "A página **MoTeC Graphs** permite gerar gráficos de dispersão a partir de dados do MoTeC.\n"
    "- Primeiro, gere um relatório em Excel a partir do software MoTeC.\n"
    "- Modifique o arquivo Excel conforme necessário.\n"
    "- Abra o Excel modificado diretamente por esta página para criar as visualizações de dispersão."
)

st.markdown("""
### Visão Geral
Esta página é voltada para análise e visualização de dados avançada:
- Gera gráficos de dispersão para analisar dados e tendências volta a volta.
- Requer pré-processamento dos arquivos Excel antes de carregá-los.
- Ajuda a visualizar diferenças de desempenho entre pilotos, voltas e sessões.
""")
