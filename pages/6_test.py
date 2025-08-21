import streamlit as st
from datetime import datetime, timedelta
import pytz
import time

# ==============================
# CONFIGURAÇÕES
# ==============================
st.set_page_config(layout="wide", page_title="Race Timer")

# Definir timezone UTC-3 (São Paulo)
tz = pytz.timezone("America/Sao_Paulo")

# ==============================
# ESTILOS CUSTOMIZADOS
# ==============================
st.markdown("""
    <style>
    /* Fundo geral */
    body {
        background-color: #0e1117;
    }
    /* Relógio */
    .clock {
        font-size: 80px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: -10px;
    }
    /* Data */
    .date {
        font-size: 28px !important;
        text-align: center;
        margin-bottom: 30px;
    }
    /* Títulos */
    h2, h3 {
        font-size: 40px !important;
    }
    /* Blocos */
    .stAlert {
        font-size: 24px !important;
        padding: 25px;
        border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# FUNÇÕES AUXILIARES
# ==============================
def format_timedelta(td):
    """Formata timedelta para HH:MM:SS"""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "00:00:00"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:01}:{minutes:02}:{seconds:02}"

# ==============================
# SESSÕES
# ==============================
# Exemplo de cronograma
sessoes = [
    {
        "nome": "Treino Livre",
        "inicio": tz.localize(datetime(2025, 8, 20, 19, 55, 0)),
        "fim": tz.localize(datetime(2025, 8, 20, 20, 5, 0))
    },
    {
        "nome": "Qualificação",
        "inicio": tz.localize(datetime(2025, 8, 20, 20, 10, 0)),
        "fim": tz.localize(datetime(2025, 8, 20, 20, 25, 0))
    },
    {
        "nome": "Corrida",
        "inicio": tz.localize(datetime(2025, 8, 20, 20, 40, 0)),
        "fim": tz.localize(datetime(2025, 8, 20, 21, 40, 0))
    }
]

# ==============================
# LOOP PRINCIPAL
# ==============================
placeholder = st.empty()

while True:
    with placeholder.container():
        agora = datetime.now(tz)

        # Relógio no topo
        st.markdown(f"<div class='clock'>{agora.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='date'>{agora.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

        # Identificar sessão atual e próxima
        sessao_atual = None
        proxima_sessao = None

        for i, s in enumerate(sessoes):
            if s["inicio"] <= agora <= s["fim"]:
                sessao_atual = s
                if i + 1 < len(sessoes):
                    proxima_sessao = sessoes[i + 1]
                break
            elif agora < s["inicio"]:
                proxima_sessao = s
                break

        # Sessão atual
        if sessao_atual:
            st.subheader("Sessão Atual:")
            tempo_decorrido = agora - sessao_atual["inicio"]
            tempo_restante = sessao_atual["fim"] - agora
            st.success(
                f"**{sessao_atual['nome']}**  \n"
                f"Início: {sessao_atual['inicio'].strftime('%H:%M:%S')} | Fim: {sessao_atual['fim'].strftime('%H:%M:%S')}  \n"
                f"Tempo Decorrido: {format_timedelta(tempo_decorrido)} | Tempo Restante: {format_timedelta(tempo_restante)}"
            )
        else:
            st.subheader("Sessão Atual:")
            st.warning("Nenhuma sessão em andamento no momento.")

        # Próxima sessão
        if proxima_sessao:
            st.subheader("Próxima Sessão:")
            duracao = proxima_sessao["fim"] - proxima_sessao["inicio"]
            regressivo = proxima_sessao["inicio"] - agora
            st.info(
                f"**{proxima_sessao['nome']}**  \n"
                f"Início: {proxima_sessao['inicio'].strftime('%H:%M:%S')}  \n"
                f"Duração: {format_timedelta(duracao)}  \n"
                f"Regressivo: {format_timedelta(regressivo)}"
            )
        else:
            st.subheader("Próxima Sessão:")
            st.warning("Não há mais sessões programadas.")

    time.sleep(1)

