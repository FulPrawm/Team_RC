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
df1 = pd.read_excel("vitals.xlsx", header=4, skiprows=[5])

# Remove espaços dos nomes das colunas (importante)
df1.columns = df1.columns.str.strip()

# Pular as 6 primeiras colunas
df1 = df1.iloc[:, 6:]

# Obter o nome da primeira coluna
first_col = df1.columns[0]

# Corrigir vírgulas e converter para float apenas na primeira coluna
df1[first_col] = (
    df1[first_col]
    .astype(str)
    .str.strip()
    .str.replace(',', '.', regex=False)
)
df1[first_col] = pd.to_numeric(df1[first_col], errors='coerce')

# Agora sim: dividir por 1000
df1[first_col] = df1[first_col] / 1000

# Agora repetir o processo para o restante das colunas
for col in df1.columns[1:]:
    df1[col] = (df1[col])

# Criar uma lista com os valores repetidos 31 vezes cada
car_ids = [11]*32 + [88]*31 + [44]*31 + [10]*31

# Adicionar como nova coluna
df1['Car'] = car_ids

df1['Lap Number'] = df1.groupby('Car').cumcount() + 1

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
"Calc Lap Time [s]",
"Engine RPM [rpm]",
"Battery Voltage [V]",
"Engine Oil Pressure [bar]",
"Engine Oil Temperature [°C]",
"Coolant Temperature [°C]",
"Gearbox Temperature [°C]",
"Fuel Temperature [°C]",
"Airbox Temperature [°C]",
"Exhaust Lambda Bank 1 [LA]",
"Fuel Pressure Differential [bar]",
"Brake Temp FL [°C]",
"Brake Temp FR [°C]",
"Brake Temp RL [°C]",
"Brake Temp RR [°C]"
]

# Força conversão para número (erros viram NaN)
for col in vitals:
    if col in df1.columns:
        # Se for string, tenta corrigir vírgulas
        if df1[col].dtype == 'object':
            df1[col] = (
                df1[col]
                .astype(str)
                .str.strip()
                .str.replace(',', '.', regex=False)
            )
        # Converte para número
        df1[col] = pd.to_numeric(df1[col], errors='coerce')

# Mapping colors for specific cars
car_colors = {
    '10': 'red',
    '11': 'blue',
    '44': 'gray',
    '88': 'yellow'
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
df1_filter = df1[(df1["Calc Lap Time [s]"] >= valor_minimo) & (df1["Calc Lap Time [s]"] <= valor_maximo)]
fig2 = px.box(df1_filter, x = df1_filter["Calc Lap Time [s]"])
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
        fig3 = px.scatter(df_filter, x='Lap Number', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
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