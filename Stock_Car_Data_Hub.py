import streamlit as st
from Data.Y25.Stock_Car_2025_Race_Data import show as show_race_2025
from Data.Y25.Stock_Car_2025_Practice_Data import show as show_practice_2025
# futuramente:
# from Data.Y26.Stock_Car_2026_Race_Data import show as show_race_2026
# from Data.Y26.Stock_Car_2026_Practice_Data import show as show_practice_2026

st.title("Race Analysis System")

# 1️⃣ Seletor de ano
ano = st.sidebar.selectbox("Escolha o ano:", ["2025", "2026"])

# 2️⃣ Seletor de sessão (Race / Practice)
sessao = st.sidebar.selectbox("Escolha a sessão:", ["Race Data", "Practice Data"])

# 3️⃣ Chamando a função correta
if ano == "2025":
    if sessao == "Race Data":
        show_race_2025()
    else:
        show_practice_2025()
elif ano == "2026":
    if sessao == "Race Data":
        st.info("Race 2026 ainda não implementado")
        # show_race_2026()
    else:
        st.info("Practice 2026 ainda não implementado")
        # show_practice_2026()
