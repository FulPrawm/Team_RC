# Stock_Car_2026_Season_Analysis.py
# Loads ALL rounds of the season and provides season-wide trend analysis.

import os
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

from sc_shared import (
    enrich_session, coerce_numeric_cols, convert_to_seconds,
    highlight_driver, highlight_team, highlight_manufacturer,
    TEAM_CAR_NAMES, TEAM_CAR_COLORS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPORAL_COLS = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
SECTOR_COLS   = ['S1 Tm', 'S2 Tm', 'S3 Tm']
NUM_COLS      = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
CMAP          = 'RdYlGn_r'

# Order matters: longer/more specific prefixes first
SESSION_PREFIXES = {
    'Qualifying Group': ['Q1G'],
    'Qualifying':       ['Q1', 'Q2', 'Q3', 'Q'],
    'Race':             ['R'],
    'Free Practice':    ['TL'],
    'Warm Up':          ['WU'],
    'Shakedown':        ['SD'],
}

def _session_type(filename: str) -> str:
    """Return broad session category from filename."""
    stem = Path(filename).stem
    match = re.search(r'ET\d+_(.+)', stem)
    tag = match.group(1).upper() if match else stem.upper()
    for label, prefixes in SESSION_PREFIXES.items():
        if any(tag.startswith(p) for p in prefixes):
            return label
    return 'Other'

def _round_name(folder_name: str) -> str:
    """ET04_Goiania_I  →  ET04 · Goiânia I"""
    parts = folder_name.split('_', 1)
    if len(parts) == 2:
        return f"{parts[0]} · {parts[1].replace('_', ' ')}"
    return folder_name


# ---------------------------------------------------------------------------
# Data loader — reads every xlsx of every round for the season
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_season(base_dir: Path) -> pd.DataFrame:
    frames = []
    folders = {
        'Race':     base_dir / 'Excel_Files' / 'Races',
        'Practice': base_dir / 'Excel_Files' / 'Practice_And_Qualy',
    }
    for folder_type, root in folders.items():
        if not root.exists():
            continue
        for etapa_dir in sorted(root.iterdir()):
            if not etapa_dir.is_dir():
                continue
            etapa_label = _round_name(etapa_dir.name)
            etapa_order = int(re.search(r'ET(\d+)', etapa_dir.name).group(1)) \
                          if re.search(r'ET(\d+)', etapa_dir.name) else 99
            for f in sorted(etapa_dir.glob('*.xlsx')):
                stype = _session_type(f.name)
                try:
                    df = pd.read_excel(f)
                    df = enrich_session(df)
                    df['Round']        = etapa_label
                    df['Round Order']  = etapa_order
                    df['Round Folder'] = etapa_dir.name
                    df['Session Type'] = stype
                    df['Session File'] = f.stem
                    for col in SECTOR_COLS:
                        df[col] = df[col].apply(convert_to_seconds)
                    df = coerce_numeric_cols(df, TEMPORAL_COLS)
                    frames.append(df)
                except Exception as e:
                    st.warning(f"Could not load {f.name}: {e}")

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values('Round Order')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Season Analysis — 2026')

    BASE_DIR = Path(__file__).resolve().parent

    with st.spinner('Loading full season data…'):
        df_all = _load_season(BASE_DIR)

    if df_all.empty:
        st.error('No season data found.')
        return

    # -----------------------------------------------------------------------
    # Sidebar-style filters (in main area to avoid conflicts with Hub sidebar)
    # -----------------------------------------------------------------------
    st.subheader('🔧 Filters')
    col1, col2, col3 = st.columns(3)

    with col1:
        all_session_types = sorted(df_all['Session Type'].unique())
        selected_types = st.multiselect(
            'Session type:',
            options=all_session_types,
            default=['Race'],
            key='season_session_type',
        )

    with col2:
        all_rounds = df_all['Round'].unique().tolist()
        selected_rounds = st.multiselect(
            'Rounds (leave empty = all):',
            options=all_rounds,
            default=[],
            key='season_rounds',
        )

    with col3:
        all_manufacturers = sorted(df_all['Manufacturer'].dropna().unique())
        selected_manuf = st.multiselect(
            'Manufacturer (leave empty = all):',
            options=all_manufacturers,
            default=[],
            key='season_manuf',
        )

    # Apply filters
    df = df_all.copy()
    if selected_types:
        df = df[df['Session Type'].isin(selected_types)]
    if selected_rounds:
        df = df[df['Round'].isin(selected_rounds)]
    if selected_manuf:
        df = df[df['Manufacturer'].isin(selected_manuf)]

    # B-Pillar filter
    use_bpillar = st.session_state.get('use_bpillar', False)
    if use_bpillar:
        class_fast   = df['Lap Tm (S)'].min()
        class_limit  = class_fast * 1.10
        driver_fast  = df.groupby('Driver')['Lap Tm (S)'].transform('min')
        driver_limit = driver_fast * 1.10
        df = df[(df['Lap Tm (S)'] <= class_limit) & (df['Lap Tm (S)'] <= driver_limit)]
        def _top50(grp):
            t = grp['Lap Tm (S)'].quantile(0.5)
            return grp[grp['Lap Tm (S)'] <= t]
        df = df.groupby('Driver', group_keys=False).apply(_top50).copy()
        st.info('🔵 B-Pillar filter active')

    if df.empty:
        st.warning('No data after filters.')
        return

    rounds_ordered = df.drop_duplicates('Round').sort_values('Round Order')['Round'].tolist()
    st.caption(f"**{len(df):,} laps** across **{df['Round'].nunique()} rounds** and **{df['Driver'].nunique()} drivers**")
    st.divider()

    # -----------------------------------------------------------------------
    # Analysis selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Select analysis:',
        (
            'Season Overview',
            'Driver Evolution',
            'Driver × Track Heatmap',
            'Manufacturer Battle',
            'Track Comparison',
            'Consistency Ranking',
        ),
    )

    # =======================================================================
    if option == 'Season Overview':
    # =======================================================================
        st.subheader('Best lap per driver per round')

        best = (
            df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)'].min()
            .reset_index()
            .sort_values('Round Order')
        )
        pivot = (
            best.pivot(index='Driver', columns='Round', values='Lap Tm (S)')
            [rounds_ordered]  # keep chronological order
        )
        ps = pivot.style.background_gradient(cmap=CMAP, axis=1).format('{:.3f}', na_rep='—')
        st.dataframe(ps, use_container_width=True)

        st.subheader('SPT evolution per round')
        spt_best = (
            df.groupby(['Driver', 'Round', 'Round Order'])['SPT'].max()
            .reset_index().sort_values('Round Order')
        )
        fig_spt = px.line(
            spt_best, x='Round', y='SPT',
            color='Driver', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Max Speed Trap per Round',
        )
        st.plotly_chart(fig_spt, use_container_width=True)

    # =======================================================================
    elif option == 'Driver Evolution':
    # =======================================================================
        st.subheader('Driver lap time evolution across the season')

        all_drivers = sorted(df['Driver'].dropna().unique(), key=str)
        selected    = st.multiselect('Select drivers:', all_drivers, default=all_drivers[:6])
        if not selected:
            st.warning('Select at least one driver.')
            return

        df_drv = df[df['Driver'].isin(selected)]

        best = (
            df_drv.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)'].min()
            .reset_index().sort_values('Round Order')
        )
        fig = px.line(
            best, x='Round', y='Lap Tm (S)',
            color='Driver', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Best Lap Time per Round',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gap to fastest of the round
        st.subheader('Gap to round fastest')
        round_best = df.groupby('Round')['Lap Tm (S)'].min().rename('Round Best')
        best = best.merge(round_best, on='Round')
        best['Gap'] = best['Lap Tm (S)'] - best['Round Best']

        fig2 = px.line(
            best, x='Round', y='Gap',
            color='Driver', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Gap to Round Fastest (s)',
        )
        fig2.add_hline(y=0, line_dash='dash', line_color='white', opacity=0.4)
        st.plotly_chart(fig2, use_container_width=True)

        # Sector evolution tabs
        st.subheader('Sector evolution')
        s_tabs = st.tabs(['S1', 'S2', 'S3'])
        for tab, col in zip(s_tabs, SECTOR_COLS):
            with tab:
                sect = (
                    df_drv.groupby(['Driver', 'Round', 'Round Order'])[col].min()
                    .reset_index().sort_values('Round Order')
                )
                fig_s = px.line(
                    sect, x='Round', y=col,
                    color='Driver', markers=True,
                    category_orders={'Round': rounds_ordered},
                    title=f'{col} Best per Round',
                )
                st.plotly_chart(fig_s, use_container_width=True)

    # =======================================================================
    elif option == 'Driver × Track Heatmap':
    # =======================================================================
        st.subheader('Best lap time — Driver × Track heatmap')

        best = df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)'].min().reset_index()
        pivot = best.pivot(index='Driver', columns='Round', values='Lap Tm (S)')[rounds_ordered]

        # Normalise per track so different circuits are comparable
        normalize = st.checkbox('Normalise per track (% gap to fastest)', value=True)
        if normalize:
            pivot_norm = pivot.apply(lambda col: (col - col.min()) / col.min() * 100)
            fig = px.imshow(
                pivot_norm,
                color_continuous_scale='RdYlGn_r',
                aspect='auto',
                text_auto='.2f',
                title='Gap to Round Fastest (%)',
                labels=dict(color='Gap %'),
            )
        else:
            fig = px.imshow(
                pivot,
                color_continuous_scale='RdYlGn_r',
                aspect='auto',
                text_auto='.3f',
                title='Best Lap Time (s)',
            )

        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'Manufacturer Battle':
    # =======================================================================
        st.subheader('Manufacturer best lap per round')

        manuf_best = (
            df.groupby(['Manufacturer', 'Round', 'Round Order'])['Lap Tm (S)'].min()
            .reset_index().sort_values('Round Order')
        )
        fig = px.line(
            manuf_best, x='Round', y='Lap Tm (S)',
            color='Manufacturer', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Best Lap per Manufacturer per Round',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gap between manufacturers per round
        st.subheader('Gap between manufacturers per round')
        pivot_m = manuf_best.pivot(index='Round', columns='Manufacturer', values='Lap Tm (S)')
        manuf_list = pivot_m.columns.tolist()

        if len(manuf_list) >= 2:
            ref = st.selectbox('Reference manufacturer:', manuf_list, index=0)
            for m in manuf_list:
                if m != ref:
                    pivot_m[f'{m} vs {ref}'] = pivot_m[m] - pivot_m[ref]

            gap_cols = [c for c in pivot_m.columns if ' vs ' in c]
            fig2 = px.line(
                pivot_m[gap_cols].reset_index().melt('Round', var_name='Comparison', value_name='Gap (s)'),
                x='Round', y='Gap (s)', color='Comparison', markers=True,
                category_orders={'Round': rounds_ordered},
                title=f'Lap Time Gap vs {ref} (s)',
            )
            fig2.add_hline(y=0, line_dash='dash', line_color='white', opacity=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        # SPT
        spt_manuf = (
            df.groupby(['Manufacturer', 'Round', 'Round Order'])['SPT'].max()
            .reset_index().sort_values('Round Order')
        )
        fig3 = px.line(
            spt_manuf, x='Round', y='SPT',
            color='Manufacturer', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Max Speed Trap per Manufacturer per Round',
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Win count (rounds where each manufacturer had the best lap)
        winners = manuf_best.loc[manuf_best.groupby('Round')['Lap Tm (S)'].idxmin()]
        win_counts = winners['Manufacturer'].value_counts().reset_index()
        win_counts.columns = ['Manufacturer', 'Rounds with Best Lap']
        fig4 = px.bar(
            win_counts, x='Manufacturer', y='Rounds with Best Lap',
            color='Manufacturer', title='Rounds with Best Lap per Manufacturer',
        )
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    # =======================================================================
    elif option == 'Track Comparison':
    # =======================================================================
        st.subheader('Track comparison — average pace and speed')

        track_stats = (
            df.groupby(['Round', 'Round Order'])
            .agg(
                Best_Lap   = ('Lap Tm (S)', 'min'),
                Avg_Lap    = ('Lap Tm (S)', 'mean'),
                Max_SPT    = ('SPT',        'max'),
                Avg_SPT    = ('SPT',        'mean'),
                Total_Laps = ('Lap Tm (S)', 'count'),
            )
            .reset_index()
            .sort_values('Round Order')
            .rename(columns={'Round': 'Track'})
        )

        tab1, tab2, tab3 = st.tabs(['Lap Time', 'Speed Trap', 'Track Stats Table'])
        with tab1:
            fig = px.bar(
                track_stats, x='Track', y=['Best_Lap', 'Avg_Lap'],
                barmode='group', title='Best vs Average Lap Time per Track',
            )
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            fig2 = px.bar(
                track_stats, x='Track', y=['Max_SPT', 'Avg_SPT'],
                barmode='group', title='Max vs Average SPT per Track',
            )
            st.plotly_chart(fig2, use_container_width=True)
        with tab3:
            fmt = {c: '{:.3f}' for c in ['Best_Lap', 'Avg_Lap', 'Max_SPT', 'Avg_SPT']}
            st.dataframe(
                track_stats.drop(columns='Round Order')
                .style.format(fmt).background_gradient(cmap=CMAP),
                hide_index=True, use_container_width=True,
            )

    # =======================================================================
    elif option == 'Consistency Ranking':
    # =======================================================================
        st.subheader('Consistency ranking — lower std deviation = more consistent')

        min_rounds = st.slider('Minimum rounds with data:', 1, df['Round'].nunique(), 2)

        consistency = (
            df.groupby('Driver')
            .agg(
                Avg_Lap     = ('Lap Tm (S)', 'mean'),
                Std_Lap     = ('Lap Tm (S)', 'std'),
                Best_Lap    = ('Lap Tm (S)', 'min'),
                Rounds      = ('Round',      'nunique'),
                Total_Laps  = ('Lap Tm (S)', 'count'),
            )
            .reset_index()
        )
        consistency = consistency[consistency['Rounds'] >= min_rounds]
        consistency['CV (%)'] = (consistency['Std_Lap'] / consistency['Avg_Lap'] * 100).round(2)
        consistency = consistency.sort_values('CV (%)')

        fig = px.bar(
            consistency, x='Driver', y='CV (%)',
            color='CV (%)', color_continuous_scale='RdYlGn_r',
            title='Coefficient of Variation (%) — lower = more consistent',
            text='CV (%)',
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        # Std per round (who was consistent at each track)
        st.subheader('Consistency per round')
        std_round = (
            df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)']
            .std().reset_index().rename(columns={'Lap Tm (S)': 'Std Dev'})
            .sort_values('Round Order')
        )
        all_drivers = sorted(df['Driver'].dropna().unique(), key=str)
        sel = st.multiselect('Filter drivers:', all_drivers, default=all_drivers[:8], key='cons_drv')
        std_round = std_round[std_round['Driver'].isin(sel)]
        fig2 = px.line(
            std_round, x='Round', y='Std Dev',
            color='Driver', markers=True,
            category_orders={'Round': rounds_ordered},
            title='Lap Time Std Dev per Round (lower = more consistent)',
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Summary table
        fmt = {c: '{:.3f}' for c in ['Avg_Lap', 'Std_Lap', 'Best_Lap']}
        fmt['CV (%)'] = '{:.2f}'
        cs = consistency.style.format(fmt).background_gradient(cmap=CMAP, subset=['CV (%)', 'Std_Lap'])
        st.dataframe(cs, hide_index=True, use_container_width=True)
