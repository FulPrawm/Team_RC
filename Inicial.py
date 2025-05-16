 # Importando as bibliotecas
import streamlit as st

#header
st.image('header.png')
st.title('Data Report')
st.header('Dados referentes a corrida da' \
' ET01 em Interlagos - 2025')
st.write('Por favor selecione a opção desejada no menu ao lado')
st.write('Race times - gráficos referentes a cronometragem da etapa (tempos de volta, setor, velocidade de reta, etc.)')
st.write('KPI - Dados do Motec (balanço do veículo, grip factors, vitais, etc.)')
st.write('Será necessário filtrar os 3 gráficos pelo tempo de volta para retirar voltas de safety car,de entrada e saída de pit, e outras voltas que o Motec cortou errado')