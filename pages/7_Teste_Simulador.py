import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.write("Página carregada")
st.write(df.head())

IMG_WIDTH = 1076
IMG_HEIGHT = 694

theta = np.linspace(0, 2*np.pi, 2000)
track_x = 538 + 400*np.cos(theta) + 60*np.cos(3*theta)
track_y = 347 + 250*np.sin(theta)

def get_position(progress):
    index = int(progress * (len(track_x)-1))
    return track_x[index], track_y[index]

def show():

    st.title("🏁 Race Replay")

    df = pd.read_excel("ET12_R2.xlsx")

    race_time = st.slider(
        "Tempo de Corrida (s)",
        0.0,
        float(df["Crossing Time"].max()),
        step=0.5
    )

    fig = go.Figure()

    # 🔹 IMAGEM DA PISTA
    fig.add_layout_image(
        dict(
            source="assets/pista.png",  # coloque sua imagem aqui
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

    for car in df["Car_ID"].unique():

        car_data = df[df["Car_ID"] == car]

        lap_row = car_data[car_data["Crossing Time"] >= race_time].head(1)

        if not lap_row.empty:

            lap_time = lap_row["Lap Tm (S)"].values[0]
            crossing = lap_row["Crossing Time"].values[0]
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
                    marker=dict(size=14),
                    showlegend=False
                )
            )

    fig.update_xaxes(range=[0, IMG_WIDTH], visible=False)
    fig.update_yaxes(range=[0, IMG_HEIGHT], visible=False, scaleanchor="x")

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)
