# Stock_Car_2026_Race_Data.py  (optimised)
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import streamlit as st
from pathlib import Path

from sc_shared import (
    enrich_session, coerce_numeric_cols, convert_to_seconds,
    highlight_driver, highlight_team, highlight_manufacturer,
    add_trend_line,
    CORES_PERSONALIZADAS, TEAM_CAR_NAMES, TEAM_CAR_COLORS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPORAL_COLS = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
NUM_COLS      = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
SECTOR_COLS   = ['S1 Tm', 'S2 Tm', 'S3 Tm']

ANALISE_CARROS       = ['Driver', 'Manufacturer', 'Team', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
ANALISE_TEAM         = ['Team', 'Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
ANALISE_MANUFACTURER = ['Manufacturer', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']

TRAFFIC_THRESHOLD = 3.0
CMAP = 'RdYlGn_r'


# ---------------------------------------------------------------------------
# Traffic detection  (vectorised)
# ---------------------------------------------------------------------------
def _detect_traffic(sessao: pd.DataFrame) -> pd.DataFrame:
    df = sessao.sort_values(['Lap', 'Crossing Seconds']).copy()
    df['_prev_crossing'] = df.groupby('Lap')['Crossing Seconds'].shift(1)
    df['_gap_ahead']     = df['Crossing Seconds'] - df['_prev_crossing']
    df['Lap Traffic?']   = np.where(
        df['_gap_ahead'].notna() & (df['_gap_ahead'] < TRAFFIC_THRESHOLD),
        'Yes', 'No',
    )
    return df.drop(columns=['_prev_crossing', '_gap_ahead'])


# ---------------------------------------------------------------------------
# Gap/crossing calculations
# ---------------------------------------------------------------------------
def _add_crossing_gaps(sessao: pd.DataFrame) -> pd.DataFrame:
    if 'Crossing Time' not in sessao.columns:
        return sessao

    sessao['Crossing Seconds']    = pd.to_timedelta(sessao['Crossing Time']).dt.total_seconds()
    sessao['Cumulative Crossing'] = sessao.groupby('Car_ID')['Crossing Seconds'].cummax()

    laps_per_car = sessao.groupby('Car_ID')['Lap'].max()
    max_laps     = laps_per_car.max()
    candidates   = laps_per_car[laps_per_car == max_laps].index
    winner       = (
        sessao[sessao['Car_ID'].isin(candidates)]
        .groupby('Car_ID')['Cumulative Crossing'].max()
        .idxmin()
    )

    winner_times = (
        sessao[sessao['Car_ID'] == winner][['Lap', 'Cumulative Crossing']]
        .rename(columns={'Cumulative Crossing': 'Winner Crossing'})
    )
    sessao = sessao.merge(winner_times, on='Lap', how='left')
    sessao['Gap to Winner']  = sessao['Cumulative Crossing'] - sessao['Winner Crossing']
    leader_times             = sessao.groupby('Lap')['Crossing Seconds'].transform('min')
    sessao['Gap to Leader']  = sessao['Crossing Seconds'] - leader_times
    sessao = _detect_traffic(sessao)
    return sessao


# ---------------------------------------------------------------------------
# Manufacturer table: top-2 cars per manufacturer
# ---------------------------------------------------------------------------
def _manufacturer_top2_table(sessao: pd.DataFrame, sessao_filtrado: pd.DataFrame) -> pd.DataFrame:
    if 'Crossing Time' in sessao.columns:
        sessao['Crossing Seconds'] = pd.to_timedelta(sessao['Crossing Time']).dt.total_seconds()

    laps_per_car  = sessao.groupby('Car_ID')['Lap'].max()
    eligible_cars = laps_per_car[laps_per_car > 0].index

    final_times = (
        sessao[sessao['Car_ID'].isin(eligible_cars)]
        .groupby('Car_ID')
        .apply(lambda df: pd.Series({
            'MaxLap':       df['Lap'].max(),
            'LastCrossing': df.loc[df['Lap'].idxmax(), 'Crossing Seconds'],
        }))
        .reset_index()
    )
    final_times['Manufacturer'] = final_times['Car_ID'].map(
        sessao.set_index('Car_ID')['Manufacturer'].to_dict()
    )
    top2 = (
        final_times
        .sort_values(['MaxLap', 'LastCrossing'], ascending=[False, True])
        .groupby('Manufacturer').head(2)
        .reset_index(drop=True)
    )
    top2_dict   = top2.groupby('Manufacturer')['Car_ID'].apply(list).to_dict()
    sessao_top2 = sessao_filtrado[sessao_filtrado['Car_ID'].isin(top2['Car_ID'])]
    result = (
        sessao_top2[ANALISE_MANUFACTURER]
        .groupby('Manufacturer').mean(numeric_only=True)
        .reset_index()
    )
    result['Top 2 Cars'] = result['Manufacturer'].map(top2_dict)
    return result


# ---------------------------------------------------------------------------
# Aerodynamic efficiency scatter
# ---------------------------------------------------------------------------
def _plot_efficiency(df: pd.DataFrame, title_suffix: str = '') -> go.Figure:
    fig = px.scatter(
        df, x='Lap Tm (S)', y='SPT',
        color='Team', symbol='Team',
        title=f'Aerodynamic Efficiency {title_suffix}',
        hover_data=['Car_ID'],
    )
    fig.update_traces(marker_size=12)
    fig.add_vline(x=df['Lap Tm (S)'].mean(), line_dash='dash', line_color='white',
                  annotation_text='Average Lap Tm', annotation_position='bottom left',
                  annotation_font_color='white')
    fig.add_hline(y=df['SPT'].mean(), line_dash='dash', line_color='white',
                  annotation_text='Average SPT', annotation_position='top right',
                  annotation_font_color='white')
    return fig


# ---------------------------------------------------------------------------
# Gap-to-fastest bar chart (Altair)
# ---------------------------------------------------------------------------
def _gap_bar_chart(df_avg: pd.DataFrame, coluna: str, tab_name: str):
    min_val = df_avg[coluna].min()
    df_avg  = df_avg.copy()
    df_avg['Diff']  = df_avg[coluna] - min_val
    df_avg          = df_avg.sort_values('Diff')
    df_avg['Color'] = df_avg['Driver'].map(CORES_PERSONALIZADAS).fillna('white')

    sort_order = df_avg['Diff'].tolist()
    bars = alt.Chart(df_avg).mark_bar().encode(
        x=alt.X('Driver:N', sort=sort_order),
        y=alt.Y('Diff', title=f'Diff to Best {coluna} (s)'),
        color=alt.Color('Color:N', scale=None),
    )
    labels = alt.Chart(df_avg).mark_text(
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
    st.title('Session Data Report')

    BASE_DIR     = Path(__file__).resolve().parent
    PASTA_ETAPAS = BASE_DIR / 'Excel_Files' / 'Races'

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
    labels_map    = {os.path.splitext(f)[0]: f for f in arquivos_xlsx}

    corrida_label = st.selectbox('Choose a race:', ['Select a race...'] + sorted(labels_map))
    if corrida_label == 'Select a race...':
        st.warning('Please, select a race.')
        return

    caminho_corrida = pasta_etapa / labels_map[corrida_label]

    # -----------------------------------------------------------------------
    # Load & enrich
    # -----------------------------------------------------------------------
    sessao = pd.read_excel(caminho_corrida)
    sessao = enrich_session(sessao)

    sessao['Last Lap Diff'] = sessao.groupby('Car_ID')['Lap Tm (S)'].diff()
    sessao['Fast Lap Diff'] = sessao['Lap Tm (S)'] - sessao.groupby('Car_ID')['Lap Tm (S)'].transform('min')
    sessao = _add_crossing_gaps(sessao)

    if 'Crossing Seconds' not in sessao.columns:
        st.warning('⚠️ This session file does not contain crossing time data.')

    # -----------------------------------------------------------------------
    # Filter controls — B-Pillar filter (optional, off by default)
    # -----------------------------------------------------------------------
    melhor_volta      = sessao['Lap Tm (S)'].min()
    voltas_por_piloto = sessao.groupby('Car_ID')['Lap'].nunique()
    max_voltas        = voltas_por_piloto.max()
    min_voltas        = int(np.floor(max_voltas * 0.5))
    pilotos_validos   = voltas_por_piloto[voltas_por_piloto >= min_voltas].index

    # Exclude lap 1 and pit laps; only keep drivers who completed >= 50% of the race laps
    df_base = sessao[
        sessao['Car_ID'].isin(pilotos_validos) &
        (sessao['Lap'] > 1)
    ].copy()

    st.subheader('🔵 B-Pillar Filter')
    usar_filtro = st.checkbox('Enable B-Pillar filter (limit laps by % over the fastest lap)', value=False)

    if usar_filtro:
        percentual = st.slider(
            'Select lap time filter percentage (%)',
            min_value=0.0,
            max_value=20.0,
            value=4.0,
            step=1.0,
        )
        # Keep all laps within the chosen % of class fastest and driver fastest
        class_limit     = melhor_volta * (1 + percentual / 100)
        driver_fast     = df_base.groupby('Driver')['Lap Tm (S)'].transform('min')
        driver_limit    = driver_fast * (1 + percentual / 100)
        sessao_filtrado = df_base[(df_base['Lap Tm (S)'] <= class_limit) & (df_base['Lap Tm (S)'] <= driver_limit)].copy()
        st.write(f"Class fastest: **{melhor_volta:.3f} s** | {percentual:.1f}% limit: **{class_limit:.3f} s**")
        st.write(f"Laps used: within {percentual:.1f}% class & driver limits, excl. Lap 1")
    else:
        sessao_filtrado = df_base
        st.write('B-Pillar filter disabled — showing all laps (excl. Lap 1) for qualifying drivers.')

    st.write(f"🧮 Maximum laps: **{max_voltas}** | Min laps to qualify: **{min_voltas}**")

    for col in SECTOR_COLS:
        sessao_filtrado[col] = sessao_filtrado[col].apply(convert_to_seconds)
    sessao_filtrado = coerce_numeric_cols(sessao_filtrado, TEMPORAL_COLS)

    # Full race (unfiltered) with sector times normalised — used for Progression charts
    for col in SECTOR_COLS:
        sessao[col] = sessao[col].apply(convert_to_seconds)
    sessao = coerce_numeric_cols(sessao, TEMPORAL_COLS)

    # All drivers and cars in the session (for All Laps / Percentual diff)
    all_drivers = sorted(
        [d for d in sessao['Driver'].dropna().unique()],
        key=lambda x: str(x),
    )
    all_car_ids = sorted(sessao['Car_ID'].dropna().unique().tolist())

    # -----------------------------------------------------------------------
    # Graph selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Select the type of graph',
        ('Chart', 'Lines', 'Histograms', 'BoxPlots', 'Others', 'All Laps'),
        index=0,
    )

    # =======================================================================
    if option == 'Chart':
    # =======================================================================
        tabela1 = (
            sessao_filtrado[ANALISE_CARROS]
            .groupby(['Driver', 'Team', 'Manufacturer'])
            .mean(numeric_only=True)
            .reset_index()
        )
        clean_pct = (
            sessao.groupby('Driver')['Lap Traffic?']
            .apply(lambda x: (x == 'No').mean() * 100)
            .reset_index()
            .rename(columns={'Lap Traffic?': '% Clean Laps'})
        ) if 'Lap Traffic?' in sessao.columns else pd.DataFrame(columns=['Driver', '% Clean Laps'])

        tabela1 = tabela1.merge(clean_pct, on='Driver', how='left')

        st.subheader('Table ordered by Car')
        fmt_t1 = {c: '{:.2f}' for c in NUM_COLS if c in tabela1.columns}
        t1s = tabela1.style.format(fmt_t1)
        t1s = t1s.background_gradient(cmap=CMAP)
        t1s = t1s.apply(highlight_driver,       subset=['Driver'])
        t1s = t1s.apply(highlight_team,         subset=['Team'])
        t1s = t1s.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t1s, hide_index=True)

        st.subheader('Consistency by driver (Standard Deviation)')
        std_df = (
            sessao_filtrado[ANALISE_CARROS]
            .groupby(['Driver', 'Team', 'Manufacturer'])
            .std(numeric_only=True)
            .reset_index()
        )
        fmt_std = {c: '{:.3f}' for c in NUM_COLS if c in std_df.columns}
        std_s = std_df.style.format(fmt_std)
        std_s = std_s.background_gradient(cmap=CMAP)
        std_s = std_s.apply(highlight_driver,       subset=['Driver'])
        std_s = std_s.apply(highlight_team,         subset=['Team'])
        std_s = std_s.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(std_s, hide_index=True)

        st.subheader('Table ordered by Team')
        team_df = (
            sessao_filtrado[ANALISE_TEAM]
            .groupby(['Team', 'Manufacturer'])
            .mean(numeric_only=True)
            .reset_index()
        )
        fmt_tm = {c: '{:.3f}' for c in NUM_COLS if c in team_df.columns}
        tms = team_df.style.format(fmt_tm)
        tms = tms.background_gradient(cmap=CMAP)
        tms = tms.apply(highlight_team,         subset=['Team'])
        tms = tms.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(tms, hide_index=True)

        manuf_table = _manufacturer_top2_table(sessao, sessao_filtrado)
        st.subheader('Analysis of BoP (average of the best 2 results from each brand)')
        fmt_mf = {c: '{:.3f}' for c in NUM_COLS if c in manuf_table.columns}
        mfs = manuf_table.style.format(fmt_mf)
        mfs = mfs.background_gradient(cmap=CMAP)
        mfs = mfs.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(mfs, hide_index=True)

        st.subheader('Race Lap Time Table')
        lap_table = (
            sessao_filtrado
            .pivot(index='Driver', columns='Lap', values='Lap Tm (S)')
            .sort_index(axis=1)
        )
        lap_table.columns = [f'Lap {int(c)}' for c in lap_table.columns]
        lts = lap_table.style.format(lambda x: f'{x:.2f}' if pd.notna(x) else '—')
        lts = lts.background_gradient(cmap=CMAP, axis=1)
        st.dataframe(lts, use_container_width=True)

        if 'Gap to Leader' in sessao.columns:
            sessao['Position'] = (
                sessao.groupby('Lap')['Gap to Leader'].rank(method='first').astype(int)
            )
            gaps_table = sessao.pivot(index='Position', columns='Lap', values='Gap to Leader').round(3)
            cars_table = sessao.pivot(index='Position', columns='Lap', values='Car_ID')

            final_table = pd.DataFrame(index=[f'P{p}' for p in gaps_table.index])
            for lap in gaps_table.columns:
                try:
                    cars_col = cars_table[lap].astype('Int64').astype(str).replace('<NA>', '')
                except Exception:
                    cars_col = cars_table[lap].apply(lambda x: str(int(x)) if pd.notna(x) else '')
                gaps_col = gaps_table[lap].apply(lambda x: f'{x:.3f}' if pd.notna(x) else '')
                final_table[f'Lap {lap} Car'] = cars_col.values
                final_table[f'Lap {lap} Gap'] = gaps_col.values

            st.subheader('Classification Table (Gap to Leader)')
            st.dataframe(final_table, use_container_width=True)
        else:
            st.info("⚠️ 'Crossing Time' not available. Classification table will not be displayed.")

    # =======================================================================
    elif option == 'Lines':
    # =======================================================================
        prog_tabs   = st.tabs(['Lap Time', 'Sector 1', 'Sector 2', 'Sector 3', 'Speed Trap'])
        prog_cols   = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
        prog_titles = ['Lap Time Progression', 'S1 Time Progression', 'S2 Time Progression',
                       'S3 Time Progression', 'SPT Progression']
        for tab, col, title in zip(prog_tabs, prog_cols, prog_titles):
            with tab:
                st.plotly_chart(px.line(sessao, x='Lap', y=col, color='Driver', title=title))

        raising_configs = [
            ('Lap Tm (S)', True,  'Lap Time Raising Average'),
            ('S1 Tm',      True,  'Sector 1 Raising Average'),
            ('S2 Tm',      True,  'Sector 2 Raising Average'),
            ('S3 Tm',      True,  'Sector 3 Raising Average'),
            ('SPT',        False, 'Speed Trap Raising Average'),
        ]
        ra_tabs = st.tabs(['Lap Time', 'Sector 1', 'Sector 2', 'Sector 3', 'Speed Trap'])
        for tab, (col, ascending, title) in zip(ra_tabs, raising_configs):
            with tab:
                df_plot = sessao_filtrado.copy()
                df_plot['Ranking'] = df_plot.groupby('Driver')[col].rank(ascending=ascending)
                df_plot = df_plot.sort_values(['Driver', 'Ranking'])
                st.plotly_chart(px.line(df_plot, x='Ranking', y=col, color='Driver', title=title))

        delta_tabs = st.tabs(['Last Lap Delta', 'Fast Lap Delta'])
        with delta_tabs[0]:
            st.plotly_chart(px.line(sessao, x='Lap', y='Last Lap Diff', color='Driver', title='Last Lap Difference'))
        with delta_tabs[1]:
            st.plotly_chart(px.line(sessao, x='Lap', y='Fast Lap Diff', color='Driver', title='Fast Lap Delta'))

        gap_tabs = st.tabs(['Gap to Winner', 'Gap to Lap Leader', 'Gap to Reference'])
        with gap_tabs[0]:
            if 'Gap to Winner' in sessao.columns:
                st.plotly_chart(px.line(sessao, x='Lap', y='Gap to Winner', color='Driver', title='Gap to Winner'))
            else:
                st.info("⚠️ 'Crossing Time' not available. Gap to Winner graph will not be displayed.")
        with gap_tabs[1]:
            if 'Gap to Leader' in sessao.columns:
                st.plotly_chart(px.line(sessao, x='Lap', y='Gap to Leader', color='Driver', title='Gap to Leader'))
            else:
                st.info("⚠️ 'Crossing Time' not available. Gap to Leader graph will not be displayed.")
        with gap_tabs[2]:
            if 'Cumulative Crossing' in sessao.columns:
                driver_options = (
                    sessao[['Car_ID', 'Driver']].dropna().drop_duplicates().sort_values('Driver')
                )
                ref_driver = st.selectbox(
                    'Select the reference car:', driver_options['Driver'], key='gap_to_reference_driver',
                )
                ref_car_id  = driver_options.loc[driver_options['Driver'] == ref_driver, 'Car_ID'].iloc[0]
                ref_times   = (
                    sessao[sessao['Car_ID'] == ref_car_id][['Lap', 'Cumulative Crossing']]
                    .rename(columns={'Cumulative Crossing': 'Reference Crossing'})
                )
                gap_ref_df  = sessao.merge(ref_times, on='Lap', how='left')
                gap_ref_df['Gap to Reference'] = gap_ref_df['Cumulative Crossing'] - gap_ref_df['Reference Crossing']
                st.plotly_chart(px.line(
                    gap_ref_df, x='Lap', y='Gap to Reference', color='Driver',
                    title=f'Gap to Reference ({ref_driver})',
                ))
            else:
                st.info("⚠️ 'Crossing Time' not available. Gap to Reference graph will not be displayed.")

        # Position Change chart
        st.subheader('Position Change')
        if 'Gap to Leader' in sessao.columns:
            pos_df = sessao.copy()
            pos_df['Position'] = (
                pos_df.groupby('Lap')['Gap to Leader'].rank(method='first').astype(int)
            )
            fig_pos = px.line(
                pos_df.sort_values(['Driver', 'Lap']),
                x='Lap', y='Position', color='Driver',
                markers=True,
                title='Position Change per Lap',
            )
            fig_pos.update_yaxes(autorange='reversed', title='Position', dtick=1)
            fig_pos.update_xaxes(title='Lap', dtick=1)
            fig_pos.update_traces(marker_size=5)
            fig_pos.update_layout(
                yaxis=dict(tickprefix='P'),
                hovermode='x unified',
            )
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info("⚠️ 'Crossing Time' not available. Position Change chart will not be displayed.")

    # =======================================================================
    elif option == 'Histograms':
    # =======================================================================
        skip_cols = {'Car_ID', 'Driver', 'Team', 'Manufacturer'}
        for var in ANALISE_CARROS:
            if var in skip_cols:
                continue
            st.plotly_chart(px.histogram(sessao_filtrado[var], nbins=25, title=f'{var} distribution'))

    # =======================================================================
    elif option == 'Others':
    # =======================================================================
        st.subheader('Car Efficiency')
        tab1, tab2 = st.tabs(['Fastest Lap per Team', 'Average per Team'])

        with tab1:
            st.markdown('### Fastest Lap per Team')
            fastest_per_team = (
                sessao_filtrado.sort_values('Lap Tm (S)')
                .groupby('Team').first().reset_index()
            )
            st.plotly_chart(_plot_efficiency(fastest_per_team, '(Fastest Lap per Team)'), use_container_width=True)
            st.markdown("""
- **↖ Upper Left** → High overall efficiency (straight + turn)
- **↗ Upper Right** → Low downforce (good straight, bad cornering)
- **↙ Lower Left** → High downforce (good cornering, bad straight)
- **↘ Lower Right** → Low efficiency (neither)
""")

        with tab2:
            st.markdown('### Average per Team')
            avg_per_team = sessao_filtrado.groupby('Team', as_index=False)[['Lap Tm (S)', 'SPT']].mean()
            rep_car      = sessao_filtrado.groupby('Team')['Car_ID'].first().reset_index()
            avg_per_team = avg_per_team.merge(rep_car, on='Team')
            st.plotly_chart(_plot_efficiency(avg_per_team, '(Average per Team)'), use_container_width=True)
            st.markdown("""
- **↗ Upper Right** → High overall efficiency (straight + turn)
- **↖ Upper Left** → Low downforce (good straight, bad cornering)
- **↘ Lower Right** → High downforce (good cornering, bad straight)
- **↙ Lower Left** → Low efficiency (neither)
""")

        sector_tabs_cfg = {
            'Gap to Fastest Car in AVG - Lap': 'Lap Tm (S)',
            'Gap to Fastest Car in AVG - S1':  'S1 Tm',
            'Gap to Fastest Car in AVG - S2':  'S2 Tm',
            'Gap to Fastest Car in AVG - S3':  'S3 Tm',
        }
        tabs = st.tabs(list(sector_tabs_cfg.keys()))
        for tab, (tab_name, coluna) in zip(tabs, sector_tabs_cfg.items()):
            with tab:
                df_avg = sessao_filtrado.groupby('Driver')[coluna].mean().reset_index()
                st.altair_chart(_gap_bar_chart(df_avg, coluna, tab_name), use_container_width=True)

        # -------------------------------------------------------------------
        # Percentual difference — ALL drivers
        # -------------------------------------------------------------------
        st.header('Percentual difference to the best lap — All Drivers')
        tabs_dif = st.tabs(all_drivers)
        for tab, driver_name in zip(tabs_dif, all_drivers):
            with tab:
                df = sessao_filtrado[sessao_filtrado['Driver'] == driver_name].copy()
                if df.empty:
                    st.write('No laps available for this driver after the filter.')
                    continue

                car_id       = df['Car_ID'].iat[0]
                melhor       = df['Lap Tm (S)'].min()
                best_lap_num = df.loc[df['Lap Tm (S)'].idxmin(), 'Lap']
                df['Diff %'] = ((df['Lap Tm (S)'] - melhor) / melhor) * 100
                df = df.sort_values('Lap')
                df['Bloco'] = (df['Lap'].diff().fillna(1) > 1).cumsum()

                bar_color = TEAM_CAR_COLORS.get(car_id, '#636EFA')
                fig = px.bar(
                    df, x='Lap', y='Diff %',
                    text=df['Diff %'].map(lambda x: f'{x:.2f}%'),
                    color_discrete_sequence=[bar_color],
                    title=f'{driver_name} — Diff % by lap',
                )
                fig.update_traces(textposition='outside')
                fig.add_vline(x=best_lap_num, line_dash='dash', line_color='white',
                              annotation_text='Best lap', annotation_position='top')
                for _, bloco in df.groupby('Bloco'):
                    add_trend_line(fig, bloco['Lap'], bloco['Diff %'])
                fig.update_layout(
                    yaxis_title='Difference to best lap (%)',
                    xaxis_title='Lap',
                    uniformtext_minsize=8,
                    uniformtext_mode='show',
                )
                st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'BoxPlots':
    # =======================================================================
        # By manufacturer
        vars_manuf = [c for c in ANALISE_MANUFACTURER if c != 'Manufacturer']
        tabs_manuf = st.tabs(vars_manuf)
        for tab, var in zip(tabs_manuf, vars_manuf):
            with tab:
                fig = px.box(
                    sessao_filtrado, x='Manufacturer', y=var,
                    points='all', color='Manufacturer',
                    title=f'{var} Distribution by Manufacturer',
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # By driver — with driver filter multiselect
        boxplot_cols   = {'Lap': 'Lap Tm (S)', 'S1': 'S1 Tm', 'S2': 'S2 Tm', 'S3': 'S3 Tm', 'SPT': 'SPT'}
        drivers_sorted = sorted(
            [d for d in sessao_filtrado['Driver'].dropna().unique()],
            key=lambda x: str(x),
        )
        tabs_box = st.tabs(list(boxplot_cols.keys()))

        for tab, (tab_nome, coluna) in zip(tabs_box, boxplot_cols.items()):
            with tab:
                selected = st.multiselect(
                    f'Filter drivers — {coluna}',
                    options=drivers_sorted,
                    default=drivers_sorted,
                    key=f'bp_race_{coluna}',
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
    elif option == 'All Laps':
    # =======================================================================
        st.subheader('All Laps by Driver')

        selected_driver = st.selectbox('Choose a driver:', ['All drivers'] + all_drivers)

        if selected_driver == 'All drivers':
            drivers_to_show = all_drivers
        else:
            drivers_to_show = [selected_driver]

        for driver_name in drivers_to_show:
            df_drv = sessao[sessao['Driver'] == driver_name].copy()
            if df_drv.empty:
                continue

            car_id = df_drv['Car_ID'].iat[0]
            team   = df_drv['Team'].iat[0] if 'Team' in df_drv.columns else '—'

            with st.expander(f'🏎️ #{car_id}  {driver_name}  |  {team}', expanded=(selected_driver != 'All drivers')):
                display_cols = [c for c in
                    ['Lap', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Lap Traffic?', 'Gap to Leader', 'Gap to Winner']
                    if c in df_drv.columns]
                st.dataframe(df_drv[display_cols].reset_index(drop=True), use_container_width=True)
