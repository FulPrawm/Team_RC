import streamlit as st
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Timers", layout="centered")
st.title("⏳ Timers para horários específicos (UTC-3)")

# Lista de horários alvo (hora, minuto)
horarios_alvo = [(16,30), (16,45), (16,50), (16,55)]

# Função para calcular tempo restante
def get_tempo_restante(hora, minuto):
    agora = datetime.now(timezone(timedelta(hours=-3)))
    alvo = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    if agora > alvo:
        alvo += timedelta(days=1)  # joga para amanhã se já passou
    return alvo - agora

# Criar placeholders para cada horário
placeholders = [st.empty() for _ in horarios_alvo]

# Loop de atualização
while True:
    for i, (hora, minuto) in enumerate(horarios_alvo):
        restante = get_tempo_restante(hora, minuto)

        if restante.total_seconds() <= 0:
            msg = f"## ✅ {hora:02d}:{minuto:02d} atingido!"
        else:
            h, r = divmod(int(restante.total_seconds()), 3600)
            m, s = divmod(r, 60)
            msg = f"""
            <div style="padding:15px; border-radius:15px; background:#1e1e1e; color:white; text-align:center;">
                <h2>🕒 {hora:02d}:{minuto:02d} (UTC-3)</h2>
                <h1 style="font-size:60px;">{h:02d}:{m:02d}:{s:02d}</h1>
            </div>
            """
        placeholders[i].markdown(msg, unsafe_allow_html=True)

    time.sleep(1)
