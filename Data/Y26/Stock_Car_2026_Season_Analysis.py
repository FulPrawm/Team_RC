# Stock_Car_2026_Season_Analysis.py
import os
import re
import numpy as np
import pandas as pd
import plotly.express as px
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
CMAP          = 'RdYlGn_r'
SKIP_STEMS    = {'Q', 'Q1'}


def _round_label(folder: str) -> str:
    parts = folder.split('_', 1)
    return f"{parts[0]} · {parts[1].replace('_', ' ')}" if len(parts) == 2 else folder

def _round_order(folder: str) -> int:
    m = re.search(r'ET(\d+)', folder)
    return int(m.group(1)) if m else 99

def _stem_tag(filename: str) -> str:
    return re.sub(r'ET\d+_', '', Path(filename).stem, flags=re.IGNORECASE).upper()


# ---------------------------------------------------------------------------
# Grid calculators
# ---------------------------------------------------------------------------
def _qualy_order(practice_dir: Path) -> pd.DataFrame:
    """Best lap per driver from Q1G*/Q2/Q3, returns sorted DataFrame with qualy positions."""
    def _best(prefixes):
        frames = []
        for f in sorted(practice_dir.glob('*.xlsx')):
            tag = _stem_tag(f.name)
            if tag in SKIP_STEMS:
                continue
            if any(tag.startswith(p) for p in prefixes):
                try:
                    df = pd.read_excel(f)[['Car_ID', 'Lap Tm (S)']]
                    frames.append(df)
                except Exception:
                    pass
        if not frames:
            return pd.DataFrame(columns=['Car_ID', 'Lap Tm (S)'])
        return pd.concat(frames).groupby('Car_ID')['Lap Tm (S)'].min().reset_index()

    q3 = _best(['Q3'])
    q2 = _best(['Q2'])
    q1 = _best(['Q1G'])

    q3s = q3.sort_values('Lap Tm (S)').head(8).reset_index(drop=True)
    q3s['Qualy_Pos'] = range(1, len(q3s) + 1)
    q3_cars = set(q3s['Car_ID'])

    q2f = q2[~q2['Car_ID'].isin(q3_cars)].sort_values('Lap Tm (S)').head(12).reset_index(drop=True)
    q2f['Qualy_Pos'] = range(len(q3s) + 1, len(q3s) + len(q2f) + 1)
    q2_cars = set(q2f['Car_ID'])

    q1f = q1[~q1['Car_ID'].isin(q3_cars | q2_cars)].sort_values('Lap Tm (S)').reset_index(drop=True)
    q1f['Qualy_Pos'] = range(len(q3s) + len(q2f) + 1, len(q3s) + len(q2f) + len(q1f) + 1)

    return pd.concat([q3s, q2f, q1f], ignore_index=True)[['Car_ID', 'Qualy_Pos']]


def _r1_grid(qualy: pd.DataFrame) -> pd.DataFrame:
    """R1 grid: invert top 12, keep 13+ in qualy order."""
    df = qualy.copy().sort_values('Qualy_Pos').reset_index(drop=True)
    top12 = df[df['Qualy_Pos'] <= 12].copy()
    rest  = df[df['Qualy_Pos'] > 12].copy()
    top12['Grid_Pos'] = top12['Qualy_Pos'].apply(lambda p: 13 - p)  # 1↔12, 2↔11, ...
    rest['Grid_Pos']  = rest['Qualy_Pos']
    return pd.concat([top12, rest])[['Car_ID', 'Grid_Pos']]


def _r2_grid(qualy: pd.DataFrame, r1_finish: pd.DataFrame) -> pd.DataFrame:
    """
    R2 grid:
    - P1–P12: qualy order directly
    - P13+: reordered by R1 finish position (among those who qualified 13th or worse)
    """
    top12 = qualy[qualy['Qualy_Pos'] <= 12].copy()
    top12['Grid_Pos'] = top12['Qualy_Pos']

    back_cars = set(qualy[qualy['Qualy_Pos'] > 12]['Car_ID'])
    back_r1 = (
        r1_finish[r1_finish['Car_ID'].isin(back_cars)]
        .sort_values('Finish_Pos')
        .reset_index(drop=True)
    )
    back_r1['Grid_Pos'] = range(13, 13 + len(back_r1))

    # Cars that qualified 13+ but didn't finish R1 go to the back
    missing = qualy[qualy['Qualy_Pos'] > 12 & ~qualy['Car_ID'].isin(back_r1['Car_ID'])].copy()
    if not missing.empty:
        missing['Grid_Pos'] = range(13 + len(back_r1), 13 + len(back_r1) + len(missing))
        back_r1 = pd.concat([back_r1[['Car_ID', 'Grid_Pos']], missing[['Car_ID', 'Grid_Pos']]])

    return pd.concat([top12[['Car_ID', 'Grid_Pos']], back_r1[['Car_ID', 'Grid_Pos']]], ignore_index=True)


def _finish_order(race_df: pd.DataFrame) -> pd.DataFrame:
    """Finish position from crossing time."""
    if 'Crossing Time' not in race_df.columns:
        return pd.DataFrame(columns=['Car_ID', 'Finish_Pos'])
    df = race_df.copy()
    df['_cs'] = pd.to_timedelta(df['Crossing Time']).dt.total_seconds()
    summary = (
        df.groupby('Car_ID').agg(MaxLap=('Lap', 'max'), LastCS=('_cs', 'max'))
        .sort_values(['MaxLap', 'LastCS'], ascending=[False, True])
        .reset_index()
    )
    summary['Finish_Pos'] = range(1, len(summary) + 1)
    return summary[['Car_ID', 'Finish_Pos']]


# ---------------------------------------------------------------------------
# Season loader
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_season(base_dir: Path):
    races_root    = base_dir / 'Excel_Files' / 'Races'
    practice_root = base_dir / 'Excel_Files' / 'Practice_And_Qualy'

    all_etapas = sorted(set(
        ([d.name for d in races_root.iterdir()    if d.is_dir()] if races_root.exists()    else []) +
        ([d.name for d in practice_root.iterdir() if d.is_dir()] if practice_root.exists() else [])
    ))

    lap_frames    = []
    result_frames = []

    for etapa_folder in all_etapas:
        rlabel = _round_label(etapa_folder)
        rorder = _round_order(etapa_folder)
        practice_dir = practice_root / etapa_folder
        races_dir    = races_root    / etapa_folder

        # --- Lap data ---
        for root in [races_root, practice_root]:
            d = root / etapa_folder
            if not d.exists():
                continue
            for f in sorted(d.glob('*.xlsx')):
                tag = _stem_tag(f.name)
                if tag in SKIP_STEMS:
                    continue
                # Determine session type
                if tag.startswith('R'):
                    stype = 'Race'
                elif tag.startswith('TL'):
                    stype = 'Free Practice'
                elif tag.startswith('WU'):
                    stype = 'Warm Up'
                elif tag.startswith('SD'):
                    stype = 'Shakedown'
                elif any(tag.startswith(p) for p in ['Q1G', 'Q2', 'Q3']):
                    stype = 'Qualifying'
                else:
                    stype = 'Other'
                try:
                    df = pd.read_excel(f)
                    df = enrich_session(df)
                    df['Round']        = rlabel
                    df['Round Order']  = rorder
                    df['Session Type'] = stype
                    for col in SECTOR_COLS:
                        df[col] = df[col].apply(convert_to_seconds)
                    df = coerce_numeric_cols(df, TEMPORAL_COLS)
                    lap_frames.append(df)
                except Exception as e:
                    st.warning(f"Could not load {f.name}: {e}")

        # --- Race results with correct grids ---
        if not races_dir.exists() or not practice_dir.exists():
            continue

        qualy = _qualy_order(practice_dir)
        if qualy.empty:
            continue

        r1_file = races_dir / next(
            (f.name for f in sorted(races_dir.glob('*.xlsx')) if _stem_tag(f.name) == 'R1'), ''
        ) if any(_stem_tag(f.name) == 'R1' for f in races_dir.glob('*.xlsx')) else None

        r2_file = races_dir / next(
            (f.name for f in sorted(races_dir.glob('*.xlsx')) if _stem_tag(f.name) == 'R2'), ''
        ) if any(_stem_tag(f.name) == 'R2' for f in races_dir.glob('*.xlsx')) else None

        r1_finish = pd.DataFrame(columns=['Car_ID', 'Finish_Pos'])

        for race_file, race_name, get_grid in [
            (r1_file, 'R1', lambda _: _r1_grid(qualy)),
            (r2_file, 'R2', lambda r1f: _r2_grid(qualy, r1f)),
        ]:
            if race_file is None or not race_file.exists():
                continue
            try:
                race_df = pd.read_excel(race_file)
                race_df = enrich_session(race_df)
                finish  = _finish_order(race_df)
                grid    = get_grid(r1_finish)

                if race_name == 'R1':
                    r1_finish = finish.copy()

                merged = finish.merge(grid, on='Car_ID', how='left')
                merged['Positions Gained'] = merged['Grid_Pos'] - merged['Finish_Pos']
                merged['Round']       = rlabel
                merged['Round Order'] = rorder
                merged['Race']        = race_name
                # Add driver/team/manufacturer
                for col, src in [('Driver', 'Driver'), ('Team', 'Team'), ('Manufacturer', 'Manufacturer')]:
                    merged[col] = merged['Car_ID'].map(
                        race_df.drop_duplicates('Car_ID').set_index('Car_ID')[src].to_dict()
                    )
                result_frames.append(merged)
            except Exception as e:
                st.warning(f"Could not process {race_file.name}: {e}")

    df_laps    = pd.concat(lap_frames,    ignore_index=True) if lap_frames    else pd.DataFrame()
    df_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()
    return df_laps, df_results


# ---------------------------------------------------------------------------
# Ranking helper: rank per round, then average the ranks
# ---------------------------------------------------------------------------
def _rank_of_ranks(df: pd.DataFrame, value_col: str, agg_fn: str,
                   ascending: bool, group_col: str = 'Driver') -> pd.DataFrame:
    """
    For each round, rank drivers by agg_fn(value_col).
    Then average those ranks across rounds → final ranking.
    """
    per_round = (
        df.groupby([group_col, 'Round', 'Round Order'])[value_col]
        .agg(agg_fn)
        .reset_index()
    )
    per_round['Round Rank'] = (
        per_round.groupby('Round')[value_col]
        .rank(ascending=ascending, method='min')
    )
    final = (
        per_round.groupby(group_col)
        .agg(
            Avg_Rank   = ('Round Rank', 'mean'),
            Rounds     = ('Round',      'nunique'),
        )
        .reset_index()
        .sort_values('Avg_Rank')
        .reset_index(drop=True)
    )
    final.index += 1
    final.index.name = 'Final Rank'
    final['Avg_Rank'] = final['Avg_Rank'].round(2)

    # Also attach the per-round pivot for detail
    pivot = per_round.pivot(index=group_col, columns='Round', values='Round Rank')
    return final, pivot


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
        df_laps.drop_duplicates('Round').sort_values('Round Order')['Round'].tolist()
    )

    # -----------------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------------
    st.subheader('🔧 Filters')
    c1, c2 = st.columns(2)
    with c1:
        all_types  = sorted(df_laps['Session Type'].unique())
        sel_types  = st.multiselect('Session type:', all_types, default=['Race'], key='s_type')
    with c2:
        sel_rounds = st.multiselect('Rounds (empty = all):', rounds_ordered, default=[], key='s_round')

    df = df_laps.copy()
    if sel_types:
        df = df[df['Session Type'].isin(sel_types)]
    if sel_rounds:
        df = df[df['Round'].isin(sel_rounds)]
        rounds_ordered = [r for r in rounds_ordered if r in sel_rounds]

    use_bpillar = st.session_state.get('use_bpillar', False)
    if use_bpillar:
        class_limit = df['Lap Tm (S)'].min() * 1.10
        drv_fast    = df.groupby('Driver')['Lap Tm (S)'].transform('min')
        df = df[(df['Lap Tm (S)'] <= class_limit) & (df['Lap Tm (S)'] <= drv_fast * 1.10)]
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
    ))

    def _show_rank_table(final, pivot, rounds_ordered, value_label, ascending=True):
        """Show final ranking + per-round rank pivot."""
        st.dataframe(
            final.style.format({'Avg_Rank': '{:.2f}'})
            .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
            use_container_width=True,
        )
        st.caption('Per-round rank detail (1 = best in that round)')
        pivot_show = pivot[[r for r in rounds_ordered if r in pivot.columns]]
        fmt = {c: (lambda x: f'{x:.0f}' if pd.notna(x) else '—') for c in pivot_show.columns}
        st.dataframe(
            pivot_show.style.format(fmt)
            .background_gradient(cmap=CMAP if ascending else 'RdYlGn', axis=1),
            use_container_width=True,
        )

    # =======================================================================
    if option == 'Lap Time Ranking':
    # =======================================================================
        st.subheader('Lap Time Ranking — rank of ranks across rounds')
        tabs = st.tabs(['Best Lap', 'Average Lap'])

        with tabs[0]:
            st.write('Each driver is ranked by best lap **within each round**, then those ranks are averaged.')
            final, pivot = _rank_of_ranks(df, 'Lap Tm (S)', 'min', ascending=True)
            _show_rank_table(final, pivot, rounds_ordered, 'Best Lap')

        with tabs[1]:
            st.write('Each driver is ranked by average lap **within each round**, then those ranks are averaged.')
            final, pivot = _rank_of_ranks(df, 'Lap Tm (S)', 'mean', ascending=True)
            _show_rank_table(final, pivot, rounds_ordered, 'Avg Lap')

    # =======================================================================
    elif option == 'Speed Trap Ranking':
    # =======================================================================
        st.subheader('Speed Trap Ranking — rank of ranks across rounds')
        tabs = st.tabs(['Max SPT', 'Average SPT'])

        with tabs[0]:
            final, pivot = _rank_of_ranks(df, 'SPT', 'max', ascending=False)
            _show_rank_table(final, pivot, rounds_ordered, 'Max SPT', ascending=False)

        with tabs[1]:
            final, pivot = _rank_of_ranks(df, 'SPT', 'mean', ascending=False)
            _show_rank_table(final, pivot, rounds_ordered, 'Avg SPT', ascending=False)

    # =======================================================================
    elif option == 'Sector Rankings':
    # =======================================================================
        st.subheader('Sector Rankings — rank of ranks across rounds')
        tabs = st.tabs(['S1', 'S2', 'S3'])
        for tab, col in zip(tabs, SECTOR_COLS):
            with tab:
                final, pivot = _rank_of_ranks(df, col, 'min', ascending=True)
                _show_rank_table(final, pivot, rounds_ordered, col)

    # =======================================================================
    elif option == 'Consistency Ranking':
    # =======================================================================
        st.subheader('Consistency Ranking — rank of std deviation per round, then averaged')
        st.write('Lower CV within each round = more consistent. Ranks are averaged across rounds.')

        # Std dev per driver per round, then rank within round
        std_per_round = (
            df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)']
            .std().reset_index().rename(columns={'Lap Tm (S)': 'Std'})
        )
        std_per_round['Round Rank'] = (
            std_per_round.groupby('Round')['Std'].rank(ascending=True, method='min')
        )
        final = (
            std_per_round.groupby('Driver')
            .agg(Avg_Rank=('Round Rank', 'mean'), Rounds=('Round', 'nunique'))
            .reset_index()
            .sort_values('Avg_Rank')
            .reset_index(drop=True)
        )
        final.index += 1
        final.index.name = 'Final Rank'
        final['Avg_Rank'] = final['Avg_Rank'].round(2)

        pivot = std_per_round.pivot(index='Driver', columns='Round', values='Round Rank')

        fig = px.bar(
            final.reset_index(), x='Driver', y='Avg_Rank',
            color='Avg_Rank', color_continuous_scale=CMAP,
            title='Average Consistency Rank (lower = more consistent)',
            text='Avg_Rank',
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        _show_rank_table(final, pivot, rounds_ordered, 'Std Dev')

    # =======================================================================
    elif option == 'Race Results & Positions':
    # =======================================================================
        st.subheader('Race Results & Position Rankings')

        if df_results.empty:
            st.warning('No race result data available yet.')
            return

        res = df_results.copy()
        if sel_rounds:
            res = res[res['Round'].isin(sel_rounds)]

        tabs = st.tabs(['Finish Position Ranking', 'Grid Position Ranking',
                        'Positions Gained', 'Per Race Results'])

        with tabs[0]:
            st.write('Rank of ranks: each driver ranked by finish position per race, then averaged.')
            fp = (
                res.groupby(['Driver', 'Round', 'Race'])['Finish_Pos'].min()
                .reset_index()
            )
            fp['Round Rank'] = fp.groupby(['Round', 'Race'])['Finish_Pos'].rank(ascending=True, method='min')
            final_fp = (
                fp.groupby('Driver')
                .agg(Avg_Rank=('Round Rank', 'mean'), Races=('Race', 'nunique'))
                .reset_index().sort_values('Avg_Rank').reset_index(drop=True)
            )
            final_fp.index += 1
            final_fp.index.name = 'Final Rank'
            final_fp['Avg_Rank'] = final_fp['Avg_Rank'].round(2)
            st.dataframe(
                final_fp.style.format({'Avg_Rank': '{:.2f}'})
                .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
                use_container_width=True,
            )

        with tabs[1]:
            st.write('Rank of ranks: each driver ranked by grid position per race, then averaged.')
            gp = res.dropna(subset=['Grid_Pos']).copy()
            gp['Round Rank'] = gp.groupby(['Round', 'Race'])['Grid_Pos'].rank(ascending=True, method='min')
            final_gp = (
                gp.groupby('Driver')
                .agg(Avg_Rank=('Round Rank', 'mean'), Races=('Race', 'nunique'))
                .reset_index().sort_values('Avg_Rank').reset_index(drop=True)
            )
            final_gp.index += 1
            final_gp.index.name = 'Final Rank'
            final_gp['Avg_Rank'] = final_gp['Avg_Rank'].round(2)
            st.dataframe(
                final_gp.style.format({'Avg_Rank': '{:.2f}'})
                .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
                use_container_width=True,
            )

        with tabs[2]:
            st.write('Average positions gained per race (positive = gained, negative = lost).')
            pg = res.dropna(subset=['Positions Gained']).copy()
            avg_gain = (
                pg.groupby('Driver')['Positions Gained'].mean()
                .reset_index().sort_values('Positions Gained', ascending=False)
                .reset_index(drop=True)
            )
            avg_gain.index += 1
            avg_gain.index.name = 'Rank'
            avg_gain['Positions Gained'] = avg_gain['Positions Gained'].round(2)

            fig = px.bar(
                avg_gain.reset_index(), x='Driver', y='Positions Gained',
                color='Positions Gained', color_continuous_scale='RdYlGn',
                title='Avg Positions Gained per Race (grid → finish)',
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
            race_options = sorted(res.apply(lambda r: f"{r['Round']} — {r['Race']}", axis=1).unique())
            sel_race = st.selectbox('Choose a race:', race_options)
            sel_round_r, sel_race_r = sel_race.split(' — ', 1)
            race_res = (
                res[(res['Round'] == sel_round_r) & (res['Race'] == sel_race_r)]
                .sort_values('Finish_Pos')
                .reset_index(drop=True)
            )
            st.dataframe(
                race_res[['Finish_Pos', 'Driver', 'Team', 'Manufacturer', 'Grid_Pos', 'Positions Gained']]
                .style.format({
                    'Finish_Pos':        '{:.0f}',
                    'Grid_Pos':          lambda x: f'{x:.0f}' if pd.notna(x) else '—',
                    'Positions Gained':  lambda x: f'{x:+.0f}' if pd.notna(x) else '—',
                })
                .background_gradient(cmap=CMAP, subset=['Finish_Pos']),
                use_container_width=True,
                hide_index=True,
            )
