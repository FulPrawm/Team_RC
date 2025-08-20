import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Painel Sessões", layout="wide")

# ------------------------
# Definir as sessões (exemplo fictício)
# ------------------------
sessoes = [
    {"nome": "TL1 - Grupo 1", "inicio": "19:45", "duracao": 30},
    {"nome": "TL1 - Grupo 2", "inicio": "20:30", "duracao": 30},
    {"nome": "TL2 - Grupo 1", "inicio": "21:15", "duracao": 30},
    {"nome": "TL2 - Grupo 2", "inicio": "22:00", "duracao": 30},
    {"nome": "Q1 - Grupo 1", "inicio": "22:45", "duracao": 15},
    {"nome": "Q1 - Grupo 2", "inicio": "23:05", "duracao": 15},
    {"nome": "Q2", "inicio": "23:25", "duracao": 10},
    {"nome": "Q3", "inicio": "23:40", "duracao": 10},
    {"nome": "Corrida 1", "inicio": "00:10", "duracao": 40},
    {"nome": "Corrida 2", "inicio": "01:00", "duracao": 40},
]

# Converter string "HH:MM" para datetime de hoje
def str_to_datetime(hora_str):
    hoje = datetime.now().date()
    h, m = map(int, hora_str.split(":"))
    return datetime.combine(hoje, datetime.min.time()) + timedelta(hours=h, minutes=m)

for s in sessoes:
    s["inicio_dt"] = str_to_datetime(s["inicio"])
    s["fim_dt"] = s["inicio_dt"] + timedelta(minutes=s["duracao"])

# ------------------------
# Atualização automática
# ------------------------
st_autorefresh = st.autorefresh(interval=1000, limit=None)  # atualiza a cada 1 segundo

# ------------------------
# Layout
# ------------------------
agora = datetime.now()

st.markdown(
    f"""
    <div style='text-align:center; font-size:40px; font-weight:bold;'>
        {agora.strftime('%H:%M:%S')}
    </div>
    <div style='text-align:center; font-size:20px;'>
        {agora.strftime('%d/%m/%Y')}
    </div>
    """,
    unsafe_allow_html=True
)

# Identificar sessão atual e próxima
sessao_atual = None
sessao_prox = None
for i, s in enumerate(sessoes):
    if s["inicio_dt"] <= agora < s["fim_dt"]:
        sessao_atual = s
        if i+1 < len(sessoes):
            sessao_prox = sessoes[i+1]
        break
    if agora < s["inicio_dt"]:
        sessao_prox = s
        break

# ---------------- Sessão Atual ----------------
if sessao_atual:
    decorrido = agora - sessao_atual["inicio_dt"]
    restante = sessao_atual["fim_dt"] - agora
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px;'>
            <h2>Sessão Atual: {sessao_atual['nome']}</h2>
            <p><b>Início:</b> {sessao_atual['inicio_dt'].strftime('%H:%M')} &nbsp;&nbsp; 
               <b>Fim:</b> {sessao_atual['fim_dt'].strftime('%H:%M')}</p>
            <p><b>Tempo Decorrido:</b> {str(decorrido).split('.')[0]} &nbsp;&nbsp;
               <b>Tempo Restante:</b> {str(restante).split('.')[0]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px;'>
            <h2>Sessão Atual: -</h2>
            <p><b>Início:</b> - &nbsp;&nbsp; <b>Fim:</b> -</p>
            <p><b>Tempo Decorrido:</b> - &nbsp;&nbsp; <b>Tempo Restante:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- Próxima Sessão ----------------
if sessao_prox:
    regressivo = sessao_prox["inicio_dt"] - agora
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px;'>
            <h2>Próxima Sessão: {sessao_prox['nome']}</h2>
            <p><b>Início:</b> {sessao_prox['inicio_dt'].strftime('%H:%M')}</p>
            <p><b>Duração:</b> {sessao_prox['duracao']:02d} min</p>
            <p><b>Regressivo:</b> <span style='font-size:30px; color:#00e676;'>
            {str(regressivo).split('.')[0]}</span></p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px;'>
            <h2>Próxima Sessão: -</h2>
            <p><b>Início:</b> -</p>
            <p><b>Duração:</b> -</p>
            <p><b>Regressivo:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

