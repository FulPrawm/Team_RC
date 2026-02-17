import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import time

# ----------------------------
# LOAD DATA
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
df = pd.read_excel(BASE_DIR / "ET12_R2.xlsx")

df["CrossingTimeDT"] = pd.to_datetime(df["Crossing Time"], format="%H:%M:%S.%f")
start_time = df["CrossingTimeDT"].min()
df["CrossingTime_s"] = (df["CrossingTimeDT"] - start_time).dt.total_seconds()

# ----------------------------
# CIRCLE CONFIG
# ----------------------------
CIRCLE_RADIUS = 1
SECTORS = ["S1", "S2", "S3"]
SECTOR_COLORS = ["lightblue", "lightgreen", "lightcoral"]

def get_circle_position(progress):
    angle = 2*np.pi*progress
    x = CIRCLE_RADIUS*np.cos(angle)
    y = CIRCLE_RADIUS*np.sin(angle)
    return x, y

def get_sector(progress):
    index = int(progress * len(SECTORS)) % len(SECTORS)
    return SECTORS[index]

# ----------------------------
# SESSION STATE INIT
# ----------------------------
if "race_time" not in st.session_state:
    st.session_state.race_time = 0.0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "speed" not in st.session_state:
    st.session_state.speed = 1.0

st.title("🏁 Race Replay - Autoplay with Controls")

max_time = float(df["CrossingTime_s"].max())
placeholder = st.empty()

# Controls
col1, col2, col3, col4 = st.columns([1,1,1,2])
with col1:
    if st.button("▶️ Play"):
        st.session_state.playing = True
with col2:
    if st.button("⏸ Pause"):
        st.session_state.playing = False
with col3:
    if st.button("🔄 Reset"):
        st.session_state.race_time = 0.0
        st.session_state.playing = False
with col4:
    st.session_state.speed = st.selectbox("Speed", [1,2,5,10], index=0, format_func=lambda x:f"{x}x")

# Manual slider
st.session_state.race_time = st.slider("Race Time (s)", 0.0, max_time, st.session_state.race_time, step=0.1)

# ----------------------------
# FUNCTION TO CREATE FIGURE
# ----------------------------
def create_figure(race_time):
    fig = go.Figure()
    fig.update_layout(plot_bgcolor="black", paper_bgcolor="black",
                      margin=dict(l=0,r=0,t=0,b=0),
                      xaxis=dict(range=[-1.2,1.2], visible=False, scaleanchor="y"),
                      yaxis=dict(range=[-1.2,1.2], visible=False))
    
    # Draw sectors
    for i, color in enumerate(SECTOR_COLORS):
        theta = np.linspace(2*np.pi*i/len(SECTORS), 2*np.pi*(i+1)/len(SECTORS), 100)
        x = CIRCLE_RADIUS*np.cos(theta)
        y = CIRCLE_RADIUS*np.sin(theta)
        fig.add_trace(go.Scatter(
            x=np.append(x,0), y=np.append(y,0),
            fill="toself", fillcolor=color,
            line=dict(color="white"), mode="lines",
            showlegend=False, hoverinfo="skip"
        ))
    
    # Add cars
    car_list = df["Car_ID"].unique()
    colors = px.colors.qualitative.Dark24
    for i, car in enumerate(car_list):
        car_data = df[df["Car_ID"]==car].sort_values("CrossingTime_s")
        lap_row = car_data[car_data["CrossingTime_s"]>=race_time].head(1)
        if lap_row.empty:
            lap_row = car_data.tail(1)
        lap_time = lap_row["Lap Tm (S)"].values[0]
        crossing = lap_row["CrossingTime_s"].values[0]
        lap_start = crossing - lap_time
        time_in_lap = np.clip(race_time - lap_start,0,lap_time)
        progress = time_in_lap / lap_time
        x, y = get_circle_position(progress)
        sector = get_sector(progress)
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            text=[f"{car}\n{sector}"],
            textposition="top center",
            marker=dict(size=14,color=colors[i%len(colors)]),
            showlegend=False
        ))
    return fig

# ----------------------------
# AUTOPLAY LOOP
# ----------------------------
update_rate = 0.2  # 5 FPS, mais suave
if st.session_state.playing:
    while st.session_state.race_time <= max_time:
        fig = create_figure(st.session_state.race_time)
        placeholder.plotly_chart(fig, use_container_width=True)
        st.session_state.race_time += update_rate * st.session_state.speed
        time.sleep(update_rate)
        if not st.session_state.playing:
            break
else:
    fig = create_figure(st.session_state.race_time)
    placeholder.plotly_chart(fig, use_container_width=True)
