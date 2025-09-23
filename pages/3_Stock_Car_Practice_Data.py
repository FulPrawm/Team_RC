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
st.subheader("Round and Session Selector")
etapas_opcoes = ["Select a round..."] + sorted(etapas_disponiveis)
etapa_escolhida = st.selectbox("Choose the round:", etapas_opcoes)
if etapa_escolhida != "Select a round...":
    pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)
    arquivos_xlsx = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]
    corrida_labels = [os.path.splitext(f)[0] for f in arquivos_xlsx]
    corridas_opcoes = ["Select a session..."] + sorted(corrida_labels)
    corrida_label = st.selectbox("Choose a session:", corridas_opcoes)
    if corrida_label != "Select a session...":
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
                51: 'Scuderia Bandeiras', 73: 'Scuderia Bandeiras',
                444: 'Scuderia Bandeiras Sports', 33: 'Scuderia Bandeiras Sports',
                121: 'Car Racing KTF', 101: 'Car Racing KTF',
                7: 'FT Gazoo Racing', 9: 'FT Gazoo Racing',
                0: 'Scuderia Chiarelli', 95: 'Scuderia Chiarelli',
                6: 'A. Mattheis Motorsport'
            }
            return Teams_dict.get(x, None)
        # Creating a new column called "Team" and applying the function "Teams"
        sessao['Team'] = sessao['Car_ID'].apply(Teams)

        # Dictionary relating each team with each manufacturer
        team_to_manufacturer = {
         "Eurofarma RC": "Mitsubishi", "Blau Motorsport": "Mitsubishi",
         "Car Racing Sterling": "Toyota", "Ipiranga Racing": "Toyota",
         "Amattheis Vogel": "Chevrolet", "RCM Motorsport": "Mitsubishi",
         "TMG Racing": "Chevrolet", "Crown Racing": "Toyota",
         "Cavaleiro Sports": "Chevrolet", "FT Cavaleiro": "Toyota",
         "Scuderia Bandeiras": "Chevrolet", "Scuderia Bandeiras Sports": "Mitsubishi",
         "Car Racing KTF": "Mitsubishi", "FT Gazoo Racing": "Toyota",
         "Scuderia Chiarelli": "Chevrolet", "A. Mattheis Motorsport": "Chevrolet"
        } 
        # Creating a new column for what Manufacturer each team races
        sessao['Manufacturer'] = sessao['Team'].map(team_to_manufacturer)
     
        #Last Dictionary relating each car to their drivers
        drivers_dict = {
         18: 'Allam Khodair', 29: 'Daniel Serra',
         38: 'Zezinho Muggiati', 301: 'Rafael Reis',
         21: 'Thiago Camilo', 30: 'Cesar Ramos',
         12: 'Lucas Foresti', 83: 'Gabriel Casagrande',
         10: 'Ricardo Zonta', 44: 'Bruno Baptista',
         8: 'Rafael Suzuki', 19: 'Felipe Massa',
         11: 'Gaetano Di Mauro', 88: 'Felipe Fraga',
         4: 'Julio Campos', 81: 'Arthur Leist',
         85: 'Guilherme Salas', 90: 'Ricardo Mauricio',
         5: 'Denis Navarro', 111: 'Rubens Barrichello',
         73: 'Enzo Elias', 51: 'Átila Abreu',
         444: 'Vicente Orige', 33: 'Nelsinho Piquet',
         121: 'Felipe Baptista', 101: 'Gianluca Petecof',
         7: 'JP Oliveira', 9: 'Arthur Gama',
         95: 'Lucas Kohl', 0: 'Cacá Bueno',
         6: 'Hélio Castroneves'
        }
        sessao['Driver'] = sessao['Car_ID'].map(drivers_dict)


        # Personalized colors with text contrast
        colors_driver = {
            "Ricardo Zonta": ("red", "white"),
            "Gaetano Di Mauro": ("lightblue", "black"),   # azul claro → texto preto
            "Bruno Baptista": ("gray", "white"),
            "Felipe Fraga": ("yellow", "black")      # fundo amarelo → texto preto
        }
        colors_team = {
            "Eurofarma RC": ("yellow", "black"),     # amarelo → preto
            "RCM Motorsport": ("gray", "white")
        }
        colors_manufacturer = {
            "Mitsubishi": ("red", "white")
        }
        # Style functions
        def highlight_driver(s):
            return [
                f"background-color: {colors_driver[v][0]}; color: {colors_driver[v][1]}"
                if v in colors_driver else "" for v in s
            ]
        def highlight_team(s):
            return [
                f"background-color: {colors_team[v][0]}; color: {colors_team[v][1]}"
                if v in colors_team else "" for v in s
            ]
        def highlight_manufacturer(s):
            return [
                f"background-color: {colors_manufacturer[v][0]}; color: {colors_manufacturer[v][1]}"
                if v in colors_manufacturer else "" for v in s
            ]
     
       
        # Creating lists to be used in the analysis
        analise_Team = ["Team", "Manufacturer", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_carros = ["Driver", "Team", "Manufacturer", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_Manufacturer = ['Manufacturer', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        

        # Melhor volta da sessão
        melhor_volta = sessao["Lap Tm (S)"].min()
        
        # Adicionar slider para o usuário escolher a % do filtro
        percentual = st.slider(
            "Select filter percentage (%)",
            min_value=0.0,
            max_value=20.0,
            value=4.0,
            step=1.0,
        )
        
        # Calcular o tempo limite baseado na % escolhida
        tempo_limite = melhor_volta * (1 + percentual / 100)
        
        # Exibir informações
        st.subheader("Custom filter applied")
        st.write(f"Best lap in the session: **{melhor_volta:.3f} s**")
        st.write(f"{percentual:.1f}% filter applied: **{tempo_limite:.3f} s**")
        
        # Aplicar o filtro
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
            # By car
            chart1 = (sessao_filtrado.groupby(["Driver", "Team", "Manufacturer"])
             .agg({
              "Lap Tm (S)": "min",
              "S1 Tm": "min",
              "S2 Tm": "min",
              "S3 Tm": "min",
              "SPT": "max",
              "Avg Speed": "max"
             })
             .reset_index()
             .style.background_gradient(cmap='coolwarm')
             .format(precision=3)
             .apply(highlight_driver, subset=['Driver'])
             .apply(highlight_team, subset=['Team'])
             .apply(highlight_manufacturer, subset=['Manufacturer'])
            )
            st.subheader("Table by Car")
            st.dataframe(chart1, hide_index=True, column_config={"": None})
            # By team
            chart2 = (sessao_filtrado.groupby(["Team", "Manufacturer"])
             .agg({
              "Lap Tm (S)": "min",
              "S1 Tm": "min",
              "S2 Tm": "min",
              "S3 Tm": "min",
              "SPT": "max",
              "Avg Speed": "max"
             })
             .reset_index()
             .style.background_gradient(cmap='coolwarm')
             .format(precision=3)
             .apply(highlight_team, subset=['Team'])
             .apply(highlight_manufacturer, subset=['Manufacturer'])
            )
            st.subheader("Table by Team")
            st.dataframe(chart2, hide_index=True, column_config={"": None}) 
            # By manufacturer
            chart3 = (sessao_filtrado.groupby(["Manufacturer"])
             .agg({
              "Lap Tm (S)": "min",
              "S1 Tm": "min",
              "S2 Tm": "min",
              "S3 Tm": "min",
              "SPT": "max",
              "Avg Speed": "max"
             })
             .reset_index()
             .style.background_gradient(cmap='coolwarm')
             .format(precision=3)
             .apply(highlight_manufacturer, subset=['Manufacturer'])
            )
            st.subheader("Table by Manufacturer")
            st.dataframe(chart3, hide_index=True, column_config={"": None})

     
        elif option == 'Lines':
            #Lap Time Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['Lap Tm (S)'].rank(ascending=True) # Creates a column ranking the cars
            sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking']) # Ordering the data by the ranking
            graf2 = px.line(sessao_filtrado, x='Ranking', y='Lap Tm (S)', color='Driver', title='Lap Time Raising Average')
            st.plotly_chart(graf2)
            #S1 Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S1 Tm'].rank(ascending=True)
            sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
            graf3 = px.line(sessao_filtrado, x='Ranking', y='S1 Tm', color='Driver', title='S1 Raising Average')
            st.plotly_chart(graf3)
            #S2 Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S2 Tm'].rank(ascending=True)
            sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
            graf4 = px.line(sessao_filtrado, x='Ranking', y='S2 Tm', color='Driver', title='S2 Raising Average')
            st.plotly_chart(graf4)
            #S3 Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S3 Tm'].rank(ascending=True)
            sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
            graf5 = px.line(sessao_filtrado, x='Ranking', y='S3 Tm', color='Driver', title='S3 Raising Average')
            st.plotly_chart(graf5)
            #SPT Raising Average
            sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['SPT'].rank(ascending=False)
            sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
            graf6 = px.line(sessao_filtrado, x='Ranking', y='SPT', color='Driver', title='SPT Raising Average')
            st.plotly_chart(graf6)
        

        elif option == 'Others':
            st.subheader("Gap to Fastest")
            
            # Tabs
            tabs = st.tabs([
                "Gap to Fastest Car - Lap",
                "Gap to Fastest Car - S1",
                "Gap to Fastest Car - S2",
                "Gap to Fastest Car - S3"
            ])
            
            colunas_setores = {
                "Gap to Fastest Car - Lap": "Lap Tm (S)",
                "Gap to Fastest Car - S1": "S1 Tm",
                "Gap to Fastest Car - S2": "S2 Tm",
                "Gap to Fastest Car - S3": "S3 Tm"
            }
            
            # Dicionário de cores — agora por Driver
            cores_personalizadas = {
                "Ricardo Zonta": "red",
                "Gaetano Di Mauro": "blue",
                "Bruno Baptista": "gray",
                "Felipe Fraga": "yellow"
            }
            
            for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
                with tabs[i]:
                    # Melhor tempo por piloto
                    melhor_por_driver = sessao_filtrado.groupby("Driver")[coluna].min().reset_index()
                    min_valor = melhor_por_driver[coluna].min()
                    melhor_por_driver["Diff"] = melhor_por_driver[coluna] - min_valor
                    
                    # Ordena pelo gap
                    melhor_por_driver = melhor_por_driver.sort_values(by="Diff")
                    
                    # Adiciona cores personalizadas (ou branco se não definido)
                    melhor_por_driver["Color"] = melhor_por_driver["Driver"].map(cores_personalizadas).fillna("white")
            
                    # Barras
                    bars = alt.Chart(melhor_por_driver).mark_bar().encode(
                        x=alt.X("Driver:N", sort=melhor_por_driver["Diff"].tolist()),
                        y=alt.Y("Diff", title=f"Diff to Best {coluna} (s)"),
                        color=alt.Color("Color:N", scale=None)
                    )
            
                    # Labels acima das barras
                    labels = alt.Chart(melhor_por_driver).mark_text(
                        align="center",
                        baseline="bottom",
                        dy=-2,
                        color="white"
                    ).encode(
                        x=alt.X("Driver:N", sort=melhor_por_driver["Diff"].tolist()),
                        y="Diff",
                        text=alt.Text("Diff", format=".2f")
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
                             title=f'{var} distribution')  # Title inside graph
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

       elif option == "Sector Analysis":
           st.subheader("Sector Heatmap & Radar Comparison")
       
           # Melhor volta de cada piloto
           best_laps = sessao_filtrado.groupby("Driver")["Lap Tm (S)"].min().reset_index()
           fastest_driver = best_laps.loc[best_laps["Lap Tm (S)"].idxmin(), "Driver"]
       
           # Tempos mínimos por setor de cada piloto
           best_sectors = sessao_filtrado.groupby("Driver")[["S1 Tm", "S2 Tm", "S3 Tm"]].min().reset_index()
       
           # Diferença para o setor mais rápido
           sector_refs = {
               "S1 Tm": best_sectors["S1 Tm"].min(),
               "S2 Tm": best_sectors["S2 Tm"].min(),
               "S3 Tm": best_sectors["S3 Tm"].min(),
           }
           for col in ["S1 Tm", "S2 Tm", "S3 Tm"]:
               best_sectors[col] = best_sectors[col] - sector_refs[col]
       
           # Ordena pela melhor volta global
           best_sectors = best_sectors.merge(best_laps, on="Driver").sort_values("Lap Tm (S)").reset_index(drop=True)
       
           # ---------- Heatmap ----------
           df_heatmap = best_sectors.melt(id_vars=["Driver"], value_vars=["S1 Tm", "S2 Tm", "S3 Tm"],
                                          var_name="Sector", value_name="Gap to Best Sector")
       
           fig_heatmap = px.imshow(
               best_sectors.set_index("Driver")[["S1 Tm", "S2 Tm", "S3 Tm"]].T,
               color_continuous_scale="Turbo",
               aspect="auto",
               text_auto=".3f"
           )
           fig_heatmap.update_layout(title="Driver Times in Each Sector (Gap to Best)")
           st.plotly_chart(fig_heatmap)
       
           # ---------- Radar Chart ----------
           # Seleção de pilotos: mais rápido + nossos 4 carros
           selected_cars = [10, 11, 44, 88]
           selected_drivers = sessao[sessao["Car_ID"].isin(selected_cars)]["Driver"].unique().tolist()
           drivers_radar = list(set(selected_drivers) | {fastest_driver})
       
           radar_data = best_sectors[best_sectors["Driver"].isin(drivers_radar)]
       
           # Normalização invertida (mais rápido → mais externo)
           for col in ["S1 Tm", "S2 Tm", "S3 Tm"]:
               max_val = radar_data[col].max()
               radar_data[col] = max_val - radar_data[col]
       
           fig_radar = px.line_polar(
               radar_data,
               r=["S1 Tm", "S2 Tm", "S3 Tm"],
               theta=["Sector 1", "Sector 2", "Sector 3"],
               color="Driver",
               line_close=True
           )
           fig_radar.update_traces(fill="toself", opacity=0.6)
           fig_radar.update_layout(title="Top Drivers - Sector Performance Comparison")
           st.plotly_chart(fig_radar)

    else:
        st.warning("Please, select a session.")
else:
    st.warning("Please, select a round.")










































