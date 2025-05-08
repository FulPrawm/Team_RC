# Importing the libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno
import plotly.express as px
import statsmodels as sm
import streamlit as st
import os

#header
st.image('header.png')

#Title
st.title("KPI Data Report")

# Driver and Car Performance
df = pd.read_excel('kpi.xlsx')
pd.set_option('display.max_columns', None)
df['Car'] = df['Car'].astype(str)

#Vitals
df1 = pd.read_excel('vital.xlsx')
pd.set_option('display.max_columns', None)
df1['Car'] = df1['Car'].astype(str)

# Driver and Car Performance
grip_factors=[
    "Grip Factor Aero (G)",
    "Grip Factor Braking (G)",
    "Grip Factor Cornering (G)",
    "Grip Factor Overall (G)",
    "Grip Factor Traction (G)",
    "Grip Factor Trailbraking (G)"
]

accelerating=[
    "Full Throttle Time (s)",
    "Part Throttle Time (s)",
    "Throttle speed (%/s)",
    "Speed (km/h)"
]

braking=[
    "Brake Press Total (psi)",
    "Brake Balance Gated (%)",
    "Front Disc Temp (°C)",
    "Rear Disc Temp (°C)",
    "Braking Efficiency (%)",
    "Avg Brake Pressure (psi)",
    "Braking Aggressiveness (psi/s)",
    "Brake release smoothness (psi/s)",
    "Brake Balance Gated (%)",
    "Brake Temperature Balance (%)",
    "Braking Time (s)"
]

steering=[
    "Steering Smoothness (°)",
    "Understeer Angle (°)",
    "Understeer angle - ENTRY (°)",
    "Understeer angle - MID (°)",
    "Understeer angle - EXIT (°)",
    "Understeer angle - HS (°)",
    "Understeer angle - LS (°)"
]

# Car Vitals Signals
vitals=[
    "ECU_Airbox_Temp (°C)",
    "ECU_Coolant_Temp (°C)",
    "Gearbox temp (°C)",
    "ECU_Oil_Temp (°C)",
    "ECU_Oil_Pressure (bar)",
    "DH Temp (°C)",
    "DH Press (psi)",
    "ECU_Fuel_Temp (°C)",
    "ECU_Fuel_Pressure (bar)",
    "ECU_Voltage (V)",
    "ECU_Eng_Safe_Soft ()",
    "ECU_Eng_Safe_Hard ()",
    "ECU_Fuel_Total (ltr)",
    "Tank Fuel Used (L)",
    "Fuel Per Lap (L/lap)",
    "Lambda1_Full throttle (-)",
    "Lambda2_Full throttle (-)",
    "LH-RH Lambda ratio (-)",
    "ECU_Lambda_1",
    "ECU_Lambda_2"
]

# Mapping colors for specific cars
car_colors = {
    '10': 'red',
    '29': 'blue',
    '44': 'gray',
    '90': 'yellow'
}

# Filtering the Dataframes
st.title("Gráfico para filtragem")
valor_minimo = st.number_input("Coloque o valor mínimo desejado", min_value=0, max_value=200, value = 50)
valor_maximo = st.number_input("Coloque o valor máximo desejado", min_value=0, max_value=200, value = 150)

# Displaying a graph to show filter results of KPI
df_filter = df[(df["Lap time (s)"] >= valor_minimo) & (df["Lap time (s)"] <= valor_maximo)]
fig1 = px.box(df_filter, x=df_filter["Lap time (s)"])
st.plotly_chart(fig1, key="kpi_graph")

# Same thing but for VITALS
df1_filter = df1[(df1["Lap time (s)"] >= valor_minimo) & (df1["Lap time (s)"] <= valor_maximo)]
fig2 = px.box(df1_filter, x = df1_filter["Lap time (s)"])
st.plotly_chart(fig2, key="vitals_graph")

#Creating a list to select which type of graphs we want to display
option = st.selectbox(
    "Tipo de KPI",
    ("Grip Factors", "Aceleração", "Frenagem", "Esterçamento", "Vitais"),
    index=0  # number 0 is to open it blank
)

if option == "Grip Factors":
    st.title("Gráficos de Grip Factors")
    for idx, var in enumerate(grip_factors):
        fig1 = px.scatter(df_filter, x='Lap Number ', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig1, key=f"grip_factor_{var}_{idx}")  #Adding an index (idk how this works but it does)

elif option == "Aceleração":
    st.title("Gráficos de Aceleração")
    for idx, var in enumerate(accelerating):
        fig2 = px.scatter(df_filter, x='Lap Number ', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig2, key=f"accelerating_{var}_{idx}")

elif option == "Frenagem":
    st.title("Gráficos de Frenagem")
    for idx, var in enumerate(braking):
        fig3 = px.scatter(df_filter, x='Lap Number ', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig3, key=f"braking_{var}_{idx}")

elif option == "Esterçamento":
    st.title("Gráficos de Esterçamento")
    for idx, var in enumerate(steering):
        fig4 = px.scatter(df_filter, x='Lap Number ', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig4, key=f"steering_{var}_{idx}")

elif option == "Vitais":
    st.title("Gráficos de vitais")
    for idx, var in enumerate(vitals):
        fig5 = px.scatter(df1_filter, x='Lap Number', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig5, key=f"vitals_{var}_{idx}")