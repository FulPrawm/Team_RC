# Stock_Car_2026_Practice_Data.py  (optimised)
import warnings
import os

import numpy as np
import pandas as pd
import plotly.express as px
import altair as alt
import streamlit as st
from pathlib import Path

from sc_shared import (
    enrich_session, coerce_numeric_cols, convert_to_seconds,
    highlight_driver, highlight_team, highlight_manufacturer,
    CORES_PERSONALIZADAS, TEAM_CAR_NAMES, TEAM_CAR_COLORS,
)

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPORAL_COLS = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']

ANALISE_CARROS       = ['Driver', 'Team', 'Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
ANALISE_TEAM         = ['Team', 'Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
ANALISE_MANUFACTURER = ['Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']

SECTOR_COLS = ['S1 Tm', 'S2 Tm', 'S3 Tm']
TIME_AGG    = {'Lap Tm (S)': 'min', 'S1 Tm': 'min', 'S2 Tm': 'min', 'S3 Tm': 'min', 'SPT': 'max', 'Avg Speed': 'max'}

# Cars shown in team-specific views
TEAM_CARS = [1, 7, 11, 38]


# ---------------------------------------------------------------------------
# Helper: gap-to-fastest bar chart (Altair)
# ---------------------------------------------------------------------------
def _gap_bar_chart(df_min: pd.DataFrame, coluna: str, tab_name: str):
    """Return an Altair bar+label chart showing gap to the fastest driver."""
    min_val = df_min[coluna].min()
    df_min  = df_min.copy()
    df_min['Diff']  = df_min[coluna] - min_val
    df_min          = df_min.sort_values('Diff')
    df_min['Color'] = df_min['Driver'].map(CORES_PERSONALIZADAS).fillna('white')

    sort_order = df_min['Diff'].tolist()
    bars = alt.Chart(df_min).mark_bar().encode(
        x=alt.X('Driver:N', sort=sort_order),
        y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
        color=alt.Color('Color:N', scale=None),
    )
    labels = alt.Chart(df_min).mark_text(
        align='center', baseline='bottom', dy=-2, color='white',
    ).encode(
        x=alt.X('Driver:N', sort=sort_order),
        y='Diff',
        text=alt.Text('Diff', format='.2f'),
    )
    return (bars + labels).properties(title=tab_name)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Fastest Time Session Data Report')

    BASE_DIR      = Path(__file__).resolve().parent
    PASTA_ETAPAS  = BASE_DIR / 'Excel_Files' / 'Practice_And_Qualy'

    etapas_disponiveis = sorted(
        p for p in os.listdir(PASTA_ETAPAS)
        if os.path.isdir(PASTA_ETAPAS / p)
    )
    st.subheader('Round and Session Selector')
    etapa_escolhida = st.selectbox('Choose the round:', ['Select a round...'] + etapas_disponiveis)

    if etapa_escolhida == 'Select a round...':
        st.warning('Please, select a round.')
        return

    pasta_etapa   = PASTA_ETAPAS / etapa_escolhida
    arquivos_xlsx = sorted(f for f in os.listdir(pasta_etapa) if f.endswith('.xlsx'))
    labels_map    = {os.path.splitext(f)[0]: f for f in arquivos_xlsx}  # label → filename

    corrida_label = st.selectbox('Choose a session:', ['Select a session...'] + sorted(labels_map))

    if corrida_label == 'Select a session...':
        st.warning('Please, select a session.')
        return

    caminho_corrida = pasta_etapa / labels_map[corrida_label]

    # -----------------------------------------------------------------------
    # Load & enrich data
    # -----------------------------------------------------------------------
    sessao = pd.read_excel(caminho_corrida)
    sessao = enrich_session(sessao)

    # -----------------------------------------------------------------------
    # Filter controls
    # -----------------------------------------------------------------------
    melhor_volta = sessao['Lap Tm (S)'].min()
    percentual   = st.slider('Select filter percentage (%)', 0.0, 20.0, 4.0, 1.0)
    tempo_limite = melhor_volta * (1 + percentual / 100)

    st.subheader('Custom filter applied')
    st.write(f"Best lap in the session: **{melhor_volta:.3f} s**")
    st.write(f"{percentual:.1f}% filter applied: **{tempo_limite:.3f} s**")

    sessao_filtrado = sessao[sessao['Lap Tm (S)'] <= tempo_limite].copy()
    sessao_filtrado = coerce_numeric_cols(sessao_filtrado, TEMPORAL_COLS)

    # -----------------------------------------------------------------------
    # Graph selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Select the type of graph',
        ('Charts', 'Lines', 'BoxPlots', 'Others', 'All Laps'),
        index=0,
    )

    # =======================================================================
    if option == 'Charts':
    # =======================================================================
        def _table(group_cols, agg_cols=None):
            """Build a grouped aggregation table ready for styling."""
            return (
                sessao_filtrado
                .groupby(group_cols)
                .agg({k: v for k, v in TIME_AGG.items() if k in sessao_filtrado.columns})
                .reset_index()
            )

        CMAP = 'coolwarm'

        # By driver
        st.subheader('Table by Car')
        t1 = _table(['Driver', 'Team', 'Manufacturer'])
        t1_styled = t1.style.format(precision=3)
        t1_styled = t1_styled.background_gradient(cmap=CMAP)
        t1_styled = t1_styled.apply(highlight_driver, subset=['Driver'])
        t1_styled = t1_styled.apply(highlight_team,   subset=['Team'])
        t1_styled = t1_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t1_styled, hide_index=True)

        # By team
        st.subheader('Table by Team')
        t2 = _table(['Team', 'Manufacturer'])
        t2_styled = t2.style.format(precision=3)
        t2_styled = t2_styled.background_gradient(cmap=CMAP)
        t2_styled = t2_styled.apply(highlight_team,         subset=['Team'])
        t2_styled = t2_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t2_styled, hide_index=True)

        # By manufacturer
        st.subheader('Table by Manufacturer')
        t3 = _table(['Manufacturer'])
        t3_styled = t3.style.format(precision=3)
        t3_styled = t3_styled.background_gradient(cmap=CMAP)
        t3_styled = t3_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t3_styled, hide_index=True)


    # =======================================================================
    elif option == 'Lines':
    # =======================================================================
        raising_configs = [
            ('Lap Tm (S)', True,  'Lap Time Raising Average'),
            ('S1 Tm',      True,  'S1 Raising Average'),
            ('S2 Tm',      True,  'S2 Raising Average'),
            ('S3 Tm',      True,  'S3 Raising Average'),
            ('SPT',        False, 'SPT Raising Average'),
        ]
        for col, ascending, title in raising_configs:
            df_plot = sessao_filtrado.copy()
            df_plot['Ranking'] = df_plot.groupby('Driver')[col].rank(ascending=ascending)
            df_plot = df_plot.sort_values(['Driver', 'Ranking'])
            st.plotly_chart(px.line(df_plot, x='Ranking', y=col, color='Driver', title=title))

    # =======================================================================
    elif option == 'Others':
    # =======================================================================
        st.subheader('Gap to Fastest')

        sector_tabs_cfg = {
            'Gap to Fastest Car - Lap': 'Lap Tm (S)',
            'Gap to Fastest Car - S1':  'S1 Tm',
            'Gap to Fastest Car - S2':  'S2 Tm',
            'Gap to Fastest Car - S3':  'S3 Tm',
        }
        tabs = st.tabs(list(sector_tabs_cfg.keys()))
        for tab, (tab_name, coluna) in zip(tabs, sector_tabs_cfg.items()):
            with tab:
                df_min = sessao_filtrado.groupby('Driver')[coluna].min().reset_index()
                st.altair_chart(_gap_bar_chart(df_min, coluna, tab_name), use_container_width=True)

        # -------------------------------------------------------------------
        st.subheader('Sector Heatmap & Radar Comparison')

        best_laps    = sessao_filtrado.groupby('Driver')['Lap Tm (S)'].min().reset_index()
        fastest_drv  = best_laps.loc[best_laps['Lap Tm (S)'].idxmin(), 'Driver']
        best_sectors = sessao_filtrado.groupby('Driver')[SECTOR_COLS].min().reset_index()

        # Gap to fastest sector
        for col in SECTOR_COLS:
            best_sectors[col] -= best_sectors[col].min()

        best_sectors = (
            best_sectors.merge(best_laps, on='Driver')
            .sort_values('Lap Tm (S)')
            .reset_index(drop=True)
        )

        # Heatmap
        fig_heatmap = px.imshow(
            best_sectors.set_index('Driver')[SECTOR_COLS],
            color_continuous_scale='Turbo',
            aspect='auto',
            text_auto='.3f',
        )
        fig_heatmap.update_layout(
            title='Driver Times in Each Sector (Gap to Best)',
            xaxis_title='Sector',
            yaxis_title='Driver',
        )
        st.plotly_chart(fig_heatmap)

        # Radar
        selected_drivers = sessao_filtrado[sessao_filtrado['Car_ID'].isin(TEAM_CARS)]['Driver'].unique()
        radar_drivers    = list(set(selected_drivers) | {fastest_drv})
        radar_data       = best_sectors[best_sectors['Driver'].isin(radar_drivers)].copy()

        # Normalise: 0 = slowest, 1 = fastest
        for col in SECTOR_COLS:
            mn, mx      = radar_data[col].min(), radar_data[col].max()
            denom       = mx - mn if mx != mn else 1
            radar_data[col] = (mx - radar_data[col]) / denom

        df_radar = radar_data.melt(id_vars=['Driver'], value_vars=SECTOR_COLS,
                                   var_name='Sector', value_name='Score')

        driver_colors = {TEAM_CAR_NAMES[c]: TEAM_CAR_COLORS[c] for c in TEAM_CARS if c in TEAM_CAR_NAMES}
        color_map = {
            d: driver_colors.get(d, 'green')
            for d in df_radar['Driver'].unique()
        }

        fig_radar = px.line_polar(
            df_radar, r='Score', theta='Sector', color='Driver',
            line_close=True, color_discrete_map=color_map,
        )
        fig_radar.update_traces(fill='toself', opacity=0.6)
        fig_radar.update_layout(
            title='Top Drivers - Sector Performance Comparison',
            polar=dict(radialaxis=dict(
                tickmode='array',
                tickvals=[0, 0.5, 1],
                ticktext=['Slow', 'Average', 'Fast'],
                tickfont=dict(color='grey'),
            )),
        )
        st.plotly_chart(fig_radar)

        # Fast Lap vs Previous Lap scatter
        st.subheader('Fast Lap vs Previous Lap')
        fastest_idx  = sessao.groupby('Driver')['Lap Tm (S)'].idxmin()
        fastest_laps = sessao.loc[fastest_idx, ['Driver', 'Lap', 'Lap Tm (S)']]

        prev_rows = []
        for _, row in fastest_laps.iterrows():
            prev = sessao[(sessao['Driver'] == row['Driver']) & (sessao['Lap'] == row['Lap'] - 1)]
            if not prev.empty:
                prev_rows.append({
                    'Driver':        row['Driver'],
                    'Fast Lap':      row['Lap Tm (S)'],
                    'Previous Lap':  prev['Lap Tm (S)'].iat[0],
                })

        if prev_rows:
            fig_scatter = px.scatter(
                pd.DataFrame(prev_rows),
                x='Fast Lap', y='Previous Lap', color='Driver',
                title='Fastest Lap vs Previous Lap',
            )
            fig_scatter.update_traces(marker_size=12)
            st.plotly_chart(fig_scatter, use_container_width=True)

    # =======================================================================
    elif option == 'BoxPlots':
    # =======================================================================
        st.write('Values from every car for each manufacturer')
        for var in ANALISE_MANUFACTURER:
            if var == 'Manufacturer':
                continue
            fig = px.box(
                sessao_filtrado, x=var, points='all',
                color='Manufacturer', title=f'{var} distribution',
            )
            st.plotly_chart(fig)

        boxplot_cols = {'Lap': 'Lap Tm (S)', 'S1': 'S1 Tm', 'S2': 'S2 Tm', 'S3': 'S3 Tm', 'SPT': 'SPT'}
        tabs_box     = st.tabs(list(boxplot_cols.keys()))
        drivers_sorted = sorted(sessao_filtrado['Driver'].unique())

        for tab, (tab_nome, coluna) in zip(tabs_box, boxplot_cols.items()):
            with tab:
                fig = px.box(
                    sessao_filtrado, x='Driver', y=coluna,
                    points='all', color='Driver',
                    category_orders={'Driver': drivers_sorted},
                )
                fig.update_layout(yaxis_title=coluna, title=f'Boxplot - {coluna}', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'All Laps':
    # =======================================================================
        for car_id in TEAM_CARS:
            name = TEAM_CAR_NAMES.get(car_id, f'Car {car_id}')
            st.write(name)
            st.dataframe(sessao[sessao['Car_ID'] == car_id])
