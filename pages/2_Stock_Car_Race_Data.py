 # Importando as bibliotecas
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
# Ignoring warnings - for aesthetic purposes
import warnings
warnings.filterwarnings('ignore')


#header
st.image('header.png')
#title
st.title("Session Data Report")


# Path to where the round folders are
PASTA_ETAPAS = "Arquivos"
# List of every round (folders inside "resultados")
etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]
st.subheader("Round and Session Selector")
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
        corrida_escolhida = corrida_arquivo  # manter compatibilidade
        caminho_corrida = os.path.join(pasta_etapa, corrida_arquivo)
     
        # ✅ EVERYTHING below stays inside this box
     
        sessao = pd.read_excel(caminho_corrida)
        # Not limiting the number of rows that can be visualized
        pd.set_option('display.max_rows', None)

     
        #Creating a new column for Last Lap Difference
        sessao['Last Lap Diff'] = sessao.groupby('Car_ID')['Lap Tm (S)'].diff()
        #Calculating the fastest time for each driver
        fastest_lap_global = sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')
        #Creating a new column for the fastest lap difference
        sessao['Fast Lap Diff'] = sessao['Lap Tm (S)'] - fastest_lap_global

     
        #Creating another new column to calculate Gap to Leader
        if "Crossing Time" in sessao.columns:
          # Convert to seconds
          sessao["Crossing Seconds"] = pd.to_timedelta(sessao["Crossing Time"]).dt.total_seconds()
      
          # Calculate cumulative crossing
          sessao["Cumulative Crossing"] = sessao.groupby("Car_ID")["Crossing Seconds"].cummax()
      
          # Find winner (max laps, then lowest crossing time)
          laps_per_car = sessao.groupby("Car_ID")["Lap"].max()
          max_laps = laps_per_car.max()
          candidates = laps_per_car[laps_per_car == max_laps].index
          winner = sessao[sessao["Car_ID"].isin(candidates)].groupby("Car_ID")["Cumulative Crossing"].max().idxmin()
      
          # Calculate gap to winner
          winner_times = sessao[sessao["Car_ID"] == winner][["Lap", "Cumulative Crossing"]].rename(
              columns={"Cumulative Crossing": "Winner Crossing"}
          )
          sessao = sessao.merge(winner_times, on="Lap", how="left")
          sessao["Gap to Winner"] = sessao["Cumulative Crossing"] - sessao["Winner Crossing"]

     
        # Dictionary relating each driver with each team
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
                73: 'Scuderia Bandeiras', 51: 'Scuderia Bandeiras',
                444: 'Scuderia Bandeiras Sports', 33: 'Scuderia Bandeiras Sports',
                121: 'Car Racing KTF', 101: 'Car Racing KTF',
                7: 'FT Gazoo Racing', 9: 'FT Gazoo Racing',
                95: 'Scuderia Chiarelli', 0: 'Scuderia Chiarelli',
                6: 'A. Mattheis Motorsport'
                    }
            return Teams_dict.get(x, None)
        # Creating a new column for what team each driver races
        sessao['Team'] = sessao['Car_ID'].apply(Teams)

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

  
        # Dictionary relating each team with each manufacturer
        Team_para_Manufacturer = {
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
        sessao['Manufacturer'] = sessao['Team'].map(Team_para_Manufacturer)

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


        # Creating a list to be used on the table graphs
        analise_Team = ["Team", "Manufacturer", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_carros = ['Driver',"Manufacturer", "Team", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_Manufacturer = ['Manufacturer', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

        # Melhor volta da sessão
        melhor_volta = sessao["Lap Tm (S)"].min()        
        # Slider para o usuário escolher a porcentagem do filtro
        percentual = st.slider(
            "Select lap time filter percentage (%)",
            min_value=0.0,
            max_value=20.0,
            value=4.0,
            step=1,
        )       
        # Tempo limite baseado na % escolhida
        tempo_limite = melhor_volta * (1 + percentual / 100)  
        # Cálculo de voltas por piloto
        voltas_por_piloto = sessao.groupby('Car_ID')['Lap'].nunique()
        # Piloto com mais voltas (para referência de 50%)
        max_voltas = voltas_por_piloto.max()
        min_voltas_necessarias = int(np.floor(max_voltas * 0.5))  # Arredonda pra baixo 
        # Lista de pilotos válidos (com pelo menos 50% das voltas completadas)
        pilotos_validos = voltas_por_piloto[voltas_por_piloto >= min_voltas_necessarias].index
        # Aplicar filtro de pilotos válidos
        sessao_filtrado = sessao[sessao['Car_ID'].isin(pilotos_validos)]
        # Aplicar filtro de tempo de volta
        sessao_filtrado = sessao_filtrado[sessao_filtrado["Lap Tm (S)"] <= tempo_limite]
        # Exibir informações
        st.subheader("Custom filter applied")
        st.write(f"🔍 Best lap of the session: **{melhor_volta:.3f} s**")
        st.write(f"📏 {percentual:.1f}% filter applied: **{tempo_limite:.3f} s**")
        st.write(f"🧮 Maximum laps completed: **{max_voltas} laps**")
        st.write(f"⚠️ Only drivers with **at least {min_voltas_necessarias} laps completed** will be considered in the analysis.")

        # List of columns that SHOULD be numerics
        colunas_temporais = ["Lap Tm (S)", "S1 Tm", "S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        # Converts these columns to Float, forcing errors as NaN
        for col in colunas_temporais:
            sessao_filtrado[col] = pd.to_numeric(sessao_filtrado[col], errors='coerce')

     
        #Creating a list to select which type of graphs we want to display
        option = st.selectbox(
            "Select the type of graph",
            ("Chart", "Lines", "Histograms", "BoxPlots", "Others", "All Laps"),
            index=0  # number 0 is to open it blank
        )

     
        if option == "Chart":
            # Ordering by each car
            st.subheader("Table ordered by Car")
            tabela1 = (
                sessao_filtrado[analise_carros]
                .groupby(by=['Driver', "Team", "Manufacturer"])
                .mean(numeric_only=True)
                .reset_index()   # <-- transforma índice em colunas normais
                .style.background_gradient(cmap='coolwarm')
                .format(precision=3)
                .apply(highlight_driver, subset=['Driver'])
                .apply(highlight_team, subset=['Team'])
                .apply(highlight_manufacturer, subset=['Manufacturer'])
            )
            st.dataframe(tabela1, hide_index=True, column_config={"": None})
        
            # Ordering by each team
            st.subheader("Table ordered by Team")
            tabela2 = (
                sessao_filtrado[analise_Team]
                .groupby(by=["Team", "Manufacturer"])
                .mean(numeric_only=True)
                .reset_index()  # 🔑
                .style.background_gradient(cmap='coolwarm')
                .format(precision=3)
                .apply(highlight_team, subset=["Team"])
                .apply(highlight_manufacturer, subset=["Manufacturer"])
            )
            st.dataframe(tabela2, hide_index=True, column_config={"B": None})

            # Ordering by each manufacturer
            tabela3 = (
                sessao_filtrado[analise_Manufacturer]
                .groupby(by=["Manufacturer"])
                .mean(numeric_only=True)
                .reset_index()  # 🔑
                .style.background_gradient(cmap='coolwarm')
                .format(precision=3)
                .apply(highlight_manufacturer, subset=["Manufacturer"])
            )
            st.subheader("Table ordered by Manufacturer")
            st.dataframe(tabela3, hide_index=True, column_config={"": None})

        
        elif option == 'Lines':

            #Creating tabs for Progression
            tabs = st.tabs(["Lap Time", "Sector 1", "Sector 2", "Sector 3", "Speed Trap"])

            #Lap Progression
            with tabs[0]:
                graf1 = px.line(sessao, x="Lap", y= "Lap Tm (S)", color="Driver", title='Lap Time Progression')
                st.plotly_chart(graf1)
        
            #S1 Progression
            with tabs[1]:
                graf9 = px.line(sessao, x="Lap", y= "S1 Tm", color="Driver", title='S1 Time Progression')
                st.plotly_chart(graf9)
        
            #S2 Progression
            with tabs[2]:
                graf10 = px.line(sessao, x="Lap", y= "S2 Tm", color="Driver", title='S2 Time Progression')
                st.plotly_chart(graf10)
        
            #S3 Progression
            with tabs[3]:
                graf11 = px.line(sessao, x="Lap", y= "S3 Tm", color="Driver", title='S3 Time Progression')
                st.plotly_chart(graf11)
        
            #SPT Progression
            with tabs[4]:
                graf12 = px.line(sessao, x="Lap", y= "SPT", color="Driver", title='SPT Progression')
                st.plotly_chart(graf12)
        
            # Create tabs for Raising Average
            tabs = st.tabs(["Lap Time", "Sector 1", "Sector 2", "Sector 3", "Speed Trap"])
            
            # --- Lap Time Raising Average ---
            with tabs[0]:
                sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['Lap Tm (S)'].rank(ascending=True)
                sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
                graf2 = px.line(sessao_filtrado, x='Ranking', y='Lap Tm (S)', color='Driver', title='Lap Time Raising Average')
                st.plotly_chart(graf2)
            
            # --- Sector 1 Raising Average ---
            with tabs[1]:
                sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S1 Tm'].rank(ascending=True)
                sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
                graf3 = px.line(sessao_filtrado, x='Ranking', y='S1 Tm', color='Driver', title='Sector 1 Raising Average')
                st.plotly_chart(graf3)
            
            # --- Sector 2 Raising Average ---
            with tabs[2]:
                sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S2 Tm'].rank(ascending=True)
                sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
                graf4 = px.line(sessao_filtrado, x='Ranking', y='S2 Tm', color='Driver', title='Sector 2 Raising Average')
                st.plotly_chart(graf4)
            
            # --- Sector 3 Raising Average ---
            with tabs[3]:
                sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['S3 Tm'].rank(ascending=True)
                sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
                graf5 = px.line(sessao_filtrado, x='Ranking', y='S3 Tm', color='Driver', title='Sector 3 Raising Average')
                st.plotly_chart(graf5)
            
            # --- Speed Trap Raising Average ---
            with tabs[4]:
                sessao_filtrado['Ranking'] = sessao_filtrado.groupby('Driver')['SPT'].rank(ascending=False)
                sessao_filtrado = sessao_filtrado.sort_values(by=['Driver', 'Ranking'])
                graf6 = px.line(sessao_filtrado, x='Ranking', y='SPT', color='Driver', title='Speed Trap Raising Average')
                st.plotly_chart(graf6)

        
            #Last Lap Diff Graph
            graf7 = px.line(sessao, x="Lap", y= "Last Lap Diff", color="Driver", title='Last Lap Diff')
            st.plotly_chart(graf7)
        
            #Fast Lap Diff Graph
            graf8 = px.line(sessao, x="Lap", y= "Fast Lap Diff", color="Driver", title='Fast Lap Diff')
            st.plotly_chart(graf8)

            #Gap to Leader Graph
            if "Gap to Winner" in sessao.columns:
                graf = px.line(sessao, x="Lap", y="Gap to Winner", color="Driver", title="Gap to Winner")
                st.plotly_chart(graf)
            else:
                st.info("⚠️ 'Crossing Time' not available for this session. Gap to Winner graph will not be displayed.")


     
        elif option =='Histograms':
            for var in analise_carros:
                if var in ['Car_ID', 'Driver', 'Team', 'Manufacturer']:
                    continue #skips these columns
                fig = px.histogram(sessao_filtrado[var], nbins=25,title=f'{var} distribution')
                st.plotly_chart(fig)
        
        elif option == 'Others':
            st.subheader("Car Efficiency")

            # General filter
            sessao_eff = sessao_filtrado.copy()
        
            # Defining the average to cut the quadrants
            media_avg_speed = sessao_eff["Avg Speed"].mean()
            media_spt = sessao_eff["SPT"].mean()
        
            # Graph
            fig = px.scatter(sessao_eff, x='Avg Speed', y='SPT', color='Team', symbol='Team',
                             title="Aerodynamic Efficiency - Avg Speed vs SPT",
                             hover_data=['Car_ID'])
        
            fig.update_traces(marker_size=10)
        
            # Linhas de corte no meio dos dados
            fig.add_vline(x=media_avg_speed, line_dash="dash", line_color="white", annotation_text="Average 'Avg Speed'", 
                          annotation_position="bottom left", annotation_font_color="white")
        
            fig.add_hline(y=media_spt, line_dash="dash", line_color="white", annotation_text="Average 'SPT'",
                          annotation_position="top right", annotation_font_color="white")
        
            # Texto descritivo sobre os quadrantes
            st.markdown("""
            - **↗ Upper Right Quadrant**: High overall efficiency (straight + turn)
            - **↖ Upper Left Quadrant**: Low downforce (good straight, bad cornering)
            - **↘ Lower Right Quadrant**: High downforce (good cornering, bad straight)
            - **↙ Lower Left Quadrant**: Low efficiency (neither)
            """)
        
            st.plotly_chart(fig, use_container_width=True)
 
            # Tabs to Gap to Fastest
            tabs = st.tabs(["Gap to Fastest Car in AVG - Lap", "Gap to Fastest Car in AVG - S1", "Gap to Fastest Car in AVG - S2", "Gap to Fastest Car in AVG - S3"])
        
            colunas_setores = {
                "Gap to Fastest Car in AVG - Lap": "Lap Tm (S)",
                "Gap to Fastest Car in AVG - S1": "S1 Tm",
                "Gap to Fastest Car in AVG - S2": "S2 Tm",
                "Gap to Fastest Car in AVG - S3": "S3 Tm"
            }
        
            # Dicionário de cores dos seus carros
            cores_personalizadas = {
                "Ricardo Zonta": "red",
                "Gaetano Di Mauro": "blue",
                "Bruno Baptista": "gray",
                "Felipe Fraga": "yellow"
            }
        
            for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
                with tabs[i]:
                    media_por_car_id = sessao_filtrado.groupby('Driver')[coluna].mean().reset_index()
                    min_valor = media_por_car_id[coluna].min()
                    media_por_car_id['Diff'] = media_por_car_id[coluna] - min_valor
                    media_por_car_id = media_por_car_id.sort_values(by='Diff')
                    media_por_car_id['Color'] = media_por_car_id['Driver'].map(cores_personalizadas).fillna('white')
        
                    bars = alt.Chart(media_por_car_id).mark_bar().encode(
                        x=alt.X('Driver:N', sort=media_por_car_id['Diff'].tolist()),
                        y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
                        color=alt.Color('Color:N', scale=None)
                    )
        
                    labels = alt.Chart(media_por_car_id).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-2,
                        color='white'
                    ).encode(
                        x=alt.X('Driver:N', sort=media_por_car_id['Diff'].tolist()),
                        y='Diff',
                        text=alt.Text('Diff', format='.2f')
                    )
        
                    chart = (bars + labels).properties(title=tab_name)
        
                    st.altair_chart(chart, use_container_width=True)
        
            # Percentual difference with tendency
            st.header("Percentual difference to the best lap for each driver from this team")
        
            carros_desejados = [10, 11, 44, 88]
            nomes_carros = {
                10: "Ricardo Zonta",
                11: "Gaetano Di Mauro",
                44: "Bruno Baptista",
                88: "Felipe Fraga"
            }
        
            cores_carros = {
                10: "red",
                11: "blue",
                44: "gray",
                88: "yellow"
            }
        
            tabs_dif = st.tabs([nomes_carros[carro] for carro in carros_desejados])
        
            for i, carro in enumerate(carros_desejados):
                with tabs_dif[i]:
                    df = sessao_filtrado[sessao_filtrado['Car_ID'] == carro].copy()
        
                    if df.empty:
                        st.write("No laps avaiable for this car after the filter.")
                        continue
        
                    melhor_volta = df['Lap Tm (S)'].min()
                    volta_mais_rapida = df[df['Lap Tm (S)'] == melhor_volta]['Lap'].iloc[0]
                    df['Diff %'] = ((df['Lap Tm (S)'] - melhor_volta) / melhor_volta) * 100
        
                    # Quebra em blocos contínuos
                    df = df.sort_values('Lap')
                    df['Gap'] = df['Lap'].diff().fillna(1)
                    df['Bloco'] = (df['Gap'] > 1).cumsum()
        
                    fig = px.bar(
                        df, x="Lap", y="Diff %",
                        text=df['Diff %'].map(lambda x: f"{x:.2f}%"),
                        color_discrete_sequence=[cores_carros[carro]],
                        title=f"{nomes_carros[carro]} - Diff % by lap"
                    )
        
                    fig.update_traces(textposition='outside')
        
                    fig.add_vline(x=volta_mais_rapida, line_dash="dash", line_color="white",
                                  annotation_text="Best lap", annotation_position="top")
        
                    # Linhas de tendência por bloco
                    for bloco_id in df['Bloco'].unique():
                        bloco = df[df['Bloco'] == bloco_id]
                        if len(bloco) < 2:
                            continue
        
                        from sklearn.linear_model import LinearRegression
                        X = bloco['Lap'].values.reshape(-1, 1)
                        y = bloco['Diff %'].values
                        modelo = LinearRegression().fit(X, y)
                        y_pred = modelo.predict(X)
        
                        fig.add_trace(go.Scatter(
                            x=bloco['Lap'],
                            y=y_pred,
                            mode='lines',
                            line=dict(color='lightgray', width=2, dash='dot'),
                            opacity=0.4,
                            showlegend=False
                        ))
        
                    fig.update_layout(
                        yaxis_title="Difference to best lap (%)",
                        xaxis_title="Lap",
                        uniformtext_minsize=8,
                        uniformtext_mode='show'
                    )
        
                    st.plotly_chart(fig, use_container_width=True)
              
        elif option == 'BoxPlots':
            for var in analise_Manufacturer:
                if var == 'Manufacturer':
                    continue
                fig = px.box(sessao_filtrado, 
                             x=sessao_filtrado[var], 
                             points='all', 
                             color='Manufacturer',
                             title=f'{var} distribution')
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
            alllaps10 = sessao_filtrado[sessao_filtrado['Car_ID'] == 10]
            st.write("Ricardo Zonta")
            styled_df10 = alllaps10.style.background_gradient(
                cmap="RdYlGn_r",  # o "_r" inverte para ficar verde = baixo, vermelho = alto
                subset=alllaps10.select_dtypes(include="number").columns,
                axis=0
            )
            st.dataframe(styled_df10)
        
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



























































































