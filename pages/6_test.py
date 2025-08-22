import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# ------------------------
# Configuração
# ------------------------
st.set_page_config(page_title="Painel de Sessões", layout="centered")

# Atualização automática (1 segundo)
st_autorefresh(interval=1000, limit=None)

# ------------------------
# Definição das sessões
# ------------------------
sessoes = [
    {"nome": "Qualy - Grupo 1", "inicio": "15:35", "duracao": 20},
    {"nome": "Qualy - Grupo 2", "inicio": "16:05", "duracao": 20}
]

# Ajustar datas para hoje
hoje = datetime.now().date()
for s in sessoes:
    inicio_dt = datetime.strptime(s["inicio"], "%H:%M").replace(year=hoje.year, month=hoje.month, day=hoje.day)
    s["inicio_dt"] = inicio_dt
    s["fim_dt"] = inicio_dt + timedelta(minutes=s["duracao"])

# ------------------------
# Layout
# ------------------------
st.markdown("<h1 style='text-align:center;'>Painel de Sessões</h1>", unsafe_allow_html=True)

# Relógio e Data
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

# Descobrir sessão atual e próxima
sessao_atual = None
sessao_prox = None
for i, s in enumerate(sessoes):
    if s["inicio_dt"] <= agora < s["fim_dt"]:
        sessao_atual = s
        if i + 1 < len(sessoes):
            sessao_prox = sessoes[i + 1]
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
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
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
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
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
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
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
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Próxima Sessão: -</h2>
            <p><b>Início:</b> -</p>
            <p><b>Duração:</b> -</p>
            <p><b>Regressivo:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

