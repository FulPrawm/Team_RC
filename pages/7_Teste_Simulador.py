import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ----------------------------
# CARREGANDO DADOS
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
df = pd.read_excel(BASE_DIR / "ET12_R2.xlsx")

# Converter Crossing Time para timedelta/segundos
df["Crossing Time"] = pd.to_timedelta(df["Crossing Time"])
df["Crossing Time (s)"] = df["Crossing Time"].dt.total_seconds()

# ----------------------------
# CONFIGURAÇÃO DO CÍRCULO (Pista)
# ----------------------------
CIRCLE_RADIUS = 1
SECTORS = ["S1", "S2", "S3"]
SECTOR_COLORS = ["lightblue", "lightgreen", "lightcoral"]

def get_circle_position(progress):
    """
    progress: 0 a 1 -> posição do carro na volta
    retorna x, y no círculo unitário
    """
    angle = 2 * np.pi * progress
    x = CIRCLE_RADIUS * np.cos(angle)
    y = CIRCLE_RADIUS * np.sin(angle)
    return x, y

def get_sector(progress):
    """
    Retorna o setor atual baseado no progresso da volta
    """
    sector_index = int(progress * len(SECTORS)) % len(SECTORS)
    return SECTORS[sector_index]

# ----------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------
def show():
    st.title("🏁 Race Replay - Círculo Setorizado")

    race_time = st.slider(
        "Tempo de Corrida (s)",
        0.0,
        float(df["Crossing Time (s)"].max()),
        step=0.5
    )

    fig = go.Figure()

    # 🔹 DESENHAR SETORES DO CÍRCULO
    for i, color in enumerate(SECTOR_COLORS):
        theta = np.linspace(2*np.pi*i/len(SECTORS), 2*np.pi*(i+1)/len(SECTORS), 100)
        x = CIRCLE_RADIUS * np.cos(theta)
        y = CIRCLE_RADIUS * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=np.append(x, 0),
            y=np.append(y, 0),
            fill="toself",
            fillcolor=color,
            line=dict(color="black"),
            mode="lines",
            showlegend=False,
            hoverinfo="skip"
        ))

    # 🔹 POSIÇÃO DOS CARROS
    colors = px.colors.qualitative.Dark24
    car_list = df["Car_ID"].unique()
    
    for i, car in enumerate(car_list):
        car_data = df[df["Car_ID"] == car].sort_values("Crossing Time (s)")
        
        # Pega a última volta que já começou
        lap_row = car_data[car_data["Crossing Time (s)"] <= race_time].tail(1)

        if not lap_row.empty:
            lap_time = lap_row["Lap Tm (S)"].values[0]
            crossing = lap_row["Crossing Time (s)"].values[0]
            lap_start = crossing - lap_time

            # Progresso na volta
            time_in_lap = race_time - lap_start
            progress = np.clip(time_in_lap / lap_time, 0, 1)

            x, y = get_circle_position(progress)
            sector = get_sector(progress)

            fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[f"{car}\n{sector}"],
                textposition="top center",
                marker=dict(size=14, color=colors[i % len(colors)]),
                showlegend=False
            ))

    # 🔹 LAYOUT
    fig.update_xaxes(range=[-1.2, 1.2], visible=False, scaleanchor="y")
    fig.update_yaxes(range=[-1.2, 1.2], visible=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)

show()
