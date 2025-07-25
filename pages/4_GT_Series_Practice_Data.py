 # Importando as bibliotecas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
import altair as alt
import os
# Ignorando warnings - por detalhes estéticos
import warnings
warnings.filterwarnings('ignore')

#header
st.image('header.png')

#title
st.title("Fastest Time Session Data Report")

# Caminho base onde ficam as pastas das etapas
PASTA_ETAPAS = "Arquivos GT Minimum"

# Lista todas as etapas (pastas dentro de "resultados")
etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]

st.header("Seletor de Etapa e Sessão")

# Seletor de etapa
etapa_escolhida = st.selectbox("Escolha a etapa:", sorted(etapas_disponiveis))

# Lista arquivos de corrida (.xlsx) dentro da etapa selecionada
pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)
corridas_disponiveis = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]

# Seletor de corrida
corrida_escolhida = st.selectbox("Escolha a sessão:", sorted(corridas_disponiveis))

# Caminho final do arquivo a ser carregado
caminho_corrida = os.path.join(pasta_etapa, corrida_escolhida)

# Carregando o DataFrame
sessao = pd.read_excel(caminho_corrida)

# Não limitando o número de linhas que poderão ser visualizadas
pd.set_option('display.max_rows', None)

#Calculating the fastest time for each driver
fastest_lap_global = sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')

carros_mercedes = [8, 3, 76]
carros_lamborhini = [420]
carros_ferrari = [10]
carros_porsche = [55]
carros_lamborghini_trofeo = [85]

def marca(x):
    if x in carros_mercedes:
        return 'Mercedes'
    if x in carros_lamborhini:
        return 'Lamborhini'
    if x in carros_ferrari:
        return 'Ferrari'
    if x in carros_porsche:
        return 'Porsche'
    else:
        return 'Lamborghini Trofeo'
    
# Cria uma nova coluna com o nome "Montadora" e aplica a função "marca" para o dataframe
sessao['Montadora'] = sessao['Car_ID'].apply(marca)

def equipes(x):
    equipes_dict = {
        8: 'RC', 3: 'KTF',
        76: 'GForce', 420: 'GRID',
        10: 'GForce', 55: 'Stuttgart Motorsport',
        85: 'GForce'
    }
    return equipes_dict.get(x, None)

# Cria uma nova coluna com o nome "equipe" e aplica a função "equipes"
sessao['Equipe'] = sessao['Car_ID'].apply(equipes)

# Criando uma lista para ser utilizada na análise entre os carros e as equipes
analise_equipe = ["Equipe", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
analise_carros = ['Car_ID', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
analise_montadora = ['Montadora', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

# Filtragem automática baseada em 4% da melhor volta da sessão
melhor_volta = sessao["Lap Tm (S)"].min()
tempo_limite = melhor_volta * 1.07

st.subheader("Filtro automático aplicado")
st.write(f"Melhor volta da sessão: **{melhor_volta:.3f} s**")
st.write(f"Filtro de 7% aplicado: **{tempo_limite:.3f} s**")

sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= tempo_limite]

# Lista das colunas que devem ser numéricas
colunas_temporais = ["Lap Tm (S)", "S1 Tm", "S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

# Converte todas essas colunas para float, forçando erros como NaN
for col in colunas_temporais:
    sessao_filtrado[col] = pd.to_numeric(sessao_filtrado[col], errors='coerce')

#Creating a list to select which type of graphs we want to display
option = st.selectbox(
    "Selecione o modo de gráfico",
    ("Tabelas", "Linhas", "BoxPlots", "Outros", "All Laps"),
    index=0  # number 0 is to open it blank
)
# Ordenando pela velocidade dos carros
if option == "Tabelas":
    tabela1 = sessao_filtrado.groupby("Car_ID").agg({
    "Lap Tm (S)": "min",
    "S1 Tm": "min",
    "S2 Tm": "min",
    "S3 Tm": "min",
    "SPT": "max",
    "Avg Speed": "max"
    }).style.background_gradient(cmap='coolwarm').format(precision=3)
    st.header("Melhor tempo/velocidade por carro")
    st.dataframe(tabela1)
 
    tabela2 = sessao_filtrado.groupby("Equipe").agg({
    "Lap Tm (S)": "min",
    "S1 Tm": "min",
    "S2 Tm": "min",
    "S3 Tm": "min",
    "SPT": "max",
    "Avg Speed": "max"
    }).style.background_gradient(cmap='coolwarm').format(precision=3)
    st.header("Melhor tempo/velocidade por equipe")
    st.dataframe(tabela2)

    tabela3 = sessao_filtrado.groupby("Montadora").agg({
    "Lap Tm (S)": "min",
    "S1 Tm": "min",
    "S2 Tm": "min",
    "S3 Tm": "min",
    "SPT": "max",
    "Avg Speed": "max"
    }).style.background_gradient(cmap='coolwarm').format(precision=3)
    st.header("Melhor tempo/velocidade por montadora")
    st.dataframe(tabela3)

elif option == 'Linhas':
    #Lap Time Raising Average
    sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['Lap Tm (S)'].rank(ascending=True) # Criando uma coluna de ranking por carro
    sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking']) # Ordenando os dados por carro e ranking
    graf2 = px.line(sessao_filtrado, x='Ranking', y='Lap Tm (S)', color='Car_ID', title='Lap Time Raising Average') # Criando o gráfico de linha
    st.plotly_chart(graf2)

    #S1 Raising Average
    sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['S1 Tm'].rank(ascending=True)
    sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking'])
    graf3 = px.line(sessao_filtrado, x='Ranking', y='S1 Tm', color='Car_ID', title='S1 Raising Average')
    st.plotly_chart(graf3)

    #S2 Raising Average
    sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['S2 Tm'].rank(ascending=True)
    sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking'])
    graf4 = px.line(sessao_filtrado, x='Ranking', y='S2 Tm', color='Car_ID', title='S2 Raising Average')
    st.plotly_chart(graf4)

    #S3 Raising Average
    sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['S3 Tm'].rank(ascending=True)
    sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking'])
    graf5 = px.line(sessao_filtrado, x='Ranking', y='S3 Tm', color='Car_ID', title='S3 Raising Average')
    st.plotly_chart(graf5)

    #SPT Raising Average
    sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['SPT'].rank(ascending=False)
    sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking'])
    graf6 = px.line(sessao_filtrado, x='Ranking', y='SPT', color='Car_ID', title='SPT Raising Average')
    st.plotly_chart(graf6)

elif option == 'Outros':
  # Tabs para Gap to Fastest
  tabs = st.tabs(["Gap to Fastest Car - Lap", "Gap to Fastest Car - S1", "Gap to Fastest Car - S2", "Gap to Fastest Car - S3"])

  colunas_setores = {
    "Gap to Fastest Car - Lap": "Lap Tm (S)",
    "Gap to Fastest Car - S1": "S1 Tm",
    "Gap to Fastest Car - S2": "S2 Tm",
    "Gap to Fastest Car - S3": "S3 Tm"
  }

  #Dicionário de cores
  cores_personalizadas = {
      "8": 'red',
      "27": 'gray',
      "34": 'yellow'
  }

  for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
    with tabs[i]:
        melhor_por_car_id = sessao_filtrado.groupby('Car_ID')[coluna].min().reset_index()
        min_valor = melhor_por_car_id[coluna].min()
        melhor_por_car_id['Diff'] = melhor_por_car_id[coluna] - min_valor
        melhor_por_car_id = melhor_por_car_id.sort_values(by='Diff')
        melhor_por_car_id['Car_ID'] = melhor_por_car_id['Car_ID'].astype(str)

        # Adiciona a cor personalizada ou padrão
        melhor_por_car_id['Color'] = melhor_por_car_id['Car_ID'].map(cores_personalizadas).fillna('white')
     
        chart = alt.Chart(melhor_por_car_id).mark_bar().encode(
            x=alt.X('Car_ID:N', sort=melhor_por_car_id['Diff'].tolist()),
            y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
            color=alt.Color('Color:N', scale=None)
        ).properties(
            title=f'{tab_name}'
        )

        st.altair_chart(chart, use_container_width=True)
        st.write(f'Baseado no melhor tempo de cada carro para {coluna}')


elif option == 'All Laps':
    alllaps3 = sessao[sessao['Car_ID'] == 3]
    st.write("Auler")
    st.dataframe(alllaps3)

    alllaps8 = sessao[sessao['Car_ID'] == 8]
    st.write("G. Figueiroa")
    st.dataframe(alllaps8)

    alllaps10 = sessao[sessao['Car_ID'] == 10]
    st.write("Nappi")
    st.dataframe(alllaps10)

    alllaps55 = sessao[sessao['Car_ID'] == 55]
    st.write("Marcel Visconde")
    st.dataframe(alllaps55)

    alllaps76 = sessao[sessao['Car_ID'] == 76]
    st.write("P. Bezerra")
    st.dataframe(alllaps76)

    alllaps85 = sessao[sessao['Car_ID'] == 85]
    st.write("Galbinha")
    st.dataframe(alllaps85)

    alllaps420 = sessao[sessao['Car_ID'] == 420]
    st.write("Turco Melik")
    st.dataframe(alllaps420)
