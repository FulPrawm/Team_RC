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
# Ignorando warnings - por detalhes estéticos
import warnings
warnings.filterwarnings('ignore')

#header
st.image('header.png')

#title
st.title("Session Data Report")

# Caminho base onde ficam as pastas das etapas
PASTA_ETAPAS = "Arquivos GT Race"

# Lista todas as etapas (pastas dentro de "resultados")
etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]

st.header("Seletor de Etapa e Sessão")
etapas_opcoes = ["Selecione uma etapa..."] + sorted(etapas_disponiveis)
etapa_escolhida = st.selectbox("Escolha a etapa:", etapas_opcoes)

if etapa_escolhida != "Selecione uma etapa...":
    pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)

    arquivos_xlsx = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]
    corrida_labels = [os.path.splitext(f)[0] for f in arquivos_xlsx]
    corridas_opcoes = ["Selecione uma corrida..."] + sorted(corrida_labels)

    corrida_label = st.selectbox("Escolha a corrida:", corridas_opcoes)

    if corrida_label != "Selecione uma corrida...":
        corrida_index = corrida_labels.index(corrida_label)
        corrida_arquivo = arquivos_xlsx[corrida_index]
        corrida_escolhida = corrida_arquivo  # manter compatibilidade

        caminho_corrida = os.path.join(pasta_etapa, corrida_arquivo)

        # ✅ TUDO abaixo fica dentro desse bloco
        sessao = pd.read_excel(caminho_corrida)

        # Aqui entra toda a lógica de filtragem, exibição de opções, análise etc:
        # st.radio(...) ← opção de sessão
        # filtros, gráficos, tabelas...
        # EXATAMENTE como estava no seu código anterior
        
        
        # Não limitando o número de linhas que poderão ser visualizadas
        pd.set_option('display.max_rows', None)
        
        #Creating a new column for Last Lap Difference
        sessao['Last Lap Diff'] = sessao.groupby('Car_ID')['Lap Tm (S)'].diff()
        
        #Calculating the fastest time for each driver
        fastest_lap_global = sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')
        
        #Creating a new column for the fastest lap difference
        sessao['Fast Lap Diff'] = sessao['Lap Tm (S)'] - fastest_lap_global
        
        # Criando 2 grupos para análise, separando o grupo de carros do modelo Corolla e do modelo Cruze
        carros_mercedes = [8, 3, 76]
        carros_lamborhini = [420]
        carros_ferrari = [10]
        carros_porsche = [55]
        carros_lamborghini_trofeo = [85]
        # Função que verifica se o carro está presente na lista de carros Toyota, se estiver retorna a string 'Toyota', senão retorna "Chevrolet"
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
        st.write(f"📏 Filtro de 7% aplicado: **{tempo_limite:.3f} s**")
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
            tabela1 = sessao_filtrado[analise_carros].groupby(by=["Car_ID"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.header("Tabela ordenada pelos carros")
            st.dataframe(tabela1)
        
            # Ordenando pelo tempo de volta das equipes
            tabela2 = sessao_filtrado[analise_equipe].groupby(by=["Equipe"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.header("Tabela ordenada pelas equipes")
            st.dataframe(tabela2)
        
            tabela3 = sessao_filtrado[analise_montadora].groupby(by=["Montadora"]).mean(numeric_only=True).style.background_gradient(cmap='coolwarm').format(precision=3)
            st.header("Tabela ordenada pelas montadoras")
            st.dataframe(tabela3)
         
            st.subheader("Heatmap de Tempos de Volta por Carro")
            
        
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
                    st.write(f"Baseado na média de cada carro para **{coluna}**")
        
            # Gráfico 3: Diferença percentual por volta com tendência
            st.header("Diferença percentual para a melhor volta dos pilotos da equipe")
        
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
                        st.write("Nenhuma volta disponível para este carro após o filtro.")
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
                        title=f"{nomes_carros[carro]} - Diferença % por volta"
                    )
        
                    fig.update_traces(textposition='outside')
        
                    fig.add_vline(x=volta_mais_rapida, line_dash="dash", line_color="white",
                                  annotation_text="Melhor Volta", annotation_position="top")
        
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
                        yaxis_title="Diferença para melhor volta (%)",
                        xaxis_title="Volta",
                        uniformtext_minsize=8,
                        uniformtext_mode='show'
                    )
        
                    st.plotly_chart(fig, use_container_width=True)
            with st.expander("Comparação entre voltas IN e OUT de pit"):
             
           st.subheader("Comparação dos tempos em voltas de entrada (IN) e saída (OUT) de pit")
       
           # Identificação com base nos setores ausentes
           df_pit = sessao_filtrado.copy()
           df_pit['Pit_IN'] = df_pit['S3 Tm'].isna()
           df_pit['Pit_OUT'] = df_pit['S1 Tm'].isna()
       
           # Filtragem
           df_in = df_pit[df_pit['Pit_IN']].copy()
           df_in['Tipo'] = 'Entrada (IN)'
       
           df_out = df_pit[df_pit['Pit_OUT']].copy()
           df_out['Tipo'] = 'Saída (OUT)'
       
           # Junta os dois
           df_comparacao = pd.concat([df_in, df_out])
           df_comparacao["Car_ID"] = df_comparacao["Car_ID"].astype(str)
       
           if df_comparacao.empty:
               st.write("Nenhuma volta de entrada ou saída de pit encontrada.")
           else:
               fig = px.bar(
                   df_comparacao,
                   x="Car_ID",
                   y="Lap Tm (S)",
                   color="Tipo",
                   barmode="group",
                   text=df_comparacao["Lap Tm (S)"].round(3),
                   color_discrete_map={"Entrada (IN)": "orange", "Saída (OUT)": "lightblue"},
                   title="Tempo de volta nas voltas de entrada e saída de pit"
               )
               fig.update_traces(textposition="outside")
               fig.update_layout(
                   xaxis_title="Carro",
                   yaxis_title="Tempo de volta (s)",
                   legend_title="Tipo de volta",
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
        st.warning("Por favor, selecione uma corrida.")
else:
    st.warning("Por favor, selecione uma etapa.")


