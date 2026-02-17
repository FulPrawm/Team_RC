import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import plotly.express as px

# ----------------------------
# CONFIGURAÇÃO DE ARQUIVOS
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
df = pd.read_excel(BASE_DIR / "ET12_R2.xlsx")
IMG_PATH = BASE_DIR.parent / "assets" / "pista.png"

# Converter tempo para segundos
df["Crossing Time"] = pd.to_timedelta(df["Crossing Time"])
df["Crossing Time (s)"] = df["Crossing Time"].dt.total_seconds()

# ----------------------------
# DIMENSÕES DA PISTA
# ----------------------------
IMG_WIDTH = 1076
IMG_HEIGHT = 694

# Criação da pista fictícia (substitua por coords reais se tiver)
theta = np.linspace(0, 2*np.pi, 2000)
track_x = 538 + 400*np.cos(theta) + 60*np.cos(3*theta)
track_y = 347 + 250*np.sin(theta)

def get_position(progress):
    """Retorna coordenadas (x,y) da pista para um dado progresso da volta."""
    index = int(progress * (len(track_x)-1))
    return track_x[index], track_y[index]

# ----------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------
def show():
    st.title("🏁 Race Replay")

    race_time = st.slider(
        "Tempo de Corrida (s)",
        0.0,
        float(df["Crossing Time (s)"].max()),
        step=0.5
    )

    fig = go.Figure()

    # 🔹 IMAGEM DA PISTA
    fig.add_layout_image(
        dict(
            source=str(IMG_PATH),
            xref="x",
            yref="y",
            x=0,
            y=IMG_HEIGHT,
            sizex=IMG_WIDTH,
            sizey=IMG_HEIGHT,
            sizing="stretch",
            layer="below"
        )
    )

    # 🔹 POSIÇÃO DOS CARROS
    colors = px.colors.qualitative.Dark24  # 24 cores diferentes
    car_list = df["Car_ID"].unique()
    
    for i, car in enumerate(car_list):
        car_data = df[df["Car_ID"] == car].sort_values("Crossing Time (s)")
        
        # Pega última volta concluída antes do tempo selecionado
        lap_row = car_data[car_data["Crossing Time (s)"] <= race_time].tail(1)

        if not lap_row.empty:
            lap_time = lap_row["Lap Tm (S)"].values[0]
            crossing = lap_row["Crossing Time (s)"].values[0]
            lap_start = crossing - lap_time

            time_in_lap = race_time - lap_start
            progress = np.clip(time_in_lap / lap_time, 0, 1)

            x, y = get_position(progress)

            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers+text",
                    text=[str(car)],
                    textposition="top center",
                    marker=dict(size=14, color=colors[i % len(colors)]),
                    showlegend=False
                )
            )

    # 🔹 LAYOUT DO GRÁFICO
    fig.update_xaxes(range=[0, IMG_WIDTH], visible=False)
    fig.update_yaxes(range=[0, IMG_HEIGHT], visible=False, scaleanchor="x", autorange="reversed")

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# EXECUÇÃO
# ----------------------------
show()
