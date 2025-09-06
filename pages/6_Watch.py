import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # stdlib (Python 3.9+)

# ------------------------
# Configuration
# ------------------------
st.set_page_config(page_title="Painel de Sessões", layout="centered")
st_autorefresh(interval=1000, limit=None)  # auto-refresh every 1s

# ------------------------
# Timezone (UTC-3)
# ------------------------
tz = ZoneInfo("America/Sao_Paulo")

# ------------------------
# Session schedule
# ------------------------
sessions = [
    {"name": "Warm up - Grupo Único", "start": "2025-09-06 07:30", "duration": 30},
    {"name": "Retirada de Pneus Parque Fechado - Classificatório", "start": "2025-09-06 09:10", "duration": 20},
    {"name": "Qualy", "start": "2025-09-06 10:10", "duration": 50},
    {"name": "Retirada de Pneus Parque Fechado - 1a. Corrida", "start": "2025-09-06 12:40", "duration": 20},
    {"name": "Box Aberto", "start": "2025-09-06 13:40", "duration": 10},
    {"name": "Box Fechado - Todos os carros para Box", "start": "2025-09-06 13:50", "duration": 5},
    {"name": "Formação Imediata do Grid", "start": "2025-09-06 13:57", "duration": 3},
    {"name": "Corrida 1", "start": "2025-09-06 14:33", "duration": 32},
    {"name": "Shakedown - Grupo Único", "start": "2025-09-07 08:00", "duration": 20},
    {"name": "Retirada de Pneus Parque Fechado - 2a. Corrida", "start": "2025-09-07 12:00", "duration": 20},
    {"name": "Box Aberto", "start": "2025-09-07 13:00", "duration": 10},
    {"name": "Box Fechado - Todos os carros para Box", "start": "2025-09-07 13:10", "duration": 5},
    {"name": "Formação Imediata do Grid", "start": "2025-09-07 13:17", "duration": 3},
    {"name": "Corrida 2", "start": "2025-09-07 14:10", "duration": 52},
]

# Convert start times into timezone-aware datetime objects
for s in sessions:
    naive = datetime.strptime(s["start"], "%Y-%m-%d %H:%M")
    start_dt = naive.replace(tzinfo=tz)
    s["start_dt"] = start_dt
    s["end_dt"] = start_dt + timedelta(minutes=s["duration"])

# ------------------------
# Layout
# ------------------------
st.markdown("<h1 style='text-align:center;'>Painel de Sessões</h1>", unsafe_allow_html=True)

# Current time and date (in UTC-3)
now = datetime.now(tz)
st.markdown(
    f"""
    <div style='text-align:center; font-size:40px; font-weight:bold;'>
        {now.strftime('%H:%M:%S')}
    </div>
    <div style='text-align:center; font-size:20px;'>
        {now.strftime('%d/%m/%Y')}
    </div>
    """,
    unsafe_allow_html=True
)

# Detect current and next session
current_session = None
next_session = None
for i, s in enumerate(sessions):
    if s["start_dt"] <= now < s["end_dt"]:
        current_session = s
        if i + 1 < len(sessions):
            next_session = sessions[i + 1]
        break
    if now < s["start_dt"]:
        next_session = s
        break

# ---------------- Sessão Atual ----------------
if current_session:
    elapsed = now - current_session["start_dt"]
    remaining = current_session["end_dt"] - now
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Sessão Atual: {current_session['name']}</h2>
            <p><b>Início:</b> {current_session['start_dt'].strftime('%d/%m %H:%M')} &nbsp;&nbsp; 
               <b>Fim:</b> {current_session['end_dt'].strftime('%d/%m %H:%M')}</p>
            <p><b>Tempo Decorrido:</b> {str(elapsed).split('.')[0]} &nbsp;&nbsp;
               <b>Tempo Restante:</b> {str(remaining).split('.')[0]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Sessão Atual: -</h2>
            <p><b>Início:</b> - &nbsp;&nbsp; <b>Fim:</b> -</p>
            <p><b>Tempo Decorrido:</b> - &nbsp;&nbsp; <b>Tempo Restante:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- Próxima Sessão ----------------
if next_session:
    countdown = next_session["start_dt"] - now
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Próxima Sessão: {next_session['name']}</h2>
            <p><b>Início:</b> {next_session['start_dt'].strftime('%d/%m %H:%M')}</p>
            <p><b>Duração:</b> {next_session['duration']:02d} min</p>
            <p><b>Contagem Regressiva:</b> <span style='font-size:30px; color:#00e676;'>
            {str(countdown).split('.')[0]}</span></p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Próxima Sessão: -</h2>
            <p><b>Início:</b> -</p>
            <p><b>Duração:</b> -</p>
            <p><b>Contagem Regressiva:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

