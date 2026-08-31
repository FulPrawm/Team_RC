# Stock_Car_2026_Season_Analysis.py
import math
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
FILTRO_PADRAO = 3.0
# Pilotos com menos etapas que o mínimo ficam fora de todos os rankings da temporada.
# O mínimo é calculado dinamicamente (metade das etapas já disputadas) em vez de um
# número fixo — com um valor fixo, no início da temporada (poucas etapas disputadas)
# ou com pilotos convidados/trocas de equipe, TODOS os pilotos podiam ficar abaixo do
# mínimo e as tabelas apareciam completamente vazias.
MIN_ROUNDS_FRACTION = 0.5


def _round_label(folder: str) -> str:
    parts = folder.split('_', 1)
    return f"{parts[0]} · {parts[1].replace('_', ' ')}" if len(parts) == 2 else folder

def _round_order(folder: str) -> int:
    m = re.search(r'ET(\d+)', folder)
    return int(m.group(1)) if m else 99

def _stem_tag(filename: str) -> str:
    return re.sub(r'ET\d+_', '', Path(filename).stem, flags=re.IGNORECASE).upper()


# ---------------------------------------------------------------------------
# Season loader
# ---------------------------------------------------------------------------
def _dir_signature(base_dir: Path) -> tuple:
    """
    Snapshot (caminho, mtime, tamanho) de cada .xlsx da temporada.
    É passado para `_load_season` para que o cache do Streamlit seja invalidado
    sempre que uma etapa/arquivo novo for adicionado — sem isso, o cache
    permanece com o resultado da primeira vez que rodou (ex.: só ET02) mesmo
    depois de novas etapas serem adicionadas ao repositório.
    """
    excel_root = base_dir / 'Excel_Files'
    if not excel_root.exists():
        return ()
    sig = []
    for f in sorted(excel_root.rglob('*.xlsx')):
        try:
            stat = f.stat()
            sig.append((str(f.relative_to(base_dir)), stat.st_mtime_ns, stat.st_size))
        except OSError:
            continue
    return tuple(sig)


@st.cache_data(show_spinner=False)
def _load_season(base_dir: Path, dir_signature: tuple) -> pd.DataFrame:
    races_root    = base_dir / 'Excel_Files' / 'Races'
    practice_root = base_dir / 'Excel_Files' / 'Practice_And_Qualy'

    all_etapas = sorted(set(
        ([d.name for d in races_root.iterdir()    if d.is_dir()] if races_root.exists()    else []) +
        ([d.name for d in practice_root.iterdir() if d.is_dir()] if practice_root.exists() else [])
    ))

    lap_frames = []

    for etapa_folder in all_etapas:
        rlabel = _round_label(etapa_folder)
        rorder = _round_order(etapa_folder)

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
                    st.warning(f"Não foi possível carregar {f.name}: {e}")

    return pd.concat(lap_frames, ignore_index=True) if lap_frames else pd.DataFrame()


# ---------------------------------------------------------------------------
# Ranking helpers
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


def _apply_min_rounds(final: pd.DataFrame, pivot: pd.DataFrame,
                       group_col: str, min_rounds: int):
    """Drop entries with fewer than `min_rounds` rounds and re-number the final rank."""
    kept = final[final['Rounds'] >= min_rounds].copy()
    kept = kept.sort_values('Avg_Rank').reset_index(drop=True)
    kept.index += 1
    kept.index.name = 'Final Rank'
    pivot = pivot.loc[pivot.index.isin(kept[group_col])]
    return kept, pivot


def _team_ranking(final_drivers: pd.DataFrame, driver_team_map: dict) -> pd.DataFrame:
    """
    Ranking por equipe: para cada equipe, faz a média do Avg_Rank dos seus
    pilotos (já filtrados pelo mínimo de etapas) para saber qual equipe é mais forte.
    """
    d = final_drivers[['Driver', 'Avg_Rank']].copy()
    d['Team'] = d['Driver'].map(driver_team_map)
    d = d.dropna(subset=['Team'])
    team = (
        d.groupby('Team')
        .agg(Avg_Rank=('Avg_Rank', 'mean'), Pilotos=('Driver', 'nunique'))
        .reset_index()
        .sort_values('Avg_Rank')
        .reset_index(drop=True)
    )
    team.index += 1
    team.index.name = 'Final Rank'
    team['Avg_Rank'] = team['Avg_Rank'].round(2)
    return team


def _show_rank_table(final, pivot, rounds_ordered, value_label, ascending=True):
    """Show final ranking + per-round rank pivot."""
    st.dataframe(
        final.style.format({'Avg_Rank': '{:.2f}'})
        .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
        use_container_width=True,
    )
    st.caption('Detalhe do ranking por etapa (1 = melhor na etapa)')
    pivot_show = pivot[[r for r in rounds_ordered if r in pivot.columns]]
    fmt = {c: (lambda x: f'{x:.0f}' if pd.notna(x) else '—') for c in pivot_show.columns}
    st.dataframe(
        pivot_show.style.format(fmt)
        .background_gradient(cmap=CMAP if ascending else 'RdYlGn', axis=1),
        use_container_width=True,
    )


def _show_team_table(team: pd.DataFrame):
    st.dataframe(
        team.style.format({'Avg_Rank': '{:.2f}'})
        .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def show():
    st.image('header.png')
    st.title('Análise da Temporada — 2026')
    st.warning('🚧 Página ainda em construção — dados e funcionalidades podem mudar.')

    BASE_DIR = Path(__file__).resolve().parent

    with st.spinner('Carregando dados da temporada completa…'):
        df_laps = _load_season(BASE_DIR, _dir_signature(BASE_DIR))

    if df_laps.empty:
        st.error('Nenhum dado de temporada encontrado.')
        return

    rounds_ordered = (
        df_laps.drop_duplicates('Round').sort_values('Round Order')['Round'].tolist()
    )

    # -----------------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------------
    st.subheader('🔧 Filtros')
    c1, c2 = st.columns(2)
    with c1:
        all_types  = sorted(df_laps['Session Type'].unique())
        sel_types  = st.multiselect('Tipo de sessão:', all_types, default=['Race'], key='s_type')
    with c2:
        sel_rounds = st.multiselect('Etapas (vazio = todas):', rounds_ordered, default=[], key='s_round')

    df = df_laps.copy()
    if sel_types:
        df = df[df['Session Type'].isin(sel_types)]
    if sel_rounds:
        df = df[df['Round'].isin(sel_rounds)]
        rounds_ordered = [r for r in rounds_ordered if r in sel_rounds]

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

    class_limit = df['Lap Tm (S)'].min() * (1 + percentual_sessao / 100)
    drv_fast    = df.groupby('Driver')['Lap Tm (S)'].transform('min')
    df = df[(df['Lap Tm (S)'] <= class_limit) & (df['Lap Tm (S)'] <= drv_fast * (1 + percentual_piloto / 100))].copy()
    st.write(f"Voltas consideradas: dentro de {percentual_sessao:.1f}% da sessão e {percentual_piloto:.1f}% do piloto")

    if df.empty:
        st.warning('Nenhum dado após os filtros.')
        return

    total_rounds = df['Round'].nunique()
    min_rounds   = max(1, math.ceil(total_rounds * MIN_ROUNDS_FRACTION))

    st.caption(f"**{len(df):,} voltas** · **{total_rounds} etapas** · **{df['Driver'].nunique()} pilotos**")
    st.caption(f"Rankings consideram apenas pilotos com no mínimo **{min_rounds} de {total_rounds} etapas**.")
    st.divider()

    driver_team_map = df.drop_duplicates('Driver').set_index('Driver')['Team'].to_dict()

    # -----------------------------------------------------------------------
    # Analysis selector
    # -----------------------------------------------------------------------
    option = st.selectbox('Selecione a análise:', (
        'Ranking de Tempo de Volta',
        'Ranking de Speed Trap',
        'Ranking de Consistência',
        'Rating Geral',
    ))

    # =======================================================================
    if option == 'Ranking de Tempo de Volta':
    # =======================================================================
        st.subheader('Ranking de Tempo de Volta — ranking de rankings entre etapas')
        tabs = st.tabs(['Melhor Volta', 'Volta Média'])

        with tabs[0]:
            st.write('Cada piloto é ranqueado pela melhor volta **dentro de cada etapa**, depois esses rankings são calculados na média.')
            final, pivot = _rank_of_ranks(df, 'Lap Tm (S)', 'min', ascending=True)
            final, pivot = _apply_min_rounds(final, pivot, 'Driver', min_rounds)
            _show_rank_table(final, pivot, rounds_ordered, 'Melhor Volta')
            st.markdown('##### 🏎️ Ranking por Equipe (média dos dois pilotos)')
            _show_team_table(_team_ranking(final, driver_team_map))

        with tabs[1]:
            st.write('Cada piloto é ranqueado pela volta média **dentro de cada etapa**, depois esses rankings são calculados na média.')
            final, pivot = _rank_of_ranks(df, 'Lap Tm (S)', 'mean', ascending=True)
            final, pivot = _apply_min_rounds(final, pivot, 'Driver', min_rounds)
            _show_rank_table(final, pivot, rounds_ordered, 'Volta Média')
            st.markdown('##### 🏎️ Ranking por Equipe (média dos dois pilotos)')
            _show_team_table(_team_ranking(final, driver_team_map))

    # =======================================================================
    elif option == 'Ranking de Speed Trap':
    # =======================================================================
        st.subheader('Ranking de Speed Trap — ranking de rankings entre etapas')
        tabs = st.tabs(['SPT Máximo', 'SPT Médio'])

        with tabs[0]:
            final, pivot = _rank_of_ranks(df, 'SPT', 'max', ascending=False)
            final, pivot = _apply_min_rounds(final, pivot, 'Driver', min_rounds)
            _show_rank_table(final, pivot, rounds_ordered, 'SPT Máximo', ascending=False)
            st.markdown('##### 🏎️ Ranking por Equipe (média dos dois pilotos)')
            _show_team_table(_team_ranking(final, driver_team_map))

        with tabs[1]:
            final, pivot = _rank_of_ranks(df, 'SPT', 'mean', ascending=False)
            final, pivot = _apply_min_rounds(final, pivot, 'Driver', min_rounds)
            _show_rank_table(final, pivot, rounds_ordered, 'SPT Médio', ascending=False)
            st.markdown('##### 🏎️ Ranking por Equipe (média dos dois pilotos)')
            _show_team_table(_team_ranking(final, driver_team_map))

    # =======================================================================
    elif option == 'Ranking de Consistência':
    # =======================================================================
        st.subheader('Ranking de Consistência — ranking do desvio padrão por etapa, depois calculados na média')
        st.write('Menor variação dentro de cada etapa = mais consistente. Os rankings são calculados na média entre etapas.')

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
        final, pivot = _apply_min_rounds(final, pivot, 'Driver', min_rounds)

        fig = px.bar(
            final.reset_index(), x='Driver', y='Avg_Rank',
            color='Avg_Rank', color_continuous_scale=CMAP,
            title='Ranking Médio de Consistência (menor = mais consistente)',
            text='Avg_Rank',
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        _show_rank_table(final, pivot, rounds_ordered, 'Desvio Padrão')
        st.markdown('##### 🏎️ Ranking por Equipe (média dos dois pilotos)')
        _show_team_table(_team_ranking(final, driver_team_map))

    # =======================================================================
    elif option == 'Rating Geral':
    # =======================================================================
        st.subheader('Rating Geral — combina tempo de volta e consistência para achar o piloto mais completo')
        st.write(
            'Cada piloto é ranqueado pela volta média e pelo desvio padrão da volta **dentro de cada etapa**. '
            'Os dois rankings são calculados na média entre etapas e combinados (peso igual) em um Rating Geral — '
            'quanto menor, mais completo (rápido + consistente) o piloto.'
        )

        lap_final, _ = _rank_of_ranks(df, 'Lap Tm (S)', 'mean', ascending=True)

        std_per_round = (
            df.groupby(['Driver', 'Round', 'Round Order'])['Lap Tm (S)']
            .std().reset_index().rename(columns={'Lap Tm (S)': 'Std'})
        )
        std_per_round['Round Rank'] = (
            std_per_round.groupby('Round')['Std'].rank(ascending=True, method='min')
        )
        std_final = (
            std_per_round.groupby('Driver')
            .agg(Avg_Rank=('Round Rank', 'mean'), Rounds=('Round', 'nunique'))
            .reset_index()
        )

        combined = (
            lap_final[['Driver', 'Avg_Rank', 'Rounds']]
            .rename(columns={'Avg_Rank': 'Ritmo'})
            .merge(
                std_final[['Driver', 'Avg_Rank']].rename(columns={'Avg_Rank': 'Consistência'}),
                on='Driver', how='inner',
            )
        )
        combined = combined[combined['Rounds'] >= min_rounds].copy()
        combined['Avg_Rank'] = ((combined['Ritmo'] + combined['Consistência']) / 2)
        combined = combined.sort_values('Avg_Rank').reset_index(drop=True)
        combined.index += 1
        combined.index.name = 'Final Rank'
        combined[['Avg_Rank', 'Ritmo', 'Consistência']] = combined[['Avg_Rank', 'Ritmo', 'Consistência']].round(2)

        st.dataframe(
            combined[['Driver', 'Avg_Rank', 'Ritmo', 'Consistência', 'Rounds']]
            .style.format({'Avg_Rank': '{:.2f}', 'Ritmo': '{:.2f}', 'Consistência': '{:.2f}'})
            .background_gradient(cmap=CMAP, subset=['Avg_Rank']),
            use_container_width=True,
        )

        fig = px.bar(
            combined.reset_index(), x='Driver', y='Avg_Rank',
            color='Avg_Rank', color_continuous_scale=CMAP,
            title='Rating Geral (menor = mais completo)',
            text='Avg_Rank',
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('##### 🏎️ Rating Geral por Equipe (média dos dois pilotos)')
        _show_team_table(_team_ranking(combined[['Driver', 'Avg_Rank']], driver_team_map))
