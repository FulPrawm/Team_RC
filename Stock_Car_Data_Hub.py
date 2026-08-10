import os
import streamlit as st

# ======================================
# Password Gate
# ======================================

def _check_password() -> bool:
    """Returns True if the user has entered the correct password."""

    def _submit():
        if st.session_state["pwd_input"] == "Meinharc#01":
            st.session_state["authenticated"] = True
        else:
            st.session_state["auth_error"] = True

    if st.session_state.get("authenticated"):
        return True

    st.title("Sistema de Análise de Corridas")
    st.subheader("🔒 Digite a senha para continuar")

    st.text_input(
        "Senha",
        type="password",
        key="pwd_input",
        on_change=_submit,
        placeholder="Digite a senha e pressione Enter",
    )

    if st.session_state.get("auth_error"):
        st.error("Senha incorreta. Por favor, tente novamente.")
        st.session_state["auth_error"] = False

    return False


if not _check_password():
    st.stop()

# ======================================
# Imports (only after auth)
# ======================================

from Data.Y25.Stock_Car_2025_Race_Data import show as show_race_2025
from Data.Y25.Stock_Car_2025_Practice_Data import show as show_practice_2025
from Data.Y26.Stock_Car_2026_Race_Data import show as show_race_2026
from Data.Y26.Stock_Car_2026_Practice_Data import show as show_practice_2026
from Data.Y26.Stock_Car_2026_Round_Analysis import show as show_round_2026
from Data.Y26.Stock_Car_2026_Season_Analysis import show as show_season_2026

# ======================================
# Sidebar Configuration Panel
# ======================================

st.title("Sistema de Análise de Corridas")

with st.sidebar:
    st.header("Configuração da Sessão")

    year_options = ["Selecione um ano...", "2025", "2026"]
    selected_year = st.selectbox("Escolha o ano:", year_options)

    session_options = ["Selecione uma sessão...", "Dados de Corrida", "Dados de Treino", "Análise da Etapa", "Análise da Temporada"]
    selected_session = st.selectbox("Escolha a sessão:", session_options)

# ======================================
# Navigation Logic
# ======================================

if selected_year == "Selecione um ano...":
    st.info("Por favor, selecione um ano para iniciar a análise.")

elif selected_session == "Selecione uma sessão...":
    st.warning("Por favor, selecione um tipo de sessão.")

else:
    if selected_year == "2025":
        if selected_session == "Dados de Corrida":
            show_race_2025()
        elif selected_session == "Dados de Treino":
            show_practice_2025()

    elif selected_year == "2026":
        if selected_session == "Dados de Corrida":
            show_race_2026()
        elif selected_session == "Dados de Treino":
            show_practice_2026()
        elif selected_session == "Análise da Etapa":
            show_round_2026()
        elif selected_session == "Análise da Temporada":
            show_season_2026()
