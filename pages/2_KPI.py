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
import plotly.graph_objects as go

#header
st.image('header.png')

#Title
st.title("KPI Data Report")

# Caminho base para os arquivos de KPI
PASTA_KPI = "Arquivos Motec"

# Lista etapas (pastas)
etapas_disponiveis = [p for p in os.listdir(PASTA_KPI) if os.path.isdir(os.path.join(PASTA_KPI, p))]
etapa_escolhida = st.selectbox("Escolha a etapa:", sorted(etapas_disponiveis))

# Caminho da etapa
pasta_etapa = os.path.join(PASTA_KPI, etapa_escolhida)
arquivos = os.listdir(pasta_etapa)

# Encontrar arquivos performance e vitals
arquivos_perf = {f.replace("_performance.xlsx", "") for f in arquivos if f.endswith("_performance.xlsx")}
arquivos_vitals = {f.replace("_vitals.xlsx", "") for f in arquivos if f.endswith("_vitals.xlsx")}
arquivos_corners = {f.replace("_corners.xlsx", "") for f in arquivos if f.endswith("_corners.xlsx")}

# Interseção entre os dois tipos (só os que têm ambos)
corridas_disponiveis = sorted(arquivos_perf & arquivos_vitals)

# Seletor de corrida
corrida_selecionada = st.selectbox("Escolha a sessão:", corridas_disponiveis)

# Montagem dos caminhos
arquivo_perf = os.path.join(pasta_etapa, f"{corrida_selecionada}_performance.xlsx")
arquivo_vitals = os.path.join(pasta_etapa, f"{corrida_selecionada}_vitals.xlsx")
arquivo_corners = os.path.join(pasta_etapa, f"{corrida_selecionada}_corners.xlsx")

def converter_tempo(val):
    try:
        val_str = str(val)
        return float(val_str.replace('.', '')) / 1000
    except:
        return None

df = pd.read_excel(arquivo_perf, converters={"Calc Lap Time [s]": converter_tempo})
df1 = pd.read_excel(arquivo_vitals, converters={"Calc Lap Time [s]": converter_tempo})
df2 = None
if os.path.exists(arquivo_corners):
    df2 = pd.read_excel(arquivo_corners)
    df2["Car"] = df2["Car"].astype(str)


df["Car"] = df["Car"].astype(str)
df1["Car"] = df1["Car"].astype(str)

# Driver and Car Performance
grip_factors=[
    "Math Aero Grip Factor [G]",
    "Math Braking Grip Factor [G]",
    "Math Cornering Grip Factor [G]",
    "Math Overall Grip Factor [G]",
    "Math Traction Grip Factor [G]",
]

accelerating=[
    "Full Throttle Time [s]",
    "Part Throttle Time [s]",
    "Math Throttle Aggression [%/s]",
    "Coasting Time [s]",
]

braking=[
    "Math Brake Pressure Total [bar]",
    "Math Brake Bias Front [%]",
    "Math Brake Aggression [bar/s]",
    "Math Brake Release Smoothness [bar/s]",
    "Braking Time [s]",
    "Math Brake Temperature Front [°C]",
    "Math Brake Temperature Rear [°C]",
    
]

steering=[
    "Math Steering Smooth",
    "Math Vehicle Balance [°]",
    "Vehicle Balance - Entry [°]",
    "Vehicle Balance - MID [°]",
    "Vehicle Balance - Exit [°]",
    "Vehicle Balance - HS [°]",
    "Vehicle Balance - LS [°]"
]

# Car Vitals Signals
vitals=[
"Calc Lap Time [s]",
"Engine RPM [rpm]",
"Battery Voltage [V]",
"Engine Oil Pressure [bar]",
"Engine Oil Temperature [°C]",
"Coolant Pressure [bar]",
"Coolant Temperature [°C]",
"Gearbox Temperature [°C]",
"Fuel Temperature [°C]",
"Airbox Temperature [°C]",
"Exhaust Lambda Bank 1 [LA]",
"Fuel Pressure Differential [bar]",
"Fuel Used [l]",
"Fuel Used per Lap [l]",
"Brake Temp FL [°C]",
"Brake Temp FR [°C]",
"Brake Temp RL [°C]",
"Brake Temp RR [°C]"
]

# Corner Performance
corners=[
"Math Aero Grip Factor [G]",
"Math Braking Grip Factor [G]",
"Math Cornering Grip Factor [G]",
"Math Overall Grip Factor [G]",
"Math Traction Grip Factor [G]",
"Corr Speed [km/h]"
]

# Mapping colors for specific cars
car_colors = {
    '10': 'red',
    '11': 'blue',
    '44': 'gray',
    '88': 'yellow'
}

# Filtro automático com base na melhor volta
st.subheader("Filtro automático baseado em 4% da melhor volta da sessão")

melhor_volta = df["Calc Lap Time [s]"].min()
tempo_limite = melhor_volta * 1.04

st.write(f"Melhor volta da sessão: **{melhor_volta:.3f} s**")
st.write(f"Filtro aplicado (4% acima): **{tempo_limite:.3f} s**")

# Aplicando o filtro
df_filter = df[df["Calc Lap Time [s]"] <= tempo_limite]
df1_filter = df1[df1["Calc Lap Time [s]"] <= tempo_limite]

#Creating a list to select which type of graphs we want to display
opcoes_kpi = ["Grip Factors", "Aceleração", "Frenagem", "Esterçamento", "Vitais", "Outros"]
if df2 is not None:
    opcoes_kpi.insert(5, "Curvas")  # Insere "Curvas" na posição certa se o arquivo existir

option = st.selectbox("Tipo de KPI", opcoes_kpi, index=0)

if option == "Grip Factors":
    st.title("Gráficos de Grip Factors")
    for idx, var in enumerate(grip_factors):
        fig1 = px.scatter(df_filter, x='Lap', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig1, key=f"grip_factor_{var}_{idx}")  #Adding an index (idk how this works but it does)

elif option == "Aceleração":
    st.title("Gráficos de Aceleração")
    for idx, var in enumerate(accelerating):
        fig2 = px.scatter(df_filter, x='Lap', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig2, key=f"accelerating_{var}_{idx}")

elif option == "Frenagem":
    st.title("Gráficos de Frenagem")
    for idx, var in enumerate(braking):
        fig3 = px.scatter(df_filter, x='Lap', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig3, key=f"braking_{var}_{idx}")

elif option == "Esterçamento":
    st.title("Gráficos de Esterçamento")
    for idx, var in enumerate(steering):
        fig4 = px.scatter(df_filter, x='Lap', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig4, key=f"steering_{var}_{idx}")

elif option == "Vitais":
    st.title("Gráficos de vitais")
    for idx, var in enumerate(vitals):
        fig5 = px.scatter(df1_filter, x='Lap', y=var, color="Car", symbol="Car", trendline="ols", color_discrete_map=car_colors)
        with st.empty():
            st.plotly_chart(fig5, key=f"vitals_{var}_{idx}")

elif option == "Curvas":
    st.title("Gráficos por curva")
    curvas_disponiveis = sorted(df2["Corner"].unique())
    abas = st.tabs(curvas_disponiveis)

    for tab, curva in zip(abas, curvas_disponiveis):
        with tab:
            st.subheader(f"Seção: {curva}")
            df_curva = df2[df2["Corner"] == curva]

            for idx, var in enumerate(corners[:-1]):  # Ignora "Corr Speed [km/h]" se quiser
                fig = px.scatter(
                    df_curva,
                    x="Lap",
                    y=var,
                    color="Car",
                    symbol="Car",
                    trendline="ols",
                    color_discrete_map=car_colors,
                    title=f"{var}"
                )
                st.plotly_chart(fig, key=f"curva_{curva}_{var}_{idx}")



elif option == "Outros":
    st.title("Gráfico de comparação entre pilotos")

    df_avg = df_filter.groupby("Car")[grip_factors].mean()
    categories = grip_factors + [grip_factors[0]]

    fig6 = go.Figure()

    for car_id, row in df_avg.iterrows():
        values = [row[col] for col in grip_factors]
        values += values[:1]

        fig6.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=f'Car {car_id}',
        line=dict(width=2, color=car_colors.get(str(car_id), 'white'))
    ))


    # Escala automática
    all_values = df_avg[grip_factors].values.flatten()
    r_min = float(np.nanmin(all_values)) * 0.95
    r_max = float(np.nanmax(all_values)) * 1.05

    fig6.update_layout(
        polar=dict(
            bgcolor="#2e2e2e",
            radialaxis=dict(
                visible=True,
                range=[r_min, r_max],
                color='white',
                tickfont=dict(color='white')
            ),
            angularaxis=dict(color='white', tickfont=dict(color='white'))
        ),
        showlegend=True,
        paper_bgcolor="#2e2e2e",
        font_color="white",
        title='Average Grip Profile per Car',
    )

    st.plotly_chart(fig6)
