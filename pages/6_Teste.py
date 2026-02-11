import streamlit as st

st.title("Análise de Dados")

# 🔽 Seletor principal
modo = st.sidebar.selectbox(
    "Selecione o tipo de sessão:",
    ["Race Data", "Practice Data"]
)

# ===============================
# FUNÇÕES SEPARADAS
# ===============================

def race_data():
    st.header("Race Data")

    # Exemplo:
    st.write("Aqui entram os gráficos de corrida")

    # suas fórmulas específicas de race
    # seus gráficos específicos de race


def practice_data():
    st.header("Practice Data")

    # Exemplo:
    st.write("Aqui entram os gráficos de treino")

    # suas fórmulas específicas de practice
    # seus gráficos específicos de practice


# ===============================
# EXECUÇÃO CONDICIONAL
# ===============================

if modo == "Race Data":
    race_data()

elif modo == "Practice Data":
    practice_data()
