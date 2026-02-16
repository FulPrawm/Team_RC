# ==============================================
# Streamlit – Complete Optimized Session Viewer
# ==============================================

import os
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ------------------ Funções utilitárias ------------------

def convert_to_seconds(x):
    """Converte tempo MM:SS.sss para segundos float"""
    if isinstance(x, str) and ":" in x:
        m, s = x.split(":")
        return float(m) * 60 + float(s)
    try:
        return float(x)
    except:
        return pd.NA

def Teams(x):
    mapping = {
        18:'Blau Motorsport', 29:'Blau Motorsport', 38:'Car Racing Sterling', 301:'Car Racing Sterling',
        21:'Ipiranga Racing', 30:'Ipiranga Racing', 12:'Amattheis Vogel', 83:'Amattheis Vogel',
        10:'RCM Motorsport',44:'RCM Motorsport', 8:'TMG Racing',19:'TMG Racing',70:'TMG Racing',
        11:'Eurofarma RC',88:'Eurofarma RC', 4:'Crown Racing',81:'Crown Racing',85:'Cavaleiro Sports',
        90:'Cavaleiro Sports',5:'FT Cavaleiro',111:'FT Cavaleiro',73:'Scuderia Bandeiras',
        51:'Scuderia Bandeiras',444:'Scuderia Bandeiras Sports',33:'Scuderia Bandeiras Sports',
        121:'Car Racing KTF',101:'Car Racing KTF',7:'FT Gazoo Racing',9:'FT Gazoo Racing',
        95:'Scuderia Chiarelli',0:'Scuderia Chiarelli',6:'A. Mattheis Motorsport',72:'FT Gazoo Racing',
        31:'RCM Motorsport'
    }
    return mapping.get(x, None)

def brand(x):
    toyota = [301,4,30,111,38,81,5,7,9,21,72]
    mitsubishi = [101,444,44,33,29,11,121,18,10,88,31]
    if x in toyota: return 'Toyota'
    if x in mitsubishi: return 'Mitsubishi'
    return 'Chevrolet'

def highlight_colors(s, colors):
    """Retorna estilo de cor para pandas.style.apply"""
    return [f"background-color: {colors[v][0]}; color: {colors[v][1]}" if v in colors else "" for v in s]

def plot_efficiency(df, title_suffix=""):
    """Gráfico de eficiência aerodinâmica (SPT vs Avg Speed)"""
    media_avg_speed = df["Avg Speed"].mean()
    media_spt = df["SPT"].mean()
    fig = px.scatter(df, x='Avg Speed', y='SPT', color='Team', symbol='Team',
                     title=f"Aerodynamic Efficiency {title_suffix}", hover_data=['Car_ID'])
    fig.update_traces(marker_size=12)
    fig.add_vline(x=media_avg_speed, line_dash="dash", line_color="white",
                  annotation_text="Average Avg Speed", annotation_position="bottom left",
                  annotation_font_color="white")
    fig.add_hline(y=media_spt, line_dash="dash", line_color="white",
                  annotation_text="Average SPT", annotation_position="top right",
                  annotation_font_color="white")
    return fig

def preprocess_session(sessao):
    """Adiciona colunas úteis, converte tempos e calcula gaps"""
    # Colunas de diferença de volta
    sessao['Last Lap Diff'] = sessao.groupby('Car_ID')['Lap Tm (S)'].diff()
    sessao['Fast Lap Diff'] = sessao['Lap Tm (S)'] - sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')

    # Crossing Seconds e Gap to Leader
    if "Crossing Time" in sessao.columns:
        sessao["Crossing Seconds"] = pd.to_timedelta(sessao["Crossing Time"]).dt.total_seconds()
        leader_times = sessao.groupby("Lap")["Crossing Seconds"].transform("min")
        sessao["Gap to Leader"] = sessao["Crossing Seconds"] - leader_times

    # Mapear equipes, marcas e pilotos
    sessao['Team'] = sessao['Car_ID'].apply(Teams)
    sessao['Manufacturer'] = sessao['Team'].map({
        "Eurofarma RC": "Mitsubishi", "Blau Motorsport": "Mitsubishi",
        "Car Racing Sterling": "Toyota", "Ipiranga Racing": "Toyota",
        "Amattheis Vogel": "Chevrolet", "RCM Motorsport": "Mitsubishi",
        "TMG Racing": "Chevrolet", "Crown Racing": "Toyota",
        "Cavaleiro Sports": "Chevrolet", "FT Cavaleiro": "Toyota",
        "Scuderia Bandeiras": "Chevrolet", "Scuderia Bandeiras Sports": "Mitsubishi",
        "Car Racing KTF": "Mitsubishi", "FT Gazoo Racing": "Toyota",
        "Scuderia Chiarelli": "Chevrolet", "A. Mattheis Motorsport": "Chevrolet"
    })
    sessao['Driver'] = sessao['Car_ID'].map({
        18:'Allam Khodair',29:'Daniel Serra',38:'Zezinho Muggiati',301:'Rafael Reis',
        21:'Thiago Camilo',30:'Cesar Ramos',12:'Lucas Foresti',83:'Gabriel Casagrande',
        10:'Ricardo Zonta',44:'Bruno Baptista',8:'Rafael Suzuki',19:'Felipe Massa',
        70:'Rafael Suzuki',11:'Gaetano Di Mauro',88:'Felipe Fraga',4:'Julio Campos',
        81:'Arthur Leist',85:'Guilherme Salas',90:'Ricardo Mauricio',5:'Denis Navarro',
        111:'Rubens Barrichello',73:'Enzo Elias',51:'Átila Abreu',444:'Vicente Orige',
        33:'Nelsinho Piquet',121:'Felipe Baptista',101:'Gianluca Petecof',
        7:'JP Oliveira',9:'Arthur Gama',95:'Lucas Kohl',0:'Cacá Bueno',
        6:'Hélio Castroneves',72:'Antonella Bassani',31:'Marcos Regadas'
    })

    # Converter setores
    for col in ["S1 Tm","S2 Tm","S3 Tm"]:
        if col in sessao.columns:
            sessao[col] = sessao[col].apply(convert_to_seconds)

    return sessao

def filter_laps(sessao, perc_filter=4):
    """Filtra pilotos e voltas com base em percentual"""
    melhor_volta = sessao["Lap Tm (S)"].min()
    tempo_limite = melhor_volta * (1 + perc_filter/100)
    voltas_por_piloto = sessao.groupby('Car_ID')['Lap'].nunique()
    min_voltas_necessarias = int(np.floor(voltas_por_piloto.max()*0.5))
    pilotos_validos = voltas_por_piloto[voltas_por_piloto >= min_voltas_necessarias].index
    sessao_filtrado = sessao[(sessao['Car_ID'].isin(pilotos_validos)) & (sessao["Lap Tm (S)"] <= tempo_limite)]
    return sessao_filtrado, melhor_volta, tempo_limite, min_voltas_necessarias

# ------------------ Função principal ------------------

def show():
    st.image('header.png')
    st.title("Session Data Report")

    # Caminhos
    BASE_DIR = Path(__file__).resolve().parent
    PASTA_ETAPAS = BASE_DIR / "Excel_Files" / "Races"
    etapas_disponiveis = [p for p in os.listdir(PASTA_ETAPAS) if os.path.isdir(os.path.join(PASTA_ETAPAS, p))]

    # Seletor de rodada e corrida
    st.subheader("Round and Session Selector")
    etapa_escolhida = st.selectbox("Choose the round:", ["Select a round..."] + sorted(etapas_disponiveis))
    if etapa_escolhida == "Select a round...": return

    pasta_etapa = os.path.join(PASTA_ETAPAS, etapa_escolhida)
    arquivos_xlsx = [f for f in os.listdir(pasta_etapa) if f.endswith(".xlsx")]
    corrida_label = st.selectbox("Choose a race:", ["Select a race..."] + sorted([os.path.splitext(f)[0] for f in arquivos_xlsx]))
    if corrida_label == "Select a race...": return

    caminho_corrida = os.path.join(pasta_etapa, [f for f in arquivos_xlsx if os.path.splitext(f)[0]==corrida_label][0])
    sessao = pd.read_excel(caminho_corrida)

    # ------------------ Pré-processamento ------------------
    sessao = preprocess_session(sessao)

    # ------------------ Filtros do usuário ------------------
    perc_filter = st.slider("Select lap time filter percentage (%)", 0.0, 20.0, 4.0, 1.0)
    sessao_filtrado, melhor_volta, tempo_limite, min_voltas_necessarias = filter_laps(sessao, perc_filter)
    st.subheader("Custom filter applied")
    st.write(f"🔍 Best lap: **{melhor_volta:.3f}s** | Filter limit: **{tempo_limite:.3f}s** | Min laps: {min_voltas_necessarias}")

    # ------------------ Gráficos ------------------
    option = st.selectbox("Select the type of graph", ("Chart", "Lines", "Histograms", "BoxPlots", "Others", "All Laps"))

    if option in ("Chart","All Laps"):
        st.write("### Average Speed vs Sector Times")
        fig = px.scatter(sessao_filtrado, x='Avg Speed', y='SPT', color='Team', symbol='Team', hover_data=['Car_ID'])
        st.plotly_chart(fig)

    if option in ("Lines","All Laps"):
        st.write("### Lap Time Progression")
        fig = px.line(sessao_filtrado, x='Lap', y='Lap Tm (S)', color='Driver', markers=True)
        st.plotly_chart(fig)

    if option in ("Histograms","All Laps"):
        st.write("### Lap Time Distribution")
        fig = px.histogram(sessao_filtrado, x='Lap Tm (S)', nbins=50, color='Team')
        st.plotly_chart(fig)

    if option in ("BoxPlots","All Laps"):
        st.write("### Boxplot per Driver")
        fig = px.box(sessao_filtrado, x='Driver', y='Lap Tm (S)', color='Team')
        st.plotly_chart(fig)

    if option in ("Others","All Laps"):
        st.write("### Aerodynamic Efficiency")
        fig = plot_efficiency(sessao_filtrado)
        st.plotly_chart(fig)

# ------------------ Rodar app ------------------
if __name__ == "__main__":
    show()
