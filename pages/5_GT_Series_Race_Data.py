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
PASTA_ETAPAS = "Arquivos GT Race"
# List of every round (folders inside "resultados")
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

     
        # Dictionary relating each driver with each team
        def equipes(x):
            equipes_dict = {
                8: 'RC', 3: 'KTF',
                76: 'GForce', 420: 'GRID',
                10: 'GForce', 55: 'Stuttgart Motorsport',
                85: 'GForce', 34: 'RC'
            }
            return equipes_dict.get(x, None)
        # Creating a new column for what team each driver races
        sessao['Equipe'] = sessao['Car_ID'].apply(equipes)

     
        # Dictionary relating each team with each manufacturer
        equipe_para_montadora = {
            "RC": "Mercedes",
            "KTF": "Mercedes",
            "GForce": "Ferrari",
            "Stuttgart Motorsport": "Porsche",
            "GRID": "Lamborghini"
        } 
        # Creating a new column for what Manufacturer each team races
        sessao['Montadora'] = sessao['Equipe'].map(equipe_para_montadora)

     
        # Dicionários de cores
        cores_carros = {8: 'red', 34: 'yellow', 27: 'gray'}
        cores_equipes = {'RC': 'gray'}
        cores_montadoras = {'Mercedes': 'gray'}
        # Funções de coloração
        def colorir_carro(val):
            if val in cores_carros:
                return f'background-color: {cores_carros[val]}'
            return ''
        def colorir_equipe(val):
            if val in cores_equipes:
                return f'background-color: {cores_equipes[val]}'
            return ''
        def colorir_montadora(val):
            if val in cores_montadoras:
                return f'background-color: {cores_montadoras[val]}'
            return ''

     
        # Creating a list to be used on the table graphs
        analise_equipe = ["Equipe", "Montadora", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_carros = ['Car_ID',"Montadora", "Equipe", "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]
        analise_montadora = ['Montadora', "Lap Tm (S)", "S1 Tm","S2 Tm", "S3 Tm", "SPT", "Avg Speed"]

     
        # Auto filter based on 4% of the fastest lap of the session
        melhor_volta = sessao["Lap Tm (S)"].min()
        tempo_limite = melhor_volta * 1.04
        # Equation for how many laps each driver made
        voltas_por_piloto = sessao.groupby('Car_ID')['Lap'].nunique()
        # Driver with most laps (winner)
        max_voltas = voltas_por_piloto.max()
        min_voltas_necessarias = int(np.floor(max_voltas * 0.5))  # Rounds to lowest
        # List of driver with at least 50% of the laps completed
        pilotos_validos = voltas_por_piloto[voltas_por_piloto >= min_voltas_necessarias].index
        # Aplying filter to only valid drivers
        sessao_filtrado = sessao[sessao['Car_ID'].isin(pilotos_validos)]  
        # Aplying lap time filter (4% of fastest time)
        sessao_filtrado = sessao_filtrado[sessao_filtrado["Lap Tm (S)"] <= tempo_limite]

     
        # Exhibiting information of the data filters
        st.subheader("Auto filter applied")
        st.write(f"🔍 Best lap of the session: **{melhor_volta:.3f} s**")
        st.write(f"📏 4% filter applied: **{tempo_limite:.3f} s**")
        st.write(f"🧮 Máximum laps completed: **{max_voltas} laps**")
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
                .groupby(by=["Car_ID", "Montadora", "Equipe"])
                .mean(numeric_only=True)
                .style.background_gradient(cmap='coolwarm')
                .format(precision=3)
            )
            st.dataframe(tabela1)
        
            # Ordering by each team
            st.subheader("Table ordered by Team")
            tabela2 = (
                sessao_filtrado[analise_equipe]
                .groupby(by=["Equipe", "Montadora"])
                .mean(numeric_only=True)
                .style.background_gradient(cmap='coolwarm')
                .format(precision=3)
            )
            st.dataframe(tabela2)

            # Ordering by each manufacturer
            tabela3 = sessao_filtrado[analise_montadora].groupby(by=["Montadora"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.subheader("Table ordered by Manufacturer")
            st.dataframe(tabela3)

        
        elif option == 'Lines':
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
        
        elif option =='Histograms':
            for var in analise_carros:
                if var == 'Car_ID':
                    continue #skips the column "Car_ID"
                fig = px.histogram(sessao_filtrado[var], nbins=25,title=f'Distribuição de {var}')
                st.plotly_chart(fig)
        
        elif option == 'Others':
         
            # Tabs para Gap to Fastest
            tabs = st.tabs(["Gap to Fastest Car - Lap", "Gap to Fastest Car - S1", "Gap to Fastest Car - S2", "Gap to Fastest Car - S3"])
        
            colunas_setores = {
                "Gap to Fastest Car - Lap": "Lap Tm (S)",
                "Gap to Fastest Car - S1": "S1 Tm",
                "Gap to Fastest Car - S2": "S2 Tm",
                "Gap to Fastest Car - S3": "S3 Tm"
            }
        
            # Dicionário de cores dos seus carros
            cores_personalizadas = {
                8: 'red',
                34: 'yellow',
                27: 'gray',
            }
        
            for i, (tab_name, coluna) in enumerate(colunas_setores.items()):
                with tabs[i]:
                    media_por_car_id = sessao_filtrado.groupby('Car_ID')[coluna].mean().reset_index()
                    min_valor = media_por_car_id[coluna].min()
                    media_por_car_id['Diff'] = media_por_car_id[coluna] - min_valor
                    media_por_car_id = media_por_car_id.sort_values(by='Diff')
                    media_por_car_id['Car_ID_str'] = media_por_car_id['Car_ID'].astype(str)
                    media_por_car_id['Color'] = media_por_car_id['Car_ID'].map(cores_personalizadas).fillna('white')
        
                    bars = alt.Chart(media_por_car_id).mark_bar().encode(
                        x=alt.X('Car_ID_str:N', sort=media_por_car_id['Diff'].tolist()),
                        y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
                        color=alt.Color('Color:N', scale=None)
                    )
        
                    labels = alt.Chart(media_por_car_id).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-2,
                        color='white'
                    ).encode(
                        x=alt.X('Car_ID_str:N', sort=media_por_car_id['Diff'].tolist()),
                        y='Diff',
                        text=alt.Text('Diff', format='.2f')
                    )
        
                    chart = (bars + labels).properties(title=tab_name)
        
                    st.altair_chart(chart, use_container_width=True)
        
            # Gráfico 3: Diferença percentual por volta com tendência
            st.header("Percentual difference to the best lap for each driver from this team")
        
            carros_desejados = [8, 27, 34]
            nomes_carros = {
                8: "Guilherme Figueiroa",
                27: "Ricardo Baptista",
                34: "Maurizio Billi"
            }
        
            cores_carros = {
                8: "red",
                34: "yellow",
                27: "gray"
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

                 # Bloco 2 — por Car_ID (como rótulo) em tabs
            tabs_box = st.tabs(["Volta", "S1", "S2", "S3", "SPT"])
            colunas_boxplot = {
                "Volta": "Lap Tm (S)",
                "S1": "S1 Tm",
                "S2": "S2 Tm",
                "S3": "S3 Tm",
                "SPT": "SPT"
            }
        
            cores_carros = {
                "Carro 8": "red",
                "Carro 27": "gray",
                "Carro 34": "yellow"
            }
        
            for i, (tab_nome, coluna) in enumerate(colunas_boxplot.items()):
                with tabs_box[i]:
                    df_plot = sessao_filtrado.copy()
                    df_plot["Car_ID"] = df_plot["Car_ID"].astype(str)
                    df_plot["Car_Label"] = "Carro " + df_plot["Car_ID"]
        
                    carros_unicos = sorted(df_plot["Car_Label"].unique())
        
                    fig = px.box(
                        df_plot,
                        x="Car_Label",
                        y=coluna,
                        points="all",
                        color="Car_Label",
                        category_orders={"Car_Label": carros_unicos},
                        color_discrete_map={**cores_carros}  # outras cores default serão automáticas
                    )
        
                    fig.update_layout(
                        xaxis_title="Carro",
                        yaxis_title=coluna,
                        title=f"Boxplot - {coluna}",
                        showlegend=False
                    )
        
                    st.plotly_chart(fig, use_container_width=True)
        
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


    else:
        st.warning("Please, select a race.")
else:
    st.warning("Please, select a round.")



































