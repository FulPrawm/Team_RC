import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ------------------------
# Configuration
# ------------------------
st.set_page_config(page_title="Painel de Sessões", layout="centered")
st_autorefresh(interval=1000, limit=None)

# ------------------------
# Timezone
# ------------------------
tz = ZoneInfo("America/Cuiaba")

# ------------------------
# Sessions
# ------------------------
sessions = [
    {"name": "Shakedown - Grupo 1 (Zonta)", "start": "2025-11-13 19:55", "duration": 15},
    {"name": "Shakedown - Grupo 2 (Baptista)", "start": "2025-11-13 20:15", "duration": 15},
    {"name": "TL1 - Grupo 1 (Zonta)", "start": "2025-11-13 21:20", "duration": 30},
    {"name": "TL1 - Grupo 2 (Baptista)", "start": "2025-11-13 22:00", "duration": 30},
    {"name": "TL2 - Grupo 1 (Zonta)", "start": "2025-11-14 14:30", "duration": 30},
    {"name": "TL2 - Grupo 2 (Baptista)", "start": "2025-11-14 15:00", "duration": 30},
    {"name": "Classificatório - Grupo 1 (Zonta e Baptista)", "start": "2025-11-14 18:25", "duration": 50},
    {"name": "Box Aberto", "start": "2025-11-14 20:30", "duration": 10},
    {"name": "Corrida 1", "start": "2025-11-14 21:13", "duration": 32},
    {"name": "Warm Up - Grupo Único", "start": "2025-11-15 17:55", "duration": 10},
    {"name": "Box Aberto", "start": "2025-11-15 20:50", "duration": 10},
    {"name": "Corrida 2", "start": "2025-11-15 21:43", "duration": 52},
]

for s in sessions:
    naive = datetime.strptime(s["start"], "%Y-%m-%d %H:%M")
    start_dt = naive.replace(tzinfo=tz)
    s["start_dt"] = start_dt
    s["end_dt"] = start_dt + timedelta(minutes=s["duration"])

# ------------------------
# Layout
# ------------------------
st.markdown("<h1 style='text-align:center;'>Painel de Sessões</h1>", unsafe_allow_html=True)

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

# ---------------- Próxima Sessão (EM CIMA E DESTACADA) ----------------
if next_session:
    countdown = next_session["start_dt"] - now
    st.markdown(
        f"""
        <div style='background:#1B4F72; color:white; padding:30px; border-radius:20px; margin-top:20px; text-align:center;'>
            <h2 style='font-size:28px;'>Próxima Sessão: {next_session['name']}</h2>
            <p style='font-size:20px;'><b>Início:</b> {next_session['start_dt'].strftime('%d/%m %H:%M')}</p>
            <p style='font-size:20px;'><b>Duração:</b> {next_session['duration']:02d} min</p>
            <p style='font-size:55px; font-weight:bold; margin-top:15px; color:#00FF99;'>
                {str(countdown).split('.')[0]}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div style='background:#1B4F72; color:white; padding:30px; border-radius:20px; margin-top:20px; text-align:center;'>
            <h2 style='font-size:28px;'>Próxima Sessão: -</h2>
            <p><b>Início:</b> -</p>
            <p><b>Duração:</b> -</p>
            <p style='font-size:55px; font-weight:bold; margin-top:15px;'>-</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- Sessão Atual (MENOS DESTAQUE) ----------------
if current_session:
    elapsed = now - current_session["start_dt"]
    remaining = current_session["end_dt"] - now
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:15px;'>
            <h3>Sessão Atual: {current_session['name']}</h3>
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
        """
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:15px;'>
            <h3>Sessão Atual: -</h3>
            <p><b>Início:</b> - &nbsp;&nbsp; <b>Fim:</b> -</p>
            <p><b>Tempo Decorrido:</b> - &nbsp;&nbsp; <b>Tempo Restante:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

