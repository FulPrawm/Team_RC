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

# Converter Crossing Time para datetime
df["Crossing Time DT"] = pd.to_datetime(df["Crossing Time"], format="%H:%M:%S.%f")
start_time = df["Crossing Time DT"].min()
df["Crossing Time (s)"] = (df["Crossing Time DT"] - start_time).dt.total_seconds()

# ----------------------------
# CONFIGURAÇÃO DO CÍRCULO
# ----------------------------
CIRCLE_RADIUS = 1
SECTORS = ["S1", "S2", "S3"]
SECTOR_COLORS = ["lightblue", "lightgreen", "lightcoral"]

def get_circle_position(progress):
    angle = 2 * np.pi * progress
    x = CIRCLE_RADIUS * np.cos(angle)
    y = CIRCLE_RADIUS * np.sin(angle)
    return x, y

def get_sector(progress):
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

        # Primeira volta cujo crossing ainda não aconteceu
        lap_row = car_data[car_data["Crossing Time (s)"] >= race_time].head(1)

        if lap_row.empty:
            # Se já terminou todas as voltas, pega a última
            lap_row = car_data.tail(1)

        lap_time = lap_row["Lap Tm (S)"].values[0]
        crossing = lap_row["Crossing Time (s)"].values[0]
        lap_start = crossing - lap_time

        # progresso dentro da volta atual
        time_in_lap = np.clip(race_time - lap_start, 0, lap_time)
        progress = time_in_lap / lap_time

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
