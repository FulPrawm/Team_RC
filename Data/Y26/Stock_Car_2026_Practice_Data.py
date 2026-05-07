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
from pathlib import Path
def show():
    # Ignoring warnings for aesthetic purposes
    import warnings
    warnings.filterwarnings('ignore')


    #header
    st.image('header.png')
    #title
    st.title("Fastest Time Session Data Report")


    # Path to where the folders of the rounds are
    BASE_DIR = Path(__file__).resolve().parent
    PASTA_ETAPAS = BASE_DIR / "Excel_Files" / "Practice_And_Qualy"
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
            carros_toyota = [6, 10, 21, 27, 30, 73, 80, 81, 95, 97, 293, 301, 25]
            carros_mitsubishi = [1, 7, 11, 18, 24, 29, 38, 51, 111, 121, 444]
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
                    27: 'A. Mattheis TMG', 73: 'A. Mattheis TMG',
                    12: 'A. Mattheis Vogel', 83: 'A. Mattheis Vogel',
                    18: 'Blau Motorsport', 29: 'Blau Motorsport',
                    293: 'Car Racing', 301: 'Car Racing',
                    85: 'Cavaleiro Sports', 90: 'Cavaleiro Sports',
                    81: 'Crown Racing', 95: 'Crown Racing',
                    1: 'Eurofarma RC', 11: 'Eurofarma RC',
                    10: 'Full Time GR', 80: 'Full Time GR',
                    21: 'Mercado Livre Racing', 30: 'Mercado Livre Racing',
                    97: 'RTR Racing Team', 25: 'RTR Racing Team',
                    8: 'Scuderia Bandeiras', 33: 'Scuderia Bandeiras',
                    51: 'Scuderia Bandeiras Sports', 111: 'Scuderia Bandeiras Sports',
                    0: 'Scudeira Chiarelli', 22: 'Scuderia Chiarelli',
                    121: 'Sterling Racing', 444: 'Sterling Racing',
                    7: 'Team RC', 38: 'Team RC',
                    4: 'TMG Racing', 19: 'TMG Racing',
                    6: 'Mercado Livre Racing Team', 24: 'Albatroz Racing' 
                }
                return Teams_dict.get(x, None)
            # Creating a new column called "Team" and applying the function "Teams"
            sessao['Team'] = sessao['Car_ID'].apply(Teams)

            # Dictionary relating each team with each manufacturer
            team_to_manufacturer = {
            "A. Mattheis TMG": "Toyota", "Car Racing": "Toyota", "Crown Racing": "Toyota", "Full Time GR": "Toyota",
            "Mercado Livre Racing": "Toyota", "Mercado Livre Racing Team": "Toyota", "RTR Racing Team": "Toyota",
            "A. Mattheis Vogel": "Chevrolet", "Cavaleiro Sports": "Chevrolet", "Scuderia Bandeiras": "Chevrolet",
            "Scuderia Chiarelli": "Chevrolet", "TMG Racing": "Chevrolet",
            "Blau Motorsport": "Mitsubishi", "Eurofarma RC": "Mitsubishi", "Albatroz Racing": "Mitsubishi",
            "Scuderia Bandeiras Sports": "Mitsubishi", "Sterling Racing": "Mitsubishi", "Team RC": "Mitsubishi"
            } 
            # Creating a new column for what Manufacturer each team races
            sessao['Manufacturer'] = sessao['Team'].map(team_to_manufacturer)
        
            #Last Dictionary relating each car to their drivers
            drivers_dict = {
            0: 'Cacá Bueno', 1: 'Felipe Fraga',
            4: 'Julio Campos', 6: 'Hélio Castroneves',
            7: 'Sérgio Sette Câmara', 8: 'Rafael Suzuki',
            10: 'Ricardo Zonta', 11: 'Gaetano Di Mauro',
            12: 'Lucas Foresti', 18: 'Allam Khodair',
            19: 'Felipe Massa', 21: 'Thiago Camilo',
            22: 'André Moraes',  24: 'Pipe Bartz',
            27: 'Renan Guerra', 29: 'Daniel Serra',
            30: 'Cesar Ramos', 33: 'Nelson Piquet Jr', 
            38: 'Zezinho Muggiati', 51: 'Átila Abreu', 
            73: 'Enzo Elias', 80: 'Alfredinho Ibiapina',
            81: 'Arthur Leist', 83: 'Gabriel Casagrande', 
            85: 'Guilherme Salas', 90: 'Ricardo Mauricio', 
            95: 'Lucas Kohl', 97: 'Bruna Tomaselli', 
            111: 'Rubens Barrichello', 121: 'Felipe Baptista',
            293: 'Léo Reis', 301: 'Rafa Reis', 
            444: 'Vicente Orige', 25: 'Tatiana Calderón'
            }
            sessao['Driver'] = sessao['Car_ID'].map(drivers_dict)


            # Personalized colors with text contrast
            colors_driver = {
                "Gaetano Di Mauro": ("lightblue", "black"),
                "Sérgio Sette Câmara": ("gray", "white"),
                "Felipe Fraga": ("yellow", "black"),
                "Zezinho Muggiati": ("#0057B8", "white")
            }
            colors_team = {
                "Eurofarma RC": ("yellow", "black"),
                "Team RC": ("gray", "white")
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
                    "Gaetano Di Mauro": "blue",
                    "Sérgio Sette Câmara": "gray",
                    "Felipe Fraga": "yellow",
                    "Zezinho Muggiati": "#0057B8"
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
                df_heatmap = best_sectors.melt(
                    id_vars=["Driver"], 
                    value_vars=["S1 Tm", "S2 Tm", "S3 Tm"],
                    var_name="Sector", 
                    value_name="Gap to Best Sector"
                )
                
                fig_heatmap = px.imshow(
                    best_sectors.set_index("Driver")[["S1 Tm", "S2 Tm", "S3 Tm"]],
                    color_continuous_scale="Turbo",
                    aspect="auto",
                    text_auto=".3f"
                )
                fig_heatmap.update_layout(
                    title="Driver Times in Each Sector (Gap to Best)",
                    xaxis_title="Sector",
                    yaxis_title="Driver"
                )
                st.plotly_chart(fig_heatmap)
                
                # ---------- Radar Chart with Absolute Times Normalized ----------
                selected_cars = [1, 7, 11, 38]
                selected_drivers = sessao[sessao["Car_ID"].isin(selected_cars)]["Driver"].unique().tolist()
                drivers_radar = list(set(selected_drivers) | {fastest_driver})
                
                radar_data = best_sectors[best_sectors["Driver"].isin(drivers_radar)].copy()
                
                # Normalização por setor (0 = mais lento, 1 = mais rápido)
                normalized = pd.DataFrame()
                normalized["Driver"] = radar_data["Driver"]
                
                for col in ["S1 Tm", "S2 Tm", "S3 Tm"]:
                    min_val = radar_data[col].min()
                    max_val = radar_data[col].max()
                    normalized[col] = (max_val - radar_data[col]) / (max_val - min_val)
                
                # Melt para plotly
                df_radar = normalized.melt(
                    id_vars=["Driver"],
                    value_vars=["S1 Tm", "S2 Tm", "S3 Tm"],
                    var_name="Sector",
                    value_name="Score"
                )
                
                # Criar dicionário de cores
                driver_colors = {11: "blue", 7: "gray", 1: "yellow", 38:"#0057B8"}
                color_map = {}
                
                for driver in df_radar["Driver"].unique():
                    car_id = sessao.loc[sessao["Driver"] == driver, "Car_ID"].iloc[0]
                    if car_id in driver_colors:
                        color_map[driver] = driver_colors[car_id]
                    else:
                        color_map[driver] = "green"  # fastest outsider
                
                # Plot
                fig_radar = px.line_polar(
                    df_radar,
                    r="Score",
                    theta="Sector",
                    color="Driver",
                    line_close=True,
                    color_discrete_map=color_map
                )
                fig_radar.update_traces(fill="toself", opacity=0.6)
                
                # Custom ticks no eixo radial
                fig_radar.update_layout(
                    title="Top Drivers - Sector Performance Comparison",
                    polar=dict(
                        radialaxis=dict(
                            tickmode='array',
                            tickvals=[0, 0.5, 1],
                            ticktext=['Slow', 'Average', 'Fast'],
                            tickfont=dict(color="grey")  # <<< deixa o texto preto
                        )
                    )
                )
                
                st.plotly_chart(fig_radar)

                st.subheader("Fast Lap vs Previous Lap")

                # --- Fastest lap for each driver (unfiltered) ---
                fastest_idx = sessao.groupby("Driver")["Lap Tm (S)"].idxmin()
                fastest_laps = sessao.loc[fastest_idx, ["Driver", "Lap", "Lap Tm (S)"]]

                # --- Previous lap ---
                prev_laps = []
                for _, row in fastest_laps.iterrows():
                    driver = row["Driver"]
                    lap = row["Lap"]

                    prev_lap = sessao[
                        (sessao["Driver"] == driver) &
                        (sessao["Lap"] == lap - 1)
                    ]

                    if not prev_lap.empty:
                        prev_time = prev_lap["Lap Tm (S)"].values[0]

                        prev_laps.append({
                            "Driver": driver,
                            "Fast Lap": row["Lap Tm (S)"],
                            "Previous Lap": prev_time
                        })

                scatter_df = pd.DataFrame(prev_laps)

                # --- Scatter Plot ---
                fig_scatter = px.scatter(
                    scatter_df,
                    x="Fast Lap",
                    y="Previous Lap",
                    color="Driver",
                    title="Fastest Lap vs Previous Lap"
                )

                fig_scatter.update_traces(marker_size=12)
                st.plotly_chart(fig_scatter, use_container_width=True)

            
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
                
                # Block 2 — por Car_ID (como rótulo) em tabs
                tabs_box = st.tabs(["Lap", "S1", "S2", "S3", "SPT"])
                colunas_boxplot = {
                    "Lap": "Lap Tm (S)",
                    "S1": "S1 Tm",
                    "S2": "S2 Tm",
                    "S3": "S3 Tm",
                    "SPT": "SPT"
                }
                for i, (tab_nome, coluna) in enumerate(colunas_boxplot.items()):
                    with tabs_box[i]:
                        df_plot = sessao_filtrado.copy()
                        
                        # Pega lista de drivers em ordem alfabética
                        drivers_unicos = sorted(df_plot["Driver"].unique())
                
                        fig = px.box(
                            df_plot,
                            x="Driver",
                            y=coluna,
                            points="all",
                            color="Driver",
                            category_orders={"Driver": drivers_unicos},
                        )
                
                        fig.update_layout(
                            yaxis_title=coluna,
                            title=f"Boxplot - {coluna}",
                            showlegend=False
                        )
                
                        st.plotly_chart(fig, use_container_width=True)
            
            
            elif option == 'All Laps':
            
                alllaps11 = sessao[sessao['Car_ID'] == 11]
                st.write("Gaetano Di Mauro")
                st.dataframe(alllaps11)
            
                alllaps44 = sessao[sessao['Car_ID'] == 7]
                st.write("Sérgio Sette Câmara")
                st.dataframe(alllaps44)
            
                alllaps88 = sessao[sessao['Car_ID'] == 1]
                st.write("Felipe Fraga")
                st.dataframe(alllaps88)

                alllaps38 = sessao[sessao['Car_ID'] == 38]
                st.write("Zezinho Mugiatti")
                st.dataframe(alllaps38)

        else:
            st.warning("Please, select a session.")
    else:
        st.warning("Please, select a round.")