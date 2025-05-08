 # Importando as bibliotecas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
import altair as alt
# Ignorando warnings - por detalhes estéticos
import warnings
warnings.filterwarnings('ignore')

#header
st.image('header.png')

#title
st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 40px;
        color: #FFFFFF;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.markdown('<div class="title">Session Data Report</div>', unsafe_allow_html=True)

# Importando o dado em .csv para o código em Python através da função read_csv da biblioteca Pandas
sessao = pd.read_excel('sessao.xlsx')
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
        6: 'RTR Sports Team'
    }
    return equipes_dict.get(x, None)

# Cria uma nova coluna com o nome "equipe" e aplica a função "equipes"
sessao['Equipe'] = sessao['Car_ID'].apply(equipes)

# Criando uma lista para ser utilizada na análise entre os carros e as equipes
analise_equipe = ["Equipe", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
analise_carros = ['Car_ID', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
analise_montadora = ['Montadora', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

#Filtering again the dataframe
st.title("Gráfico para filtragem")
valor_maximo = st.number_input("Coloque o valor desejado", min_value=0, max_value=200, value=110)
sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= valor_maximo]
fig = px.box(sessao_filtrado, x="Lap Tm (S)")
st.plotly_chart(fig)

#Creating a list to select which type of graphs we want to display
option = st.selectbox(
    "Selecione o modo de gráfico",
    ("Tabelas", "Linhas", "Histogramas", "BoxPlots", "Outros", "All Laps"),
    index=0  # number 0 is to open it blank
)
# Ordenando pela velocidade dos carros
if option == "Tabelas":
    tabela1 = sessao_filtrado[analise_carros].groupby(by=["Car_ID"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm')
    st.title("Tabela ordenada pelos carros")
    st.dataframe(tabela1)

    # Ordenando pelo tempo de volta das equipes
    tabela2 = sessao_filtrado[analise_equipe].groupby(by=["Equipe"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm')
    st.title("Tabela ordenada pelas equipes")
    st.dataframe(tabela2)

    tabela3 = sessao_filtrado[analise_montadora].groupby(by=["Montadora"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm')
    st.title("Tabela ordenada pelas montadoras")
    st.dataframe(tabela3)

elif option == 'Linhas':
    #Lap Progression
    st.title("Lap Time Progression")
    graf1 = px.line(sessao, x="Lap", y= "Lap Tm (S)", color="Car_ID", title='Lap Time')
    st.plotly_chart(graf1)

    #S1 Progression
    st.title("S1 Progression")
    graf9 = px.line(sessao, x="Lap", y= "S1 Tm", color="Car_ID", title='S1')
    st.plotly_chart(graf9)

    #S2 Progression
    st.title("S2 Time Progression")
    graf10 = px.line(sessao, x="Lap", y= "S2 Tm", color="Car_ID", title='S2')
    st.plotly_chart(graf10)

    #S3 Progression
    st.title("S3 Time Progression")
    graf11 = px.line(sessao, x="Lap", y= "S3 Tm", color="Car_ID", title='S3')
    st.plotly_chart(graf11)

    #SPT Progression
    st.title("SPT Progression")
    graf12 = px.line(sessao, x="Lap", y= "SPT", color="Car_ID", title='SPT')
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
        fig = px.histogram(sessao_filtrado[var], nbins=25)
        st.plotly_chart(fig)

elif option == 'Outros':
    
    #Calculating the efficiency of each car
    fig = px.scatter(sessao_filtrado, x = 'Avg Speed', y = 'SPT', color = 'Equipe', symbol = 'Equipe',
                     title="Car Efficiency")
    fig.update_traces(marker_size=10)
    st.plotly_chart(fig)

    # Calcular a média de 'Lap Tm (S)' para cada 'Car_ID'
    media_por_car_id = sessao_filtrado.groupby('Car_ID')['Lap Tm (S)'].mean().reset_index()

    # Encontrar o valor mínimo de 'Lap Tm (S)'
    min_valor = media_por_car_id['Lap Tm (S)'].min()

    # Calcular a diferença para o menor valor
    media_por_car_id['Diff'] = media_por_car_id['Lap Tm (S)'] - min_valor

    # Ordenar os valores da diferença do menor para o maior
    media_por_car_id = media_por_car_id.sort_values(by='Diff')

    # Garantir que o Car_ID seja tratado como uma categoria, se necessário
    media_por_car_id['Car_ID'] = media_por_car_id['Car_ID'].astype(str)

    # Criar o gráfico de barras com Altair
    chart = alt.Chart(media_por_car_id).mark_bar().encode(
    x=alt.X('Car_ID:N', sort=media_por_car_id['Diff'].tolist()),  # Ordena pelo valor da diferença
    y='Diff'
    ).properties(
    title='Gap to fastest (S)'  # Adiciona o título ao gráfico
    )

    # Exibir o gráfico com Streamlit
    st.altair_chart(chart, use_container_width=True)

elif option == 'BoxPlots':
    for var in analise_montadora:
        if var == 'Montadora':
            continue
        fig = px.box(sessao_filtrado, x = sessao_filtrado[var], points = 'all', color = 'Montadora')
        st.plotly_chart(fig)

elif option == 'All Laps':
    alllaps10 = sessao[sessao['Car_ID'] == 10]
    st.write("Ricardo Zonta")
    st.dataframe(alllaps10)

    alllaps29 = sessao[sessao['Car_ID'] == 29]
    st.write("Daniel Serra")
    st.dataframe(alllaps29)

    alllaps44 = sessao[sessao['Car_ID'] == 44]
    st.write("Bruno Baptista")
    st.dataframe(alllaps44)

    alllaps90 = sessao[sessao['Car_ID'] == 90]
    st.write("Ricardo Mauricio")
    st.dataframe(alllaps90)