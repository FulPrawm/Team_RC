import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import os

# ------------------------
# Configuration
# ------------------------
st.set_page_config(page_title="Painel de Sessões", layout="centered")
st_autorefresh(interval=1000, limit=None)

# ------------------------
# Timezone
# ------------------------
tz = ZoneInfo("America/Sao_Paulo")

import pandas as pd

st.markdown("## ⚙️ Ajuste dos Horários das Sessões")

# cria tabela padrão apenas quando a página carrega
if "sessions_df" not in st.session_state:
    st.session_state.sessions_df = pd.DataFrame({
        "Sessão": [
            "Shakedown - Grupo 1 (Regadas)",
            "Shakedown - Grupo 2 (Zonta)",
            "TL1 - Grupo 1 (Regadas)",
            "TL1 - Grupo 2 (Zonta)",
            "TL2 - Grupo 1 (Regadas)",
            "TL2 - Grupo 2 (Zonta)",
            "Classificatório - Grupo 1",
            "Box Aberto",
            "Corrida 1",
            "Warm Up - Grupo Único",
            "Box Aberto",
            "Corrida 2",
            "Férias"
        ],
        "Data": [
            "2025-12-11","2025-12-11","2025-12-12","2025-12-12","2025-12-12","2025-12-12",
            "2025-12-13","2025-12-13","2025-12-13","2025-12-14","2025-12-14","2025-12-14","2025-12-14"
        ],
        "Horário": [
            "16:25","16:40","10:40","11:20","14:10","14:50",
            "09:20","12:50","13:28","09:40","11:20","12:13","13:20"
        ],
        "Duração (min)": [15,15,30,30,30,30,50,10,32,10,10,52,43200]
    })

# editor na tela
st.session_state.sessions_df = st.data_editor(
    st.session_state.sessions_df,
    num_rows="dynamic",
    use_container_width=True
)


sessions = []

for _, row in st.session_state.sessions_df.iterrows():
    try:
        start_str = f"{row['Data']} {row['Horário']}"
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        end_dt = start_dt + timedelta(minutes=int(row["Duração (min)"]))

        sessions.append({
            "name": row["Sessão"],
            "start_dt": start_dt,
            "end_dt": end_dt,
            "duration": int(row["Duração (min)"])
        })
    except:
        pass  # ignora linhas incompletas enquanto você edita

sessions.sort(key=lambda x: x["start_dt"])

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

