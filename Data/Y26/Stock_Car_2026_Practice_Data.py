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
NUM_COLS      = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']

ANALISE_CARROS       = ['Driver', 'Team', 'Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
ANALISE_TEAM         = ['Team', 'Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
ANALISE_MANUFACTURER = ['Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']

SECTOR_COLS = ['S1 Tm', 'S2 Tm', 'S3 Tm']
TIME_AGG    = {'Lap Tm (S)': 'min', 'S1 Tm': 'min', 'S2 Tm': 'min', 'S3 Tm': 'min', 'SPT': 'max', 'Avg Speed': 'max'}

CMAP           = 'RdYlGn_r'  # same as Race
FILTRO_PADRAO  = 3.0


# ---------------------------------------------------------------------------
# Helper: gap-to-fastest bar chart (Altair)
# ---------------------------------------------------------------------------
def _gap_bar_chart(df_min: pd.DataFrame, coluna: str, tab_name: str):
    min_val = df_min[coluna].min()
    df_min  = df_min.copy()
    df_min['Diff']  = df_min[coluna] - min_val
    df_min          = df_min.sort_values('Diff')
    df_min['Color'] = df_min['Driver'].map(CORES_PERSONALIZADAS).fillna('white')

    sort_order = df_min['Diff'].tolist()
    bars = alt.Chart(df_min).mark_bar().encode(
        x=alt.X('Driver:N', sort=sort_order),
        y=alt.Y('Diff', title=f'Diferença para o melhor {coluna} (s)'),
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
    st.title('Relatório de Dados da Sessão — Volta Mais Rápida')

    BASE_DIR      = Path(__file__).resolve().parent
    PASTA_ETAPAS  = BASE_DIR / 'Excel_Files' / 'Practice_And_Qualy'

    etapas_disponiveis = sorted(
        p for p in os.listdir(PASTA_ETAPAS)
        if os.path.isdir(PASTA_ETAPAS / p)
    )
    st.subheader('Seletor de Etapa e Sessão')
    etapa_escolhida = st.selectbox('Escolha a etapa:', ['Selecione uma etapa...'] + etapas_disponiveis)

    if etapa_escolhida == 'Selecione uma etapa...':
        st.warning('Por favor, selecione uma etapa.')
        return

    pasta_etapa   = PASTA_ETAPAS / etapa_escolhida
    arquivos_xlsx = sorted(f for f in os.listdir(pasta_etapa) if f.endswith('.xlsx'))
    labels_map    = {os.path.splitext(f)[0]: f for f in arquivos_xlsx}

    corrida_label = st.selectbox('Escolha uma sessão:', ['Selecione uma sessão...'] + sorted(labels_map))

    if corrida_label == 'Selecione uma sessão...':
        st.warning('Por favor, selecione uma sessão.')
        return

    caminho_corrida = pasta_etapa / labels_map[corrida_label]

    # -----------------------------------------------------------------------
    # Load & enrich data
    # -----------------------------------------------------------------------
    sessao = pd.read_excel(caminho_corrida)
    sessao = enrich_session(sessao)

    # -----------------------------------------------------------------------
    # Filter controls — Filter (always active, main filter)
    # -----------------------------------------------------------------------
    melhor_volta = sessao['Lap Tm (S)'].min()

    st.subheader('🔵 Filtro')
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        percentual_sessao = st.slider(
            'Volta mais rápida da sessão (%)',
            min_value=0.0,
            max_value=20.0,
            value=FILTRO_PADRAO,
            step=0.5,
        )
    with col_f2:
        percentual_piloto = st.slider(
            'Volta mais rápida de cada piloto (%)',
            min_value=0.0,
            max_value=20.0,
            value=FILTRO_PADRAO,
            step=0.5,
        )

    # Exclude lap 1; keep laps within the chosen % of the session's fastest and of the driver's fastest
    df_bp = sessao[sessao['Lap'] > 1].copy()
    class_limit  = melhor_volta * (1 + percentual_sessao / 100)
    driver_fast  = df_bp.groupby('Driver')['Lap Tm (S)'].transform('min')
    driver_limit = driver_fast * (1 + percentual_piloto / 100)
    sessao_filtrado = df_bp[(df_bp['Lap Tm (S)'] <= class_limit) & (df_bp['Lap Tm (S)'] <= driver_limit)].copy()
    st.write(f"Volta mais rápida da sessão: **{melhor_volta:.3f} s** | Limite ({percentual_sessao:.1f}%): **{class_limit:.3f} s**")
    st.write(f"Voltas consideradas: dentro de {percentual_sessao:.1f}% da sessão e {percentual_piloto:.1f}% do piloto, excl. Volta 1")

    sessao_filtrado = coerce_numeric_cols(sessao_filtrado, TEMPORAL_COLS)

    # All drivers and cars available in the session
    all_drivers = sorted(sessao['Driver'].dropna().unique().tolist())
    all_car_ids = sorted(sessao['Car_ID'].dropna().unique().tolist())

    # -----------------------------------------------------------------------
    # Graph selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Selecione o tipo de gráfico',
        ('Tabelas', 'Linhas', 'BoxPlots', 'Outros', 'Todas as Voltas'),
        index=0,
    )

    # =======================================================================
    if option == 'Tabelas':
    # =======================================================================
        def _table(group_cols):
            return (
                sessao_filtrado
                .groupby(group_cols)
                .agg({k: v for k, v in TIME_AGG.items() if k in sessao_filtrado.columns})
                .reset_index()
            )

        # By driver
        st.subheader('Tabela por Carro')
        t1 = _table(['Driver', 'Team', 'Manufacturer'])
        fmt1 = {c: '{:.3f}' for c in NUM_COLS if c in t1.columns}
        t1_styled = t1.style.format(fmt1)
        t1_styled = t1_styled.background_gradient(cmap=CMAP)
        t1_styled = t1_styled.apply(highlight_driver, subset=['Driver'])
        t1_styled = t1_styled.apply(highlight_team,   subset=['Team'])
        t1_styled = t1_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t1_styled, hide_index=True)

        # By team
        st.subheader('Tabela por Equipe')
        t2 = _table(['Team', 'Manufacturer'])
        fmt2 = {c: '{:.3f}' for c in NUM_COLS if c in t2.columns}
        t2_styled = t2.style.format(fmt2)
        t2_styled = t2_styled.background_gradient(cmap=CMAP)
        t2_styled = t2_styled.apply(highlight_team,         subset=['Team'])
        t2_styled = t2_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t2_styled, hide_index=True)

        # By manufacturer
        st.subheader('Tabela por Fabricante')
        t3 = _table(['Manufacturer'])
        fmt3 = {c: '{:.3f}' for c in NUM_COLS if c in t3.columns}
        t3_styled = t3.style.format(fmt3)
        t3_styled = t3_styled.background_gradient(cmap=CMAP)
        t3_styled = t3_styled.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t3_styled, hide_index=True)

    # =======================================================================
    elif option == 'Linhas':
    # =======================================================================
        raising_configs = [
            ('Lap Tm (S)', True,  'Média Crescente do Tempo de Volta'),
            ('S1 Tm',      True,  'Média Crescente do S1'),
            ('S2 Tm',      True,  'Média Crescente do S2'),
            ('S3 Tm',      True,  'Média Crescente do S3'),
            ('SPT',        False, 'Média Crescente do SPT'),
        ]
        for col, ascending, title in raising_configs:
            df_plot = sessao_filtrado.copy()
            df_plot['Ranking'] = df_plot.groupby('Driver')[col].rank(ascending=ascending)
            df_plot = df_plot.sort_values(['Driver', 'Ranking'])
            st.plotly_chart(px.line(df_plot, x='Ranking', y=col, color='Driver', title=title))

    # =======================================================================
    elif option == 'Outros':
    # =======================================================================
        st.subheader('Gap para o Mais Rápido')

        sector_tabs_cfg = {
            'Gap para o Carro Mais Rápido - Volta': 'Lap Tm (S)',
            'Gap para o Carro Mais Rápido - S1':    'S1 Tm',
            'Gap para o Carro Mais Rápido - S2':    'S2 Tm',
            'Gap para o Carro Mais Rápido - S3':    'S3 Tm',
        }
        tabs = st.tabs(list(sector_tabs_cfg.keys()))
        for tab, (tab_name, coluna) in zip(tabs, sector_tabs_cfg.items()):
            with tab:
                df_min = sessao_filtrado.groupby('Driver')[coluna].min().reset_index()
                st.altair_chart(_gap_bar_chart(df_min, coluna, tab_name), use_container_width=True)

        # -------------------------------------------------------------------
        st.subheader('Heatmap de Setores & Comparação em Radar')

        best_laps    = sessao_filtrado.groupby('Driver')['Lap Tm (S)'].min().reset_index()
        fastest_drv  = best_laps.loc[best_laps['Lap Tm (S)'].idxmin(), 'Driver']
        best_sectors = sessao_filtrado.groupby('Driver')[SECTOR_COLS].min().reset_index()

        sector_mins      = {col: best_sectors[col].min() for col in SECTOR_COLS}
        best_sectors_pct = best_sectors.copy()
        for col in SECTOR_COLS:
            best_sectors_pct[col] = (best_sectors[col] - sector_mins[col]) / sector_mins[col] * 100
            best_sectors[col]    -= sector_mins[col]

        best_sectors = (
            best_sectors.merge(best_laps, on='Driver')
            .sort_values('Lap Tm (S)')
            .reset_index(drop=True)
        )
        best_sectors_pct = (
            best_sectors_pct.merge(best_laps, on='Driver')
            .sort_values('Lap Tm (S)')
            .reset_index(drop=True)
        )

        heatmap_tabs = st.tabs(['Tempo (s)', 'Porcentagem (%)'])
        with heatmap_tabs[0]:
            fig_heatmap = px.imshow(
                best_sectors.set_index('Driver')[SECTOR_COLS],
                color_continuous_scale='Turbo',
                aspect='auto',
                text_auto='.3f',
            )
            fig_heatmap.update_layout(
                title='Tempo de Cada Piloto por Setor (Gap para o Melhor)',
                xaxis_title='Setor',
                yaxis_title='Piloto',
            )
            st.plotly_chart(fig_heatmap)
        with heatmap_tabs[1]:
            fig_heatmap_pct = px.imshow(
                best_sectors_pct.set_index('Driver')[SECTOR_COLS],
                color_continuous_scale='Turbo',
                aspect='auto',
                text_auto='.2f',
            )
            fig_heatmap_pct.update_layout(
                title='Gap para o Melhor por Setor (%)',
                xaxis_title='Setor',
                yaxis_title='Piloto',
            )
            st.plotly_chart(fig_heatmap_pct)

        # Radar
        selected_drivers = sessao_filtrado[sessao_filtrado['Car_ID'].isin(all_car_ids)]['Driver'].unique()
        radar_drivers    = list(set(selected_drivers) | {fastest_drv})
        radar_data       = best_sectors[best_sectors['Driver'].isin(radar_drivers)].copy()

        for col in SECTOR_COLS:
            mn, mx = radar_data[col].min(), radar_data[col].max()
            denom  = mx - mn if mx != mn else 1
            radar_data[col] = (mx - radar_data[col]) / denom

        df_radar = radar_data.melt(id_vars=['Driver'], value_vars=SECTOR_COLS,
                                   var_name='Sector', value_name='Score')

        driver_colors = {TEAM_CAR_NAMES[c]: TEAM_CAR_COLORS[c] for c in TEAM_CAR_NAMES}
        color_map = {d: driver_colors.get(d, 'green') for d in df_radar['Driver'].unique()}

        fig_radar = px.line_polar(
            df_radar, r='Score', theta='Sector', color='Driver',
            line_close=True, color_discrete_map=color_map,
        )
        fig_radar.update_traces(fill='toself', opacity=0.6)
        fig_radar.update_layout(
            title='Comparação de Desempenho por Setor — Melhores Pilotos',
            polar=dict(radialaxis=dict(
                tickmode='array',
                tickvals=[0, 0.5, 1],
                ticktext=['Lento', 'Médio', 'Rápido'],
                tickfont=dict(color='red'),
            )),
        )
        st.plotly_chart(fig_radar)

        # Fast Lap vs Previous Lap scatter
        st.subheader('Volta Mais Rápida vs Volta Anterior')
        fastest_idx  = sessao.groupby('Driver')['Lap Tm (S)'].idxmin()
        fastest_laps = sessao.loc[fastest_idx, ['Driver', 'Lap', 'Lap Tm (S)']]

        prev_rows = []
        for _, row in fastest_laps.iterrows():
            prev = sessao[(sessao['Driver'] == row['Driver']) & (sessao['Lap'] == row['Lap'] - 1)]
            if not prev.empty:
                prev_rows.append({
                    'Driver':       row['Driver'],
                    'Fast Lap':     row['Lap Tm (S)'],
                    'Previous Lap': prev['Lap Tm (S)'].iat[0],
                })

        if prev_rows:
            fig_scatter = px.scatter(
                pd.DataFrame(prev_rows),
                x='Fast Lap', y='Previous Lap', color='Driver',
                title='Volta Mais Rápida vs Volta Anterior',
            )
            fig_scatter.update_traces(marker_size=12)
            st.plotly_chart(fig_scatter, use_container_width=True)

    # =======================================================================
    elif option == 'BoxPlots':
    # =======================================================================
        st.write('Valores de todos os carros de cada fabricante')
        for var in ANALISE_MANUFACTURER:
            if var == 'Manufacturer':
                continue
            fig = px.box(
                sessao_filtrado, x=var, points='all',
                color='Manufacturer', title=f'Distribuição de {var}',
            )
            st.plotly_chart(fig)

        boxplot_cols   = {'Volta': 'Lap Tm (S)', 'S1': 'S1 Tm', 'S2': 'S2 Tm', 'S3': 'S3 Tm', 'SPT': 'SPT'}
        drivers_sorted = sorted(
            [d for d in sessao_filtrado['Driver'].dropna().unique()],
            key=lambda x: str(x),
        )
        tabs_box = st.tabs(list(boxplot_cols.keys()))

        for tab, (tab_nome, coluna) in zip(tabs_box, boxplot_cols.items()):
            with tab:
                selected = st.multiselect(
                    f'Filtrar pilotos — {coluna}',
                    options=drivers_sorted,
                    default=drivers_sorted,
                    key=f'bp_practice_{coluna}',
                )
                df_box = sessao_filtrado[sessao_filtrado['Driver'].isin(selected)]
                fig = px.box(
                    df_box, x='Driver', y=coluna,
                    points='all', color='Driver',
                    category_orders={'Driver': [d for d in drivers_sorted if d in selected]},
                )
                fig.update_layout(yaxis_title=coluna, title=f'Boxplot - {coluna}', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'Todas as Voltas':
    # =======================================================================
        st.subheader('Todas as Voltas por Piloto')

        selected_driver = st.selectbox('Escolha um piloto:', ['Todos os pilotos'] + all_drivers)

        if selected_driver == 'Todos os pilotos':
            drivers_to_show = all_drivers
        else:
            drivers_to_show = [selected_driver]

        for driver_name in drivers_to_show:
            df_drv = sessao[sessao['Driver'] == driver_name].copy()
            if df_drv.empty:
                continue

            car_id = df_drv['Car_ID'].iat[0]
            team   = df_drv['Team'].iat[0] if 'Team' in df_drv.columns else '—'

            with st.expander(f'🏎️ #{car_id}  {driver_name}  |  {team}', expanded=(selected_driver != 'Todos os pilotos')):
                display_cols = [c for c in ['Lap', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
                                if c in df_drv.columns]
                st.dataframe(df_drv[display_cols].reset_index(drop=True), use_container_width=True)
