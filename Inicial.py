 # Importando as bibliotecas
import streamlit as st

#header
st.image('header.png')
st.title('Data Report')
st.header('Dados referentes as etapas de 2025')
st.write('Por favor selecione a opção desejada no menu ao lado')
st.write('Race times - gráficos referentes a cronometragem das corridas por tempo/velocidade médio(a) (tempos de volta, setor, velocidade de reta, etc.)')
st.write('Minimum times - gráficos referentes a cronometragem dos treinos/qualy por menor tempo/maior velocidade')
st.write('KPI - Dados do Motec (balanço do veículo, grip factors, vitais, etc.)')
st.write('Também é possível selecionar a etapa e corrida desejada')
st.write('Todos os dados são filtrados com 4% do menor tempo de volta')
