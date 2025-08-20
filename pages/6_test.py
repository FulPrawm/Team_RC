import streamlit as st
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ------------------------
# Configuração da Página
# ------------------------
st.set_page_config(
    page_title="Relógio / Timer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------
# Atualização automática
# ------------------------
st_autorefresh(interval=1000, limit=None)  # atualiza a cada 1s

# ------------------------
# Sessões de exemplo
# ------------------------
# Você pode trocar aqui pelos seus horários de sessão
sessoes = [
    {"nome": "Treino Livre", "inicio": "2025-08-20 19:55:00", "fim": "2025-08-20 20:05:00"},
    {"nome": "Qualificação", "inicio": "2025-08-20 20:10:00", "fim": "2025-08-20 20:25:00"},
    {"nome": "Corrida", "inicio": "2025-08-20 20:30:00", "fim": "2025-08-20 21:00:00"}
]

# Converter strings para datetime
for sessao in sessoes:
    sessao["inicio"] = datetime.strptime(sessao["inicio"], "%Y-%m-%d %H:%M:%S")
    sessao["fim"] = datetime.strptime(sessao["fim"], "%Y-%m-%d %H:%M:%S")

# ------------------------
# Relógio Atual
# ------------------------
agora = datetime.now()
st.markdown(
    f"<h1 style='text-align:center;'>{agora.strftime('%H:%M:%S')}</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<p style='text-align:center;'>{agora.strftime('%d/%m/%Y')}</p>",
    unsafe_allow_html=True
)

# ------------------------
# Descobrir Sessão Atual e Próxima
# ------------------------
sessao_atual = None
proxima_sessao = None

for i, sessao in enumerate(sessoes):
    if sessao["inicio"] <= agora <= sessao["fim"]:
        sessao_atual = sessao
        if i + 1 < len(sessoes):
            proxima_sessao = sessoes[i + 1]
        break
    elif agora < sessao["inicio"]:
        proxima_sessao = sessao
        break

# ------------------------
# Layout Sessão Atual
# ------------------------
st.markdown("### Sessão Atual:")

if sessao_atual:
    tempo_decorrido = agora - sessao_atual["inicio"]
    tempo_restante = sessao_atual["fim"] - agora

    st.success(
        f"**{sessao_atual['nome']}**  \n"
        f"Início: {sessao_atual['inicio'].strftime('%H:%M:%S')} | "
        f"Fim: {sessao_atual['fim'].strftime('%H:%M:%S')}  \n"
        f"Tempo Decorrido: {str(tempo_decorrido).split('.')[0]} | "
        f"Tempo Restante: {str(tempo_restante).split('.')[0]}"
    )
else:
    st.success("Nenhuma sessão em andamento.")

# ------------------------
# Layout Próxima Sessão
# ------------------------
st.markdown("### Próxima Sessão:")

if proxima_sessao:
    countdown = proxima_sessao["inicio"] - agora

    st.info(
        f"**{proxima_sessao['nome']}**  \n"
        f"Início: {proxima_sessao['inicio'].strftime('%H:%M:%S')}  \n"
        f"Duração: {str(proxima_sessao['fim'] - proxima_sessao['inicio']).split('.')[0]}  \n"
        f"Regressivo: {str(countdown).split('.')[0]}"
    )
else:
    st.info("Nenhuma próxima sessão encontrada.")

