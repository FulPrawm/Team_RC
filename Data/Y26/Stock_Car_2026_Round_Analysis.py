# Stock_Car_2026_Round_Analysis.py
# Loads ALL sessions of a chosen round (races + practice/qualy) and
# provides cross-session comparisons.

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
NUM_COLS      = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
CMAP          = 'RdYlGn_r'

# Session type tags derived from filename prefixes
# Order matters: longer/more specific prefixes first
SESSION_TYPE_MAP = {
    'Q1G': 'Qualifying Group',
    'Q1':  'Qualifying Q1',
    'Q2':  'Qualifying Q2',
    'Q3':  'Qualifying Q3',
    'Q':   'Qualifying (Full)',
    'R':   'Race',
    'TL':  'Free Practice',
    'WU':  'Warm Up',
    'SD':  'Shakedown',
}

def _session_type(filename: str) -> str:
    stem = Path(filename).stem  # e.g. ET04_R1, ET04_TL2, ET04_Q1G1
    # Extract the part after ETxx_
    match = re.search(r'ET\d+_(.+)', stem)
    if not match:
        return stem
    tag = match.group(1)
    for prefix, label in SESSION_TYPE_MAP.items():
        if tag.upper().startswith(prefix):
            return f"{label} ({tag})"
    return tag


# ---------------------------------------------------------------------------
# Data loader — reads all xlsx from both Races and Practice folders for a round
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_round(base_dir: Path, etapa: str) -> pd.DataFrame:
    """Load and tag every session file for the chosen round."""
    frames = []
    folders = {
        'Race':     base_dir / 'Excel_Files' / 'Races'             / etapa,
        'Practice': base_dir / 'Excel_Files' / 'Practice_And_Qualy' / etapa,
    }
    for folder_type, folder in folders.items():
        if not folder.exists():
            continue
        for f in sorted(folder.glob('*.xlsx')):
            try:
                df = pd.read_excel(f)
                df = enrich_session(df)
                df['Session']      = _session_type(f.name)
                df['Session File'] = f.stem
                df['Folder Type']  = folder_type
                for col in SECTOR_COLS:
                    df[col] = df[col].apply(convert_to_seconds)
                df = coerce_numeric_cols(df, TEMPORAL_COLS)
                frames.append(df)
            except Exception as e:
                st.warning(f"Could not load {f.name}: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Round Analysis')

    BASE_DIR = Path(__file__).resolve().parent

    # Find etapas that exist in at least one of the two folders
    races_dir    = BASE_DIR / 'Excel_Files' / 'Races'
    practice_dir = BASE_DIR / 'Excel_Files' / 'Practice_And_Qualy'
    etapas = sorted(set(
        list(os.listdir(races_dir))    if races_dir.exists()    else [] +
        list(os.listdir(practice_dir)) if practice_dir.exists() else []
    ))
    etapas = [e for e in etapas if (races_dir / e).is_dir() or (practice_dir / e).is_dir()]

    st.subheader('Round Selector')
    etapa = st.selectbox('Choose a round:', ['Select a round...'] + etapas)
    if etapa == 'Select a round...':
        st.warning('Please select a round.')
        return

    with st.spinner('Loading all sessions…'):
        df_all = _load_round(BASE_DIR, etapa)

    if df_all.empty:
        st.error('No data found for this round.')
        return

    sessions_available = sorted(df_all['Session'].unique())
    st.success(f"Loaded **{len(sessions_available)} sessions** for **{etapa}**")

    # Optional session filter
    selected_sessions = st.multiselect(
        'Filter sessions (leave empty = all):',
        options=sessions_available,
        default=sessions_available,
    )
    if selected_sessions:
        df = df_all[df_all['Session'].isin(selected_sessions)].copy()
    else:
        df = df_all.copy()

    # B-Pillar filter toggle (reads from Hub if available)
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

    # -----------------------------------------------------------------------
    # Analysis selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Select analysis:',
        ('Overview', 'Driver Comparison', 'Session Progression', 'Manufacturer Battle', 'Best Laps Table'),
    )

    # =======================================================================
    if option == 'Overview':
    # =======================================================================
        st.subheader('Round Overview — Best lap per driver per session')

        pivot = (
            df.groupby(['Driver', 'Session'])['Lap Tm (S)'].min()
            .unstack('Session')
            .reset_index()
        )
        st.dataframe(
            pivot.style.background_gradient(cmap=CMAP, axis=1).format('{:.3f}', na_rep='—'),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader('Lap time distribution across sessions')
        fig = px.box(
            df, x='Session', y='Lap Tm (S)',
            color='Session', points='all',
            title='Lap Time Distribution per Session',
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Speed Trap across sessions')
        fig2 = px.box(
            df, x='Session', y='SPT',
            color='Session', points='all',
            title='Speed Trap Distribution per Session',
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # =======================================================================
    elif option == 'Driver Comparison':
    # =======================================================================
        st.subheader('Driver Comparison across sessions')

        all_drivers = sorted(df['Driver'].dropna().unique().tolist(), key=str)
        selected    = st.multiselect('Select drivers:', all_drivers, default=all_drivers[:6])
        if not selected:
            st.warning('Select at least one driver.')
            return

        df_drv = df[df['Driver'].isin(selected)]

        # Best lap per session per driver
        best = df_drv.groupby(['Driver', 'Session'])['Lap Tm (S)'].min().reset_index()
        fig  = px.line(
            best, x='Session', y='Lap Tm (S)',
            color='Driver', markers=True,
            title='Best Lap Time per Session',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Sector breakdown heatmap
        st.subheader('Best sectors per driver (all sessions combined)')
        sect = df_drv.groupby('Driver')[SECTOR_COLS].min().reset_index()
        for col in SECTOR_COLS:
            sect[col] -= sect[col].min()  # gap to fastest
        fig_h = px.imshow(
            sect.set_index('Driver')[SECTOR_COLS],
            color_continuous_scale='Turbo',
            aspect='auto', text_auto='.3f',
            title='Sector Gap to Best (s)',
        )
        st.plotly_chart(fig_h, use_container_width=True)

        # SPT comparison
        spt = df_drv.groupby(['Driver', 'Session'])['SPT'].max().reset_index()
        fig3 = px.bar(
            spt, x='Driver', y='SPT', color='Session',
            barmode='group', title='Max Speed Trap per Session',
        )
        st.plotly_chart(fig3, use_container_width=True)

    # =======================================================================
    elif option == 'Session Progression':
    # =======================================================================
        st.subheader('How drivers evolved lap-by-lap within each session')

        session_choice = st.selectbox('Choose session:', sessions_available)
        df_sess = df[df['Session'] == session_choice]

        all_drivers = sorted(df_sess['Driver'].dropna().unique().tolist(), key=str)
        selected    = st.multiselect('Filter drivers:', all_drivers, default=all_drivers)
        df_sess     = df_sess[df_sess['Driver'].isin(selected)]

        tabs = st.tabs(['Lap Time', 'S1', 'S2', 'S3', 'SPT'])
        cols = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
        for tab, col in zip(tabs, cols):
            with tab:
                fig = px.line(df_sess.sort_values('Lap'), x='Lap', y=col,
                              color='Driver', markers=True, title=f'{col} — {session_choice}')
                st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'Manufacturer Battle':
    # =======================================================================
        st.subheader('Manufacturer Battle — average best lap per session')

        manuf_best = (
            df.groupby(['Manufacturer', 'Session'])['Lap Tm (S)'].min()
            .reset_index()
        )
        fig = px.line(
            manuf_best, x='Session', y='Lap Tm (S)',
            color='Manufacturer', markers=True,
            title='Best Lap per Manufacturer per Session',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Average across all sessions
        manuf_avg = df.groupby('Manufacturer')[NUM_COLS].mean(numeric_only=True).reset_index()
        fmt = {c: '{:.3f}' for c in NUM_COLS if c in manuf_avg.columns}
        ms  = manuf_avg.style.format(fmt)
        ms  = ms.background_gradient(cmap=CMAP)
        ms  = ms.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.subheader('Average across all sessions')
        st.dataframe(ms, hide_index=True, use_container_width=True)

    # =======================================================================
    elif option == 'Best Laps Table':
    # =======================================================================
        st.subheader('Best lap of each driver in each session')

        best_all = (
            df.groupby(['Driver', 'Team', 'Manufacturer', 'Session'])['Lap Tm (S)'].min()
            .reset_index()
            .sort_values(['Session', 'Lap Tm (S)'])
        )
        fmt = {'Lap Tm (S)': '{:.3f}'}
        bs  = best_all.style.format(fmt)
        bs  = bs.background_gradient(cmap=CMAP, subset=['Lap Tm (S)'])
        bs  = bs.apply(highlight_driver,       subset=['Driver'])
        bs  = bs.apply(highlight_team,         subset=['Team'])
        bs  = bs.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(bs, hide_index=True, use_container_width=True)
