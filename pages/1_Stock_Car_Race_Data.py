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
st.title("Session Data Report")

# Caminho base onde ficam as pastas das etapas
PASTA_ETAPAS = "Arquivos"

# Lista todas as etapas (pastas dentro de "resultados")
etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]

st.header("Seletor de Etapa e Sessão")

# Seletor de etapa
etapa_escolhida = st.selectbox("Escolha a etapa:", sorted(etapas_disponiveis))

# Lista arquivos de corrida (.xlsx) dentro da etapa selecionada
pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)
corridas_disponiveis = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]

# Seletor de corrida
corrida_escolhida = st.selectbox("Escolha a corrida:", sorted(corridas_disponiveis))

# Caminho final do arquivo a ser carregado
caminho_corrida = os.path.join(pasta_etapa, corrida_escolhida)

# Carregando o DataFrame
sessao = pd.read_excel(caminho_corrida)

# Não limitando o número de linhas que poderão ser visualizadas
pd.set_option('display.max_rows', None)

#Creating a new column for Last Lap Difference
sessao['Last Lap Diff'] = sessao.groupby('Car_ID')['Lap Tm (S)'].diff()

#Calculating the fastest time for each driver
fastest_lap_global = sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')

#Creating a new column for the fastest lap difference
sessao['Fast Lap Diff'] = sessao['Lap Tm (S)'] - fastest_lap_global

# Criando 2 grupos para análise, separando o grupo de carros do modelo Corolla e do modelo Cruze
carros_toyota = [301, 4, 30, 111, 38, 81, 5, 7, 9, 21]
carros_mitsubishi = [101, 444, 44, 33, 29, 11, 121, 18, 10, 88]
# Função que verifica se o carro está presente na lista de carros Toyota, se estiver retorna a string 'Toyota', senão retorna "Chevrolet"
def marca(x):
    if x in carros_toyota:
        return 'Toyota'
    if x in carros_mitsubishi:
        return 'Mitsubishi'
    else:
        return 'Chevrolet'
# Cria uma nova coluna com o nome "Montadora" e aplica a função "marca" para o dataframe
sessao['Montadora'] = sessao['Car_ID'].apply(marca)

def equipes(x):
    equipes_dict = {
        18: 'Blau Motorsport', 29: 'Blau Motorsport',
        38: 'Car Racing Sterling', 301: 'Car Racing Sterling',
        21: 'Ipiranga Racing', 30: 'Ipiranga Racing',
        12: 'Amattheis Vogel', 83: 'Amattheis Vogel',
        10: 'RCM Motorsport', 44: 'RCM Motorsport',
        8: 'TMG Racing', 19: 'TMG Racing',
        11: 'Eurofarma RC', 88: 'Eurofarma RC',
        4: 'Crown Racing', 81: 'Crown Racing',
        85: 'Cavaleiro Sports', 90: 'Cavaleiro Sports',
        5: 'FT Cavaleiro', 111: 'FT Cavaleiro',
        0: 'Scuderia Bandeiras', 85: 'Scuderia Bandeiras',
        444: 'Scuderia Bandeiras Sports', 33: 'Scuderia Bandeiras Sports',
        121: 'Car Racing KTF', 101: 'Car Racing KTF',
        7: 'FT Gazoo Racing', 9: 'FT Gazoo Racing',
        120: 'Scuderia Chiarelli', 0: 'Scuderia Chiarelli',
        6: 'A. Mattheis Motorsport'
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
tempo_limite = melhor_volta * 1.04

# Cálculo de voltas por piloto
voltas_por_piloto = sessao.groupby('Car_ID')['Lap'].nunique()

# Piloto com mais voltas (vencedor)
max_voltas = voltas_por_piloto.max()
min_voltas_necessarias = int(np.floor(max_voltas * 0.5))  # arredonda para baixo

# Lista de pilotos que completaram ao menos 50% das voltas
pilotos_validos = voltas_por_piloto[voltas_por_piloto >= min_voltas_necessarias].index

# Aplica filtro de pilotos válidos
sessao_filtrado = sessao[sessao['Car_ID'].isin(pilotos_validos)]

# Aplica filtro de tempo de volta (dentro de 4% da melhor volta)
sessao_filtrado = sessao_filtrado[sessao_filtrado["Lap Tm (S)"] <= tempo_limite]

# Exibição informativa no app
st.subheader("Filtro automático aplicado")
st.write(f"🔍 Melhor volta da sessão: **{melhor_volta:.3f} s**")
st.write(f"📏 Filtro de 4% aplicado: **{tempo_limite:.3f} s**")
st.write(f"🧮 Máximo de voltas completadas: **{max_voltas} voltas**")
st.write(f"⚠️ Apenas pilotos com **pelo menos {min_voltas_necessarias} voltas completadas** foram considerados na análise.")

# Lista das colunas que devem ser numéricas
colunas_temporais = ["Lap Tm (S)", "S1 Tm", "S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

# Converte todas essas colunas para float, forçando erros como NaN
for col in colunas_temporais:
    sessao_filtrado[col] = pd.to_numeric(sessao_filtrado[col], errors='coerce')

#Creating a list to select which type of graphs we want to display
option = st.selectbox(
    "Selecione o modo de gráfico",
    ("Tabelas", "Linhas", "Histogramas", "BoxPlots", "Outros", "All Laps"),
    index=0  # number 0 is to open it blank
)
# Ordenando pela velocidade dos carros
if option == "Tabelas":

    # Cores personalizadas
    def cor_carro(val):
        if val == 10:
            return 'background-color: red; color: white'
        elif val == 11:
            return 'background-color: blue; color: white'
        elif val == 44:
            return 'background-color: gray; color: white'
        elif val == 88:
            return 'background-color: yellow; color: black'
        return ''

    def cor_equipe(val):
        if val == 'Eurofarma RC':
            return 'background-color: yellow; color: black'
        elif val == 'RCM Motorsport':
            return 'background-color: gray; color: white'
        return ''

    def cor_montadora(val):
        if val == 'Mitsubishi':
            return 'background-color: red; color: white'
        return ''

    # TABELA POR CARROS
    df_carros = sessao_filtrado[analise_carros].groupby(by=["Car_ID"]).mean(numeric_only=True).reset_index()
    tabela1 = df_carros.style.background_gradient(cmap='coolwarm')
    tabela1 = tabela1.applymap(cor_carro, subset=['Car_ID']).hide(axis="index")
    st.header("Tabela ordenada pelos carros")
    st.markdown(tabela1.to_html(uuid="tabela1", doctype_html=False), unsafe_allow_html=True)

    # TABELA POR EQUIPES
    df_equipe = sessao_filtrado[analise_equipe].groupby(by=["Equipe"]).mean(numeric_only=True).reset_index()
    tabela2 = df_equipe.style.background_gradient(cmap='coolwarm')
    tabela2 = tabela2.applymap(cor_equipe, subset=['Equipe']).hide(axis="index")
    st.header("Tabela ordenada pelas equipes")
    st.markdown(tabela2.to_html(uuid="tabela2", doctype_html=False), unsafe_allow_html=True)

    # TABELA POR MONTADORAS
    df_montadora = sessao_filtrado[analise_montadora].groupby(by=["Montadora"]).mean(numeric_only=True).reset_index()
    tabela3 = df_montadora.style.background_gradient(cmap='coolwarm')
    tabela3 = tabela3.applymap(cor_montadora, subset=['Montadora']).hide(axis="index")
    st.header("Tabela ordenada pelas montadoras")
    st.markdown(tabela3.to_html(uuid="tabela3", doctype_html=False), unsafe_allow_html=True)

elif option == 'Linhas':
    #Lap Progression
    graf1 = px.line(sessao, x="Lap", y= "Lap Tm (S)", color="Car_ID", title='Lap Time Progression')
    st.plotly_chart(graf1)

    #S1 Progression
    graf9 = px.line(sessao, x="Lap", y= "S1 Tm", color="Car_ID", title='S1 Time Progression')
    st.plotly_chart(graf9)

    #S2 Progression
    graf10 = px.line(sessao, x="Lap", y= "S2 Tm", color="Car_ID", title='S2 Time Progression')
    st.plotly_chart(graf10)

    #S3 Progression
    graf11 = px.line(sessao, x="Lap", y= "S3 Tm", color="Car_ID", title='S3 Time Progression')
    st.plotly_chart(graf11)

    #SPT Progression
    graf12 = px.line(sessao, x="Lap", y= "SPT", color="Car_ID", title='SPT Progression')
    st.plotly_chart(graf12)

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

    #Last Lap Diff Graph
    graf7 = px.line(sessao, x="Lap", y= "Last Lap Diff", color="Car_ID", title='Last Lap Diff')
    st.plotly_chart(graf7)

    #Fast Lap Diff Graph
    graf8 = px.line(sessao, x="Lap", y= "Fast Lap Diff", color="Car_ID", title='Fast Lap Diff')
    st.plotly_chart(graf8)

elif option =='Histogramas':
    for var in analise_carros:
        if var == 'Car_ID':
            continue #skips the column "Car_ID"
        fig = px.histogram(sessao_filtrado[var], nbins=25,title=f'Distribuição de {var}')
        st.plotly_chart(fig)

elif option == 'Outros':
    
  # Scatter de eficiência
  fig = px.scatter(sessao_filtrado, x='Avg Speed', y='SPT', color='Equipe', symbol='Equipe',
                 title="Car Efficiency")
  fig.update_traces(marker_size=10)
  st.plotly_chart(fig)

  # Tabs para Gap to Fastest
  tabs = st.tabs(["Gap to Fastest - Lap", "Gap to Fastest - S1", "Gap to Fastest - S2", "Gap to Fastest - S3"])

  colunas_setores = {
    "Gap to Fastest - Lap": "Lap Tm (S)",
    "Gap to Fastest - S1": "S1 Tm",
    "Gap to Fastest - S2": "S2 Tm",
    "Gap to Fastest - S3": "S3 Tm"
  }

  for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
    with tabs[i]:
        media_por_car_id = sessao_filtrado.groupby('Car_ID')[coluna].mean().reset_index()
        min_valor = media_por_car_id[coluna].min()
        media_por_car_id['Diff'] = media_por_car_id[coluna] - min_valor
        media_por_car_id = media_por_car_id.sort_values(by='Diff')
        media_por_car_id['Car_ID'] = media_por_car_id['Car_ID'].astype(str)

        chart = alt.Chart(media_por_car_id).mark_bar().encode(
            x=alt.X('Car_ID:N', sort=media_por_car_id['Diff'].tolist()),
            y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)')
        ).properties(
            title=f'{tab_name}'
        )

        st.altair_chart(chart, use_container_width=True)
        st.write(f'Baseado na média de cada carro para {coluna}')

elif option == 'BoxPlots':
    st.write('Média de todos os carros da montadora')
    for var in analise_montadora:
        if var == 'Montadora':
            continue
        fig = px.box(sessao_filtrado, 
                     x=sessao_filtrado[var], 
                     points='all', 
                     color='Montadora',
                     title=f'Distribuição de {var}')  # Título dentro do gráfico
        st.plotly_chart(fig)


elif option == 'All Laps':
    alllaps10 = sessao[sessao['Car_ID'] == 10]
    st.write("Ricardo Zonta")
    st.dataframe(alllaps10)

    alllaps11 = sessao[sessao['Car_ID'] == 11]
    st.write("Gaetano Di Mauro")
    st.dataframe(alllaps11)

    alllaps44 = sessao[sessao['Car_ID'] == 44]
    st.write("Bruno Baptista")
    st.dataframe(alllaps44)

    alllaps88 = sessao[sessao['Car_ID'] == 88]
    st.write("Felipe Fraga")
    st.dataframe(alllaps88)
