import streamlit as st
import time
from datetime import datetime, timedelta, timezone

st.title("⏳ Timer até 16:30 (UTC-3)")

# Definir o horário alvo (hoje às 16:30 no UTC-3)
agora = datetime.now(timezone(timedelta(hours=-3)))
horario_alvo = agora.replace(hour=16, minute=30, second=0, microsecond=0)

# Se já passou hoje, coloca para amanhã
if agora > horario_alvo:
    horario_alvo += timedelta(days=1)

st.write(f"Horário alvo: {horario_alvo.strftime('%H:%M:%S %Z')}")

placeholder = st.empty()

while True:
    agora = datetime.now(timezone(timedelta(hours=-3)))
    restante = horario_alvo - agora

    if restante.total_seconds() <= 0:
        placeholder.markdown("## ✅ Tempo atingido!")
        break

    horas, resto = divmod(int(restante.total_seconds()), 3600)
    minutos, segundos = divmod(resto, 60)
    placeholder.markdown(f"## ⏳ {horas:02d}:{minutos:02d}:{segundos:02d}")
    time.sleep(1)
