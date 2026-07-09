# Stock_Car_2026_Season_Analysis.py
# Season-wide rankings and comparisons across all rounds.

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
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPORAL_COLS = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Avg Speed']
SECTOR_COLS   = ['S1 Tm', 'S2 Tm', 'S3 Tm']
NUM_COLS      = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
CMAP          = 'RdYlGn_r'

# Files to skip (composite qualy — already covered by Q1G1/Q1G2/Q2/Q3)
SKIP_STEMS = {'Q', 'Q1'}

# Session type from filename tag
SESSION_TYPE_MAP = {
    'Q1G': 'Qualifying',
    'Q2':  'Qualifying',
    'Q3':  'Qualifying',
    'R':   'Race',
    'TL':  'Free Practice',
    'WU':  'Warm Up',
    'SD':  'Shakedown',
}

def _session_type(filename: str) -> str:
    stem = Path(filename).stem
    match = re.search(r'ET\d+_(.+)', stem)
    tag = match.group(1).upper() if match else stem.upper()
    for prefix, label in SESSION_TYPE_MAP.items():
        if tag.startswith(prefix):
            return label
    return 'Other'

def _round_label(folder_name: str) -> str:
    parts = folder_name.split('_', 1)
    return f"{parts[0]} · {parts[1].replace('_', ' ')}" if len(parts) == 2 else folder_name

def _round_order(folder_name: str) -> int:
    m = re.search(r'ET(\d+)', folder_name)
    return int(m.group(1)) if m else 99


# ---------------------------------------------------------------------------
# Grid position calculator from Q1G1/Q1G2/Q2/Q3 files
# ---------------------------------------------------------------------------
def _calc_grid(etapa_dir: Path) -> pd.DataFrame:
    """
    Returns a DataFrame with columns [Car_ID, Grid_Position] for the round.
    Logic:
      - Q3 best lap → P1–P8
      - Q2 best lap → P9–P20 (drivers not in Q3)
      - Q1G1 + Q1G2 combined best lap → P21+ (drivers not in Q2/Q3)
    """
    def _best(tag_prefix: list[str]) -> pd.DataFrame:
        frames = []
        for f in sorted(etapa_dir.glob('*.xlsx')):
            stem_tag = re.sub(r'ET\d+_', '', f.stem, flags=re.IGNORECASE).upper()
            if any(stem_tag.startswith(p) for p in tag_prefix):
                try:
                    df = pd.read_excel(f)
                    frames.append(df[['Car_ID', 'Lap Tm (S)']].copy())
                except Exception:
                    pass
        if not frames:
            return pd.DataFrame(columns=['Car_ID', 'Lap Tm (S)'])
        combined = pd.concat(frames, ignore_index=True)
        return combined.groupby('Car_ID')['Lap Tm (S)'].min().reset_index()

    q3 = _best(['Q3'])
    q2 = _best(['Q2'])
    q1 = _best(['Q1G'])

    # Q3: top 8
    q3_sorted = q3.sort_values('Lap Tm (S)').head(8).reset_index(drop=True)
    q3_sorted['Grid_Position'] = range(1, len(q3_sorted) + 1)
    q3_cars = set(q3_sorted['Car_ID'])

    # Q2: next 12 (not already in Q3)
    q2_filtered = q2[~q2['Car_ID'].isin(q3_cars)].sort_values('Lap Tm (S)').head(12).reset_index(drop=True)
    q2_filtered['Grid_Position'] = range(len(q3_sorted) + 1, len(q3_sorted) + len(q2_filtered) + 1)
    q2_cars = set(q2_filtered['Car_ID'])

    # Q1: rest (not in Q2 or Q3), groups combined
    q1_filtered = q1[~q1['Car_ID'].isin(q3_cars | q2_cars)].sort_values('Lap Tm (S)').reset_index(drop=True)
    q1_filtered['Grid_Position'] = range(len(q3_sorted) + len(q2_filtered) + 1,
                                          len(q3_sorted) + len(q2_filtered) + len(q1_filtered) + 1)

    grid = pd.concat([
        q3_sorted[['Car_ID', 'Grid_Position']],
        q2_filtered[['Car_ID', 'Grid_Position']],
        q1_filtered[['Car_ID', 'Grid_Position']],
    ], ignore_index=True)
    return grid


# ---------------------------------------------------------------------------
# Finish position calculator from race file
# ---------------------------------------------------------------------------
def _calc_finish(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns [Car_ID, Finish_Position] sorted by laps completed desc,
    then by last crossing time asc.
    """
    if 'Crossing Time' not in race_df.columns:
        return pd.DataFrame(columns=['Car_ID', 'Finish_Position'])

    race_df = race_df.copy()
    race_df['Crossing Seconds'] = pd.to_timedelta(race_df['Crossing Time']).dt.total_seconds()
    summary = (
        race_df.groupby('Car_ID')
        .agg(MaxLap=('Lap', 'max'), LastCrossing=('Crossing Seconds', 'max'))
        .reset_index()
        .sort_values(['MaxLap', 'LastCrossing'], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary['Finish_Position'] = range(1, len(summary) + 1)
    return summary[['Car_ID', 'Finish_Position']]


# ---------------------------------------------------------------------------
# Season data loader
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_season(base_dir: Path):
    """
    Returns two DataFrames:
      - df_laps: all lap data with Round/Session Type tags
      - df_results: per-round grid + finish positions per driver
    """
    lap_frames    = []
    result_frames = []

    races_root    = base_dir / 'Excel_Files' / 'Races'
    practice_root = base_dir / 'Excel_Files' / 'Practice_And_Qualy'

    all_etapas = sorted(set(
        ([d.name for d in races_root.iterdir() if d.is_dir()]    if races_root.exists()    else []) +
        ([d.name for d in practice_root.iterdir() if d.is_dir()] if practice_root.exists() else [])
    ))

    for etapa_folder in all_etapas:
        round_label = _round_label(etapa_folder)
        round_ord   = _round_order(etapa_folder)

        # --- Lap data (both folders) ---
        for root in [races_root, practice_root]:
            etapa_dir = root / etapa_folder
            if not etapa_dir.exists():
                continue
            for f in sorted(etapa_dir.glob('*.xlsx')):
                stem_tag = re.sub(r'ET\d+_', '', f.stem, flags=re.IGNORECASE)
                if stem_tag.upper() in SKIP_STEMS:
                    continue
                stype = _session_type(f.name)
                try:
                    df = pd.read_excel(f)
                    df = enrich_session(df)
                    df['Round']       = round_label
                    df['Round Order'] = round_ord
                    df['Session Type'] = stype
                    for col in SECTOR_COLS:
                        df[col] = df[col].apply(convert_to_seconds)
                    df = coerce_numeric_cols(df, TEMPORAL_COLS)
                    lap_frames.append(df)
                except Exception as e:
                    st.warning(f"Could not load {f.name}: {e}")

        # --- Grid positions from qualy files ---
        practice_dir = practice_root / etapa_folder
        grid_df = pd.DataFrame(columns=['Car_ID', 'Grid_Position'])
        if practice_dir.exists():
            grid_df = _calc_grid(practice_dir)

        # --- Finish positions from race files ---
        races_dir = races_root / etapa_folder
        if races_dir.exists():
            for f in sorted(races_dir.glob('*.xlsx')):
                stem_tag = re.sub(r'ET\d+_', '', f.stem, flags=re.IGNORECASE).upper()
                if not stem_tag.startswith('R'):
                    continue
                try:
                    race_df  = pd.read_excel(f)
                    race_df  = enrich_session(race_df)
                    finish   = _calc_finish(race_df)
                    race_name = f.stem

                    merged = finish.merge(grid_df, on='Car_ID', how='left')
                    merged['Round']       = round_label
                    merged['Round Order'] = round_ord
                    merged['Race']        = race_name
                    merged['Driver']      = merged['Car_ID'].map(
                        race_df.set_index('Car_ID')['Driver'].to_dict()
                    )
                    merged['Team']        = merged['Car_ID'].map(
                        race_df.set_index('Car_ID')['Team'].to_dict()
                    )
                    merged['Manufacturer'] = merged['Car_ID'].map(
                        race_df.set_index('Car_ID')['Manufacturer'].to_dict()
                    )
                    merged['Positions Gained'] = (
                        merged['Grid_Position'] - merged['Finish_Position']
                    )
                    result_frames.append(merged)
                except Exception as e:
                    st.warning(f"Could not load {f.name}: {e}")

    df_laps    = pd.concat(lap_frames,    ignore_index=True) if lap_frames    else pd.DataFrame()
    df_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()
    return df_laps, df_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _rank_table(df: pd.DataFrame, value_col: str, agg: str, ascending: bool,
                group_col: str = 'Driver', label: str = '') -> pd.DataFrame:
    fn = {'min': 'min', 'max': 'max', 'mean': 'mean'}[agg]
    ranked = (
        getattr(df.groupby(group_col)[value_col], fn)()
        .reset_index()
        .sort_values(value_col, ascending=ascending)
        .reset_index(drop=True)
    )
    ranked.index += 1
    ranked.index.name = 'Rank'
    if label:
        ranked = ranked.rename(columns={value_col: label})
    return ranked


def _styled(df, num_cols, ascending=True):
    fmt = {c: '{:.3f}' for c in num_cols if c in df.columns}
    s = df.style.format(fmt)
    s = s.background_gradient(cmap=CMAP if ascending else 'RdYlGn', subset=[
        c for c in num_cols if c in df.columns
    ])
    return s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Season Analysis — 2026')

    BASE_DIR = Path(__file__).resolve().parent

    with st.spinner('Loading full season data…'):
        df_laps, df_results = _load_season(BASE_DIR)

    if df_laps.empty:
        st.error('No season data found.')
        return

    rounds_ordered = (
        df_laps.drop_duplicates('Round')
        .sort_values('Round Order')['Round'].tolist()
    )

    # -----------------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------------
    st.subheader('🔧 Filters')
    col1, col2, col3 = st.columns(3)
    with col1:
        all_types = sorted(df_laps['Session Type'].unique())
        sel_types = st.multiselect('Session type:', all_types, default=['Race'], key='s_type')
    with col2:
        sel_rounds = st.multiselect('Rounds (empty = all):', rounds_ordered, default=[], key='s_round')
    with col3:
        all_manuf = sorted(df_laps['Manufacturer'].dropna().unique())
        sel_manuf = st.multiselect('Manufacturer (empty = all):', all_manuf, default=[], key='s_manuf')

    df = df_laps.copy()
    if sel_types:
        df = df[df['Session Type'].isin(sel_types)]
    if sel_rounds:
        df = df[df['Round'].isin(sel_rounds)]
    if sel_manuf:
        df = df[df['Manufacturer'].isin(sel_manuf)]

    use_bpillar = st.session_state.get('use_bpillar', False)
    if use_bpillar:
        class_limit  = df['Lap Tm (S)'].min() * 1.10
        driver_fast  = df.groupby('Driver')['Lap Tm (S)'].transform('min')
        df = df[(df['Lap Tm (S)'] <= class_limit) & (df['Lap Tm (S)'] <= driver_fast * 1.10)]
        def _top50(g):
            return g[g['Lap Tm (S)'] <= g['Lap Tm (S)'].quantile(0.5)]
        df = df.groupby('Driver', group_keys=False).apply(_top50).copy()
        st.info('🔵 B-Pillar filter active')

    if df.empty:
        st.warning('No data after filters.')
        return

    st.caption(f"**{len(df):,} laps** · **{df['Round'].nunique()} rounds** · **{df['Driver'].nunique()} drivers**")
    st.divider()

    # -----------------------------------------------------------------------
    # Analysis selector
    # -----------------------------------------------------------------------
    option = st.selectbox('Select analysis:', (
        'Lap Time Ranking',
        'Speed Trap Ranking',
        'Sector Rankings',
        'Consistency Ranking',
        'Race Results & Positions',
        'Driver × Track Heatmap',
        'Manufacturer Battle',
        'Track Comparison',
    ))

    # =======================================================================
    if option == 'Lap Time Ranking':
    # =======================================================================
        st.subheader('Lap Time Rankings')
        tabs = st.tabs(['Best Lap', 'Average Lap', 'Best Lap per Round'])

        with tabs[0]:
            ranked = _rank_table(df, 'Lap Tm (S)', 'min', True, label='Best Lap (s)')
            st.dataframe(_styled(ranked, ['Best Lap (s)']), use_container_width=True)

        with tabs[1]:
            ranked = _rank_table(df, 'Lap Tm (S)', 'mean', True, label='Avg Lap (s)')
            st.dataframe(_styled(ranked, ['Avg Lap (s)']), use_container_width=True)

        with tabs[2]:
            best_per_round = (
                df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)'].min()
                .reset_index().sort_values('Round Order')
            )
            pivot = best_per_round.pivot(index='Driver', columns='Round', values='Lap Tm (S)')[rounds_ordered]
            fmt   = {c: (lambda x: f'{x:.3f}' if isinstance(x, float) and not pd.isna(x) else '—')
                     for c in pivot.columns}
            ps = pivot.style.format(fmt).background_gradient(cmap=CMAP, axis=1)
            st.dataframe(ps, use_container_width=True)

    # =======================================================================
    elif option == 'Speed Trap Ranking':
    # =======================================================================
        st.subheader('Speed Trap Rankings')
        tabs = st.tabs(['Max SPT', 'Average SPT', 'Max SPT per Round'])

        with tabs[0]:
            ranked = _rank_table(df, 'SPT', 'max', False, label='Max SPT (km/h)')
            st.dataframe(_styled(ranked, ['Max SPT (km/h)'], ascending=False), use_container_width=True)

        with tabs[1]:
            ranked = _rank_table(df, 'SPT', 'mean', False, label='Avg SPT (km/h)')
            st.dataframe(_styled(ranked, ['Avg SPT (km/h)'], ascending=False), use_container_width=True)

        with tabs[2]:
            spt_round = (
                df.groupby(['Driver', 'Round', 'Round Order'])['SPT'].max()
                .reset_index().sort_values('Round Order')
            )
            pivot = spt_round.pivot(index='Driver', columns='Round', values='SPT')[rounds_ordered]
            fmt   = {c: (lambda x: f'{x:.1f}' if isinstance(x, float) and not pd.isna(x) else '—')
                     for c in pivot.columns}
            ps = pivot.style.format(fmt).background_gradient(cmap='RdYlGn', axis=1)
            st.dataframe(ps, use_container_width=True)

    # =======================================================================
    elif option == 'Sector Rankings':
    # =======================================================================
        st.subheader('Sector Rankings — Best time per sector')
        tabs = st.tabs(['S1', 'S2', 'S3'])
        for tab, col in zip(tabs, SECTOR_COLS):
            with tab:
                ranked = _rank_table(df, col, 'min', True, label=f'Best {col} (s)')
                st.dataframe(_styled(ranked, [f'Best {col} (s)']), use_container_width=True)

                # Per round
                sect_round = (
                    df.groupby(['Driver', 'Round', 'Round Order'])[col].min()
                    .reset_index().sort_values('Round Order')
                )
                pivot = sect_round.pivot(index='Driver', columns='Round', values=col)
                if rounds_ordered:
                    pivot = pivot[[r for r in rounds_ordered if r in pivot.columns]]
                fmt = {c: (lambda x: f'{x:.3f}' if isinstance(x, float) and not pd.isna(x) else '—')
                       for c in pivot.columns}
                st.dataframe(
                    pivot.style.format(fmt).background_gradient(cmap=CMAP, axis=1),
                    use_container_width=True,
                )

    # =======================================================================
    elif option == 'Consistency Ranking':
    # =======================================================================
        st.subheader('Consistency Ranking — lower CV = more consistent')
        min_rounds = st.slider('Min rounds with data:', 1, max(df['Round'].nunique(), 1), 1)

        cons = (
            df.groupby('Driver').agg(
                Avg_Lap    = ('Lap Tm (S)', 'mean'),
                Std_Lap    = ('Lap Tm (S)', 'std'),
                Best_Lap   = ('Lap Tm (S)', 'min'),
                Rounds     = ('Round',      'nunique'),
                Total_Laps = ('Lap Tm (S)', 'count'),
            ).reset_index()
        )
        cons = cons[cons['Rounds'] >= min_rounds]
        cons['CV (%)'] = (cons['Std_Lap'] / cons['Avg_Lap'] * 100).round(3)
        cons = cons.sort_values('CV (%)').reset_index(drop=True)
        cons.index += 1
        cons.index.name = 'Rank'

        fig = px.bar(
            cons.reset_index(), x='Driver', y='CV (%)',
            color='CV (%)', color_continuous_scale=CMAP,
            title='Coefficient of Variation (%) — lower = more consistent',
            text='CV (%)',
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        fmt = {'Avg_Lap': '{:.3f}', 'Std_Lap': '{:.3f}', 'Best_Lap': '{:.3f}', 'CV (%)': '{:.3f}'}
        cs = cons.style.format(fmt).background_gradient(cmap=CMAP, subset=['CV (%)', 'Std_Lap'])
        st.dataframe(cs, use_container_width=True)

    # =======================================================================
    elif option == 'Race Results & Positions':
    # =======================================================================
        st.subheader('Race Results & Position Rankings')

        if df_results.empty:
            st.warning('No race result data available.')
            return

        res = df_results.copy()
        if sel_rounds:
            res = res[res['Round'].isin(sel_rounds)]

        tabs = st.tabs(['Finish Position Ranking', 'Grid Position Ranking', 'Positions Gained', 'Per Race Results'])

        with tabs[0]:
            st.write('Average finish position across races (lower = better)')
            avg_finish = (
                res.groupby('Driver')['Finish_Position'].mean()
                .reset_index().sort_values('Finish_Position')
                .reset_index(drop=True)
            )
            avg_finish.index += 1
            avg_finish.index.name = 'Rank'
            avg_finish['Finish_Position'] = avg_finish['Finish_Position'].round(2)
            st.dataframe(
                avg_finish.style.format({'Finish_Position': '{:.2f}'})
                .background_gradient(cmap=CMAP, subset=['Finish_Position']),
                use_container_width=True,
            )

        with tabs[1]:
            st.write('Average grid position across races (lower = better)')
            avg_grid = (
                res.dropna(subset=['Grid_Position'])
                .groupby('Driver')['Grid_Position'].mean()
                .reset_index().sort_values('Grid_Position')
                .reset_index(drop=True)
            )
            avg_grid.index += 1
            avg_grid.index.name = 'Rank'
            avg_grid['Grid_Position'] = avg_grid['Grid_Position'].round(2)
            st.dataframe(
                avg_grid.style.format({'Grid_Position': '{:.2f}'})
                .background_gradient(cmap=CMAP, subset=['Grid_Position']),
                use_container_width=True,
            )

        with tabs[2]:
            st.write('Average positions gained per race (positive = gained, negative = lost)')
            avg_gain = (
                res.dropna(subset=['Positions Gained'])
                .groupby('Driver')['Positions Gained'].mean()
                .reset_index().sort_values('Positions Gained', ascending=False)
                .reset_index(drop=True)
            )
            avg_gain.index += 1
            avg_gain.index.name = 'Rank'
            avg_gain['Positions Gained'] = avg_gain['Positions Gained'].round(2)
            fig = px.bar(
                avg_gain.reset_index(), x='Driver', y='Positions Gained',
                color='Positions Gained', color_continuous_scale='RdYlGn',
                title='Avg Positions Gained per Race',
                text='Positions Gained',
            )
            fig.update_traces(texttemplate='%{text:+.1f}', textposition='outside')
            fig.add_hline(y=0, line_dash='dash', line_color='white', opacity=0.4)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(
                avg_gain.style.format({'Positions Gained': '{:+.2f}'})
                .background_gradient(cmap='RdYlGn', subset=['Positions Gained']),
                use_container_width=True,
            )

        with tabs[3]:
            st.write('Full results per race')
            race_options = sorted(res['Race'].unique())
            sel_race = st.selectbox('Choose a race:', race_options)
            race_res = res[res['Race'] == sel_race].sort_values('Finish_Position')
            st.dataframe(
                race_res[['Finish_Position', 'Driver', 'Team', 'Manufacturer', 'Grid_Position', 'Positions Gained']]
                .reset_index(drop=True)
                .style.format({
                    'Finish_Position': '{:.0f}',
                    'Grid_Position':   lambda x: f'{x:.0f}' if pd.notna(x) else '—',
                    'Positions Gained': lambda x: f'{x:+.0f}' if pd.notna(x) else '—',
                })
                .background_gradient(cmap=CMAP, subset=['Finish_Position']),
                use_container_width=True,
                hide_index=True,
            )

    # =======================================================================
    elif option == 'Driver × Track Heatmap':
    # =======================================================================
        st.subheader('Driver × Track — Best Lap Heatmap')
        best = df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)'].min().reset_index()
        pivot = best.pivot(index='Driver', columns='Round', values='Lap Tm (S)')
        pivot = pivot[[r for r in rounds_ordered if r in pivot.columns]]

        normalize = st.checkbox('Show as % gap to round fastest', value=True)
        if normalize:
            pivot_show = pivot.apply(lambda col: (col - col.min()) / col.min() * 100)
            text_fmt   = '.2f'
            color_label = 'Gap %'
        else:
            pivot_show = pivot
            text_fmt   = '.3f'
            color_label = 'Lap (s)'

        fig = px.imshow(
            pivot_show,
            color_continuous_scale=CMAP,
            aspect='auto', text_auto=text_fmt,
            title=f'Driver × Track ({color_label})',
            labels=dict(color=color_label),
        )
        fig.update_layout(height=max(400, len(pivot_show) * 22))
        st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    elif option == 'Manufacturer Battle':
    # =======================================================================
        st.subheader('Manufacturer Battle')
        tabs = st.tabs(['Best Lap per Round', 'Avg Lap per Round', 'SPT per Round', 'Wins'])

        with tabs[0]:
            mb = df.groupby(['Manufacturer', 'Round', 'Round Order'])['Lap Tm (S)'].min().reset_index().sort_values('Round Order')
            st.plotly_chart(px.line(mb, x='Round', y='Lap Tm (S)', color='Manufacturer',
                                    markers=True, category_orders={'Round': rounds_ordered},
                                    title='Best Lap per Manufacturer per Round'), use_container_width=True)
        with tabs[1]:
            ma = df.groupby(['Manufacturer', 'Round', 'Round Order'])['Lap Tm (S)'].mean().reset_index().sort_values('Round Order')
            st.plotly_chart(px.line(ma, x='Round', y='Lap Tm (S)', color='Manufacturer',
                                    markers=True, category_orders={'Round': rounds_ordered},
                                    title='Avg Lap per Manufacturer per Round'), use_container_width=True)
        with tabs[2]:
            ms = df.groupby(['Manufacturer', 'Round', 'Round Order'])['SPT'].max().reset_index().sort_values('Round Order')
            st.plotly_chart(px.line(ms, x='Round', y='SPT', color='Manufacturer',
                                    markers=True, category_orders={'Round': rounds_ordered},
                                    title='Max SPT per Manufacturer per Round'), use_container_width=True)
        with tabs[3]:
            mb2 = df.groupby(['Manufacturer', 'Round', 'Round Order'])['Lap Tm (S)'].min().reset_index()
            winners = mb2.loc[mb2.groupby('Round')['Lap Tm (S)'].idxmin(), 'Manufacturer']
            wc = winners.value_counts().reset_index()
            wc.columns = ['Manufacturer', 'Rounds with Best Lap']
            st.plotly_chart(px.bar(wc, x='Manufacturer', y='Rounds with Best Lap',
                                   color='Manufacturer', title='Rounds with Best Lap per Manufacturer'),
                            use_container_width=True)

    # =======================================================================
    elif option == 'Track Comparison':
    # =======================================================================
        st.subheader('Track Comparison')
        track_stats = (
            df.groupby(['Round', 'Round Order']).agg(
                Best_Lap   = ('Lap Tm (S)', 'min'),
                Avg_Lap    = ('Lap Tm (S)', 'mean'),
                Max_SPT    = ('SPT', 'max'),
                Avg_SPT    = ('SPT', 'mean'),
                Total_Laps = ('Lap Tm (S)', 'count'),
            ).reset_index().sort_values('Round Order').rename(columns={'Round': 'Track'})
        )
        tabs = st.tabs(['Lap Time', 'Speed Trap', 'Table'])
        with tabs[0]:
            st.plotly_chart(px.bar(track_stats, x='Track', y=['Best_Lap', 'Avg_Lap'],
                                   barmode='group', title='Best vs Avg Lap per Track'), use_container_width=True)
        with tabs[1]:
            st.plotly_chart(px.bar(track_stats, x='Track', y=['Max_SPT', 'Avg_SPT'],
                                   barmode='group', title='Max vs Avg SPT per Track'), use_container_width=True)
        with tabs[2]:
            fmt = {c: '{:.3f}' for c in ['Best_Lap', 'Avg_Lap', 'Max_SPT', 'Avg_SPT']}
            st.dataframe(
                track_stats.drop(columns='Round Order').style.format(fmt).background_gradient(cmap=CMAP),
                hide_index=True, use_container_width=True,
            )
