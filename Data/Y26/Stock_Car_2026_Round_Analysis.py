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
FILTRO_PADRAO = 3.0

# Session type tags derived from filename prefixes
# Order matters: longer/more specific prefixes first
# Q and Q1 are excluded — they are composite files already covered by Q1G1/Q1G2/Q2/Q3
SESSION_TYPE_MAP = {
    'Q1G': 'Qualifying Group',
    'Q2':  'Qualifying Q2',
    'Q3':  'Qualifying Q3',
    'R':   'Race',
    'TL':  'Free Practice',
    'WU':  'Warm Up',
    'SD':  'Shakedown',
}

# Files to skip (composite qualifying files already covered by individual sessions)
SKIP_STEMS = {'Q', 'Q1'}  # e.g. ET04_Q, ET04_Q1

# Chronological session order for the weekend
SESSION_ORDER = [
    'Shakedown (SD)',
    'Free Practice (TL1)',
    'Free Practice (TL2)',
    'Qualifying Group (Q1G1)',
    'Qualifying Group (Q1G2)',
    'Qualifying Q2 (Q2)',
    'Qualifying Q3 (Q3)',
    'Warm Up (WU)',
    'Race (R1)',
    'Race (R2)',
]

def _session_sort_key(session_name: str) -> int:
    for i, s in enumerate(SESSION_ORDER):
        if s == session_name:
            return i
    # fallback: extract any trailing number for unknown sessions
    import re
    m = re.search(r'(\d+)$', session_name)
    return 100 + (int(m.group(1)) if m else 0)

def _session_type(filename: str) -> str:
    stem = Path(filename).stem  # e.g. ET04_R1, ET04_TL2, ET04_Q1G1
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
                st.warning(f"Não foi possível carregar {f.name}: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Análise da Etapa')

    BASE_DIR = Path(__file__).resolve().parent

    # Find etapas that exist in at least one of the two folders
    races_dir    = BASE_DIR / 'Excel_Files' / 'Races'
    practice_dir = BASE_DIR / 'Excel_Files' / 'Practice_And_Qualy'
    etapas = sorted(set(
        list(os.listdir(races_dir))    if races_dir.exists()    else [] +
        list(os.listdir(practice_dir)) if practice_dir.exists() else []
    ))
    etapas = [e for e in etapas if (races_dir / e).is_dir() or (practice_dir / e).is_dir()]

    st.subheader('Seletor de Etapa')
    etapa = st.selectbox('Escolha uma etapa:', ['Selecione uma etapa...'] + etapas)
    if etapa == 'Selecione uma etapa...':
        st.warning('Por favor, selecione uma etapa.')
        return

    with st.spinner('Carregando todas as sessões…'):
        df_all = _load_round(BASE_DIR, etapa)

    if df_all.empty:
        st.error('Nenhum dado encontrado para esta etapa.')
        return

    # Sort sessions in chronological weekend order
    all_sess = df_all['Session'].unique().tolist()
    sessions_available = sorted(all_sess, key=_session_sort_key)
    st.success(f"**{len(sessions_available)} sessões** carregadas para **{etapa}**")

    # Optional session filter
    selected_sessions = st.multiselect(
        'Filtrar sessões (vazio = todas):',
        options=sessions_available,
        default=sessions_available,
    )
    if selected_sessions:
        df = df_all[df_all['Session'].isin(selected_sessions)].copy()
    else:
        df = df_all.copy()

    # Filter (always active, main filter)
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

    class_limit  = df['Lap Tm (S)'].min() * (1 + percentual_sessao / 100)
    driver_fast  = df.groupby('Driver')['Lap Tm (S)'].transform('min')
    driver_limit = driver_fast * (1 + percentual_piloto / 100)
    df = df[(df['Lap Tm (S)'] <= class_limit) & (df['Lap Tm (S)'] <= driver_limit)].copy()
    st.write(f"Voltas consideradas: dentro de {percentual_sessao:.1f}% da sessão e {percentual_piloto:.1f}% do piloto")

    if df.empty:
        st.warning('Nenhum dado após os filtros.')
        return

    # -----------------------------------------------------------------------
    # Analysis selector
    # -----------------------------------------------------------------------
    option = st.selectbox(
        'Selecione a análise:',
        ('Visão Geral', 'Comparação de Pilotos', 'Progressão da Sessão', 'Disputa entre Fabricantes', 'Tabela de Melhores Voltas'),
    )

    # =======================================================================
    if option == 'Visão Geral':
    # =======================================================================
        st.subheader('Visão Geral da Etapa — Melhor volta por piloto por sessão')

        _pivot_raw = (
            df.groupby(['Driver', 'Session'])['Lap Tm (S)'].min()
            .unstack('Session')
        )
        # Reorder columns chronologically
        _ordered_cols = [s for s in sessions_available if s in _pivot_raw.columns]
        pivot = _pivot_raw[_ordered_cols].reset_index()
        st.dataframe(
            pivot.style.background_gradient(cmap=CMAP, axis=1)
              .format(lambda x: f'{x:.3f}' if isinstance(x, (int, float)) and not pd.isna(x) else '—'),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader('Distribuição do tempo de volta entre sessões')
        fig = px.box(
            df, x='Session', y='Lap Tm (S)',
            color='Session', points='all',
            category_orders={'Session': sessions_available},
            title='Distribuição do Tempo de Volta por Sessão',
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Speed Trap entre sessões')
        fig2 = px.box(
            df, x='Session', y='SPT',
            color='Session', points='all',
            category_orders={'Session': sessions_available},
            title='Distribuição do Speed Trap por Sessão',
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # =======================================================================
    elif option == 'Comparação de Pilotos':
    # =======================================================================
        st.subheader('Comparação de Pilotos entre sessões')

        DEFAULT_DRIVERS = ['Felipe Fraga', 'Gaetano Di Mauro', 'Sérgio Sette Câmara', 'Zezinho Muggiati']

        all_drivers = sorted(df['Driver'].dropna().unique().tolist(), key=str)
        selected = st.multiselect(
            'Selecione os pilotos:',
            options=all_drivers,
            default=[d for d in DEFAULT_DRIVERS if d in all_drivers],
        )
        if not selected:
            st.warning('Selecione ao menos um piloto.')
            return

        df_drv = df[df['Driver'].isin(selected)]

        # Best lap per session per driver
        best = df_drv.groupby(['Driver', 'Session'])['Lap Tm (S)'].min().reset_index()
        best['Session'] = pd.Categorical(best['Session'], categories=sessions_available, ordered=True)
        best = best.sort_values('Session')
        fig  = px.line(
            best, x='Session', y='Lap Tm (S)',
            color='Driver', markers=True,
            category_orders={'Session': sessions_available},
            title='Melhor Tempo de Volta por Sessão',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Sector breakdown heatmap
        st.subheader('Melhores setores por piloto (todas as sessões combinadas)')
        sect = df_drv.groupby('Driver')[SECTOR_COLS].min().reset_index()
        for col in SECTOR_COLS:
            sect[col] -= sect[col].min()  # gap to fastest
        fig_h = px.imshow(
            sect.set_index('Driver')[SECTOR_COLS],
            color_continuous_scale='Turbo',
            aspect='auto', text_auto='.3f',
            title='Gap para o Melhor por Setor (s)',
        )
        st.plotly_chart(fig_h, use_container_width=True)

        # SPT comparison
        spt = df_drv.groupby(['Driver', 'Session'])['SPT'].max().reset_index()
        spt['Session'] = pd.Categorical(spt['Session'], categories=sessions_available, ordered=True)
        spt = spt.sort_values('Session')
        fig3 = px.bar(
            spt, x='Driver', y='SPT', color='Session',
            barmode='group',
            category_orders={'Session': sessions_available},
            title='Speed Trap Máximo por Sessão',
        )
        st.plotly_chart(fig3, use_container_width=True)

    # =======================================================================
    elif option == 'Progressão da Sessão':
    # =======================================================================
        st.subheader('Como os pilotos evoluíram volta a volta em cada sessão')

        session_choice = st.selectbox('Escolha a sessão:', sessions_available)
        df_sess = df[df['Session'] == session_choice]

        all_drivers = sorted(df_sess['Driver'].dropna().unique().tolist(), key=str)
        selected    = st.multiselect('Filtrar pilotos:', all_drivers, default=all_drivers)
        df_sess     = df_sess[df_sess['Driver'].isin(selected)]

        tabs = st.tabs(['Tempo de Volta', 'S1', 'S2', 'S3', 'SPT'])
        cols = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
        for tab, col in zip(tabs, cols):
            with tab:
                fig = px.line(df_sess.sort_values('Lap'), x='Lap', y=col,
                              color='Driver', markers=True, title=f'{col} — {session_choice}')
                st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'Disputa entre Fabricantes':
    # =======================================================================
        st.subheader('Disputa entre Fabricantes — média da melhor volta por sessão')

        manuf_best = (
            df.groupby(['Manufacturer', 'Session'])['Lap Tm (S)'].min()
            .reset_index()
        )
        manuf_best['Session'] = pd.Categorical(manuf_best['Session'], categories=sessions_available, ordered=True)
        manuf_best = manuf_best.sort_values('Session')
        fig = px.line(
            manuf_best, x='Session', y='Lap Tm (S)',
            color='Manufacturer', markers=True,
            category_orders={'Session': sessions_available},
            title='Melhor Volta por Fabricante por Sessão',
        )
        st.plotly_chart(fig, use_container_width=True)

        # Average across all sessions
        manuf_avg = df.groupby('Manufacturer')[NUM_COLS].mean(numeric_only=True).reset_index()
        fmt = {c: '{:.3f}' for c in NUM_COLS if c in manuf_avg.columns}
        ms  = manuf_avg.style.format(fmt)
        ms  = ms.background_gradient(cmap=CMAP)
        ms  = ms.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.subheader('Média entre todas as sessões')
        st.dataframe(ms, hide_index=True, use_container_width=True)

    # =======================================================================
    elif option == 'Tabela de Melhores Voltas':
    # =======================================================================
        st.subheader('Melhor volta de cada piloto em cada sessão')

        best_all = (
            df.groupby(['Driver', 'Team', 'Manufacturer', 'Session'])['Lap Tm (S)'].min()
            .reset_index()
            .sort_values(['Session', 'Lap Tm (S)'])
            .assign(Session=lambda d: pd.Categorical(d['Session'], categories=sessions_available, ordered=True))
        )
        fmt = {'Lap Tm (S)': '{:.3f}'}
        bs  = best_all.style.format(fmt)
        bs  = bs.background_gradient(cmap=CMAP, subset=['Lap Tm (S)'])
        bs  = bs.apply(highlight_driver,       subset=['Driver'])
        bs  = bs.apply(highlight_team,         subset=['Team'])
        bs  = bs.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(bs, hide_index=True, use_container_width=True)
