 # Importing the libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
import altair as alt
import os
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go


# Ignoring warnings for aesthetic purposes
import warnings
warnings.filterwarnings('ignore')


#header
st.image('header.png')
#title
st.title("Fastest Time Session Data Report")


# Path to where the folders of the rounds are
PASTA_ETAPAS = "Arquivos Treinos & Qualy"
# Lists every round (folders inside "resultados")
etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]
st.header("Round and Session Selector")
etapas_opcoes = ["Select a round..."] + sorted(etapas_disponiveis)
etapa_escolhida = st.selectbox("Choose the round:", etapas_opcoes)
if etapa_escolhida != "Select a round...":
    pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)
    arquivos_xlsx = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]
    corrida_labels = [os.path.splitext(f)[0] for f in arquivos_xlsx]
    corridas_opcoes = ["Select a race..."] + sorted(corrida_labels)
    corrida_label = st.selectbox("Choose a race:", corridas_opcoes)
    if corrida_label != "Select a race...":
        corrida_index = corrida_labels.index(corrida_label)
        corrida_arquivo = arquivos_xlsx[corrida_index]
        corrida_escolhida = corrida_arquivo  # maintaining compabibility
        caminho_corrida = os.path.join(pasta_etapa, corrida_arquivo)


        # ✅ Evertything below stays inside this block
        sessao = pd.read_excel(caminho_corrida)
        # Not limiting the number of rows that can be seen
        pd.set_option('display.max_rows', None)


        #Calculating the fastest time for each driver
        fastest_lap_global = sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')


        # Creating 3 manufacturer groups
        carros_toyota = [301, 4, 30, 111, 38, 81, 5, 7, 9, 21]
        carros_mitsubishi = [101, 444, 44, 33, 29, 11, 121, 18, 10, 88]
        # Function that verifies if the car is Toyota, if not its Mitsubishi, and if its not either, its Chevrolet
        def brand(x):
            if x in carros_toyota:
                return 'Toyota'
            if x in carros_mitsubishi:
                return 'Mitsubishi'
            else:
                return 'Chevrolet'
        # Creating a new column called "Manufacturer" and apllying the fucition "brand"
        sessao['Manufacturer'] = sessao['Car_ID'].apply(brand)
        

        #Defining the teams and their cars
        def Teams(x):
            Teams_dict = {
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
            return Teams_dict.get(x, None)
        # Creating a new column called "Team" and applying the function "Teams"
        sessao['Team'] = sessao['Car_ID'].apply(Teams)
        

        # Creating lists to be used in the analysis
        analise_Team = ["Team", "Manufacturer", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_carros = ['Car_ID', "Team", "Manufacturer", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_Manufacturer = ['Manufacturer', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        

        # Automatic filter based 4% of the Best lap in the session
        melhor_volta = sessao["Lap Tm (S)"].min()
        tempo_limite = melhor_volta * 1.04
        st.subheader("Auto filter applied")
        st.write(f"Best lap in the session: **{melhor_volta:.3f} s**")
        st.write(f"4% filter applied: **{tempo_limite:.3f} s**")
        sessao_filtrado = sessao[sessao["Lap Tm (S)"] <= tempo_limite]
        

        # List of columns that SHOULD be numeric
        colunas_temporais = ["Lap Tm (S)", "S1 Tm", "S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        # Converts these columns to float, forcing errors as NaN
        for col in colunas_temporais:
            sessao_filtrado[col] = pd.to_numeric(sessao_filtrado[col], errors='coerce')
        

        # Creating a list to select which type of graphs we want to display
        option = st.selectbox(
            "Select the type of graph",
            ("Charts", "Lines", "BoxPlots", "Others", "All Laps"),
            index=0  # number 0 is to open it blank
        )
        

        if option == "Charts":
            #By car
            tabela1 = sessao_filtrado.groupby("Car_ID", "Team", "Manufacturer").agg({
            "Lap Tm (S)": "min",
            "S1 Tm": "min",
            "S2 Tm": "min",
            "S3 Tm": "min",
            "SPT": "max",
            "Avg Speed": "max"
            }).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.subheader("Best time/speed by Car")
            st.dataframe(tabela1)
            #By team
            tabela2 = sessao_filtrado.groupby("Team", "Manufacturer).agg({
            "Lap Tm (S)": "min",
            "S1 Tm": "min",
            "S2 Tm": "min",
            "S3 Tm": "min",
            "SPT": "max",
            "Avg Speed": "max"
            }).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.subheader("Best time/speed by Team")
            st.dataframe(tabela2)
            #By Manufacturer
            tabela3 = sessao_filtrado.groupby("Manufacturer").agg({
            "Lap Tm (S)": "min",
            "S1 Tm": "min",
            "S2 Tm": "min",
            "S3 Tm": "min",
            "SPT": "max",
            "Avg Speed": "max"
            }).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.subheader("Best time/speed by Manufacturer")
            st.dataframe(tabela3)
        
        elif option == 'Lines':
            #Lap Time Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Car_ID')['Lap Tm (S)'].rank(ascending=True) # Creates a column ranking the cars
            sessao_filtrado = sessao_filtrado.sort_values(by=['Car_ID', 'Ranking']) # Ordering the data by the ranking
            graf2 = px.line(sessao_filtrado, x='Ranking', y='Lap Tm (S)', color='Car_ID', title='Lap Time Raising Average')
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
        

        elif option == 'Others':
          st.header("Gap to Fastest")
          # Tabs
          tabs = st.tabs(["Gap to Fastest Car - Lap", "Gap to Fastest Car - S1", "Gap to Fastest Car - S2", "Gap to Fastest Car - S3"])
          colunas_setores = {
            "Gap to Fastest Car - Lap": "Lap Tm (S)",
            "Gap to Fastest Car - S1": "S1 Tm",
            "Gap to Fastest Car - S2": "S2 Tm",
            "Gap to Fastest Car - S3": "S3 Tm"
          }
        
          #Color dictionary
          cores_personalizadas = {
              10: 'red',
              11: 'blue',
              44: 'gray',
              88: 'yellow'
          }
        
          for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
            with tabs[i]:
                melhor_por_car_id = sessao_filtrado.groupby('Car_ID')[coluna].min().reset_index()
                min_valor = melhor_por_car_id[coluna].min()
                melhor_por_car_id['Diff'] = melhor_por_car_id[coluna] - min_valor
                melhor_por_car_id = melhor_por_car_id.sort_values(by='Diff')
                melhor_por_car_id['Car_ID_str'] = melhor_por_car_id['Car_ID'].astype(str)
                melhor_por_car_id['Color'] = melhor_por_car_id['Car_ID'].map(cores_personalizadas).fillna('white')

                bars = alt.Chart(melhor_por_car_id).mark_bar().encode(
                        x=alt.X('Car_ID_str:N', sort=melhor_por_car_id['Diff'].tolist()),
                        y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
                        color=alt.Color('Color:N', scale=None)
                )
        
                labels = alt.Chart(melhor_por_car_id).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-2,
                        color='white'
                ).encode(
                        x=alt.X('Car_ID_str:N', sort=melhor_por_car_id['Diff'].tolist()),
                        y='Diff',
                        text=alt.Text('Diff', format='.2f')
                )
        
                chart = (bars + labels).properties(title=tab_name)
        
                st.altair_chart(chart, use_container_width=True)
        

        elif option == 'BoxPlots':
            st.write('Values from every car for each manufacturer')
            for var in analise_Manufacturer:
                if var == 'Manufacturer':
                    continue
                fig = px.box(sessao_filtrado, 
                             x=sessao_filtrado[var], 
                             points='all', 
                             color='Manufacturer',
                             title=f'{var} distribuction')  # Title inside graph
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


    else:
        st.warning("Please, select a race.")
else:
    st.warning("Please, select a round.")



