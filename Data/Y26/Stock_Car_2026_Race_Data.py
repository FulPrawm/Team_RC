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

TRAFFIC_THRESHOLD  = 3.0
CMAP               = 'RdYlGn_r'
FILTRO_PADRAO      = 3.0


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
        title=f'Eficiência Aerodinâmica {title_suffix}',
        hover_data=['Car_ID'],
    )
    fig.update_traces(marker_size=12)
    fig.add_vline(x=df['Lap Tm (S)'].mean(), line_dash='dash', line_color='white',
                  annotation_text='Tempo de Volta Médio', annotation_position='bottom left',
                  annotation_font_color='white')
    fig.add_hline(y=df['SPT'].mean(), line_dash='dash', line_color='white',
                  annotation_text='SPT Médio', annotation_position='top right',
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
        y=alt.Y('Diff', title=f'Diferença para o melhor {coluna} (s)'),
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
    st.title('Relatório de Dados da Sessão')

    BASE_DIR     = Path(__file__).resolve().parent
    PASTA_ETAPAS = BASE_DIR / 'Excel_Files' / 'Races'

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

    corrida_label = st.selectbox('Escolha uma corrida:', ['Selecione uma corrida...'] + sorted(labels_map))
    if corrida_label == 'Selecione uma corrida...':
        st.warning('Por favor, selecione uma corrida.')
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
        st.warning('⚠️ Este arquivo de sessão não contém dados de tempo de cruzamento (Crossing Time).')

    # -----------------------------------------------------------------------
    # Filter controls — Filter (always active, main filter)
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

    # Keep all laps within the chosen % of the session's fastest and of each driver's fastest
    class_limit     = melhor_volta * (1 + percentual_sessao / 100)
    driver_fast     = df_base.groupby('Driver')['Lap Tm (S)'].transform('min')
    driver_limit    = driver_fast * (1 + percentual_piloto / 100)
    sessao_filtrado = df_base[(df_base['Lap Tm (S)'] <= class_limit) & (df_base['Lap Tm (S)'] <= driver_limit)].copy()
    st.write(f"Volta mais rápida da sessão: **{melhor_volta:.3f} s** | Limite ({percentual_sessao:.1f}%): **{class_limit:.3f} s**")
    st.write(f"Voltas consideradas: dentro de {percentual_sessao:.1f}% da sessão e {percentual_piloto:.1f}% do piloto, excl. Volta 1")

    st.write(f"🧮 Voltas máximas: **{max_voltas}** | Mínimo de voltas para se qualificar: **{min_voltas}**")

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
        'Selecione o tipo de gráfico',
        ('Tabelas', 'Linhas', 'Histogramas', 'BoxPlots', 'Outros', 'Todas as Voltas'),
        index=0,
    )

    # =======================================================================
    if option == 'Tabelas':
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

        st.subheader('Tabela ordenada por Carro')
        fmt_t1 = {c: '{:.2f}' for c in NUM_COLS if c in tabela1.columns}
        t1s = tabela1.style.format(fmt_t1)
        t1s = t1s.background_gradient(cmap=CMAP)
        t1s = t1s.apply(highlight_driver,       subset=['Driver'])
        t1s = t1s.apply(highlight_team,         subset=['Team'])
        t1s = t1s.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(t1s, hide_index=True)

        st.subheader('Consistência por piloto (Desvio Padrão)')
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

        st.subheader('Tabela ordenada por Equipe')
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
        st.subheader('Análise de BoP (média dos 2 melhores resultados de cada marca)')
        fmt_mf = {c: '{:.3f}' for c in NUM_COLS if c in manuf_table.columns}
        mfs = manuf_table.style.format(fmt_mf)
        mfs = mfs.background_gradient(cmap=CMAP)
        mfs = mfs.apply(highlight_manufacturer, subset=['Manufacturer'])
        st.dataframe(mfs, hide_index=True)

        st.subheader('Tabela de Tempos de Volta da Corrida')
        lap_table = (
            sessao_filtrado
            .pivot(index='Driver', columns='Lap', values='Lap Tm (S)')
            .sort_index(axis=1)
        )
        lap_table.columns = [f'Volta {int(c)}' for c in lap_table.columns]
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
                final_table[f'Volta {lap} Carro'] = cars_col.values
                final_table[f'Volta {lap} Gap']   = gaps_col.values

            st.subheader('Tabela de Classificação (Gap para o Líder)')
            st.dataframe(final_table, use_container_width=True)
        else:
            st.info("⚠️ 'Crossing Time' não disponível. A tabela de classificação não será exibida.")

    # =======================================================================
    elif option == 'Linhas':
    # =======================================================================
        prog_tabs   = st.tabs(['Tempo de Volta', 'Setor 1', 'Setor 2', 'Setor 3', 'Speed Trap'])
        prog_cols   = ['Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
        prog_titles = ['Progressão do Tempo de Volta', 'Progressão do S1', 'Progressão do S2',
                       'Progressão do S3', 'Progressão do SPT']
        for tab, col, title in zip(prog_tabs, prog_cols, prog_titles):
            with tab:
                st.plotly_chart(px.line(sessao, x='Lap', y=col, color='Driver', title=title))

        raising_configs = [
            ('Lap Tm (S)', True,  'Média Crescente do Tempo de Volta'),
            ('S1 Tm',      True,  'Média Crescente do Setor 1'),
            ('S2 Tm',      True,  'Média Crescente do Setor 2'),
            ('S3 Tm',      True,  'Média Crescente do Setor 3'),
            ('SPT',        False, 'Média Crescente do Speed Trap'),
        ]
        ra_tabs = st.tabs(['Tempo de Volta', 'Setor 1', 'Setor 2', 'Setor 3', 'Speed Trap'])
        for tab, (col, ascending, title) in zip(ra_tabs, raising_configs):
            with tab:
                df_plot = sessao_filtrado.copy()
                df_plot['Ranking'] = df_plot.groupby('Driver')[col].rank(ascending=ascending)
                df_plot = df_plot.sort_values(['Driver', 'Ranking'])
                st.plotly_chart(px.line(df_plot, x='Ranking', y=col, color='Driver', title=title))

        delta_tabs = st.tabs(['Delta da Última Volta', 'Delta da Volta Mais Rápida'])
        with delta_tabs[0]:
            st.plotly_chart(px.line(sessao, x='Lap', y='Last Lap Diff', color='Driver', title='Diferença da Última Volta'))
        with delta_tabs[1]:
            st.plotly_chart(px.line(sessao, x='Lap', y='Fast Lap Diff', color='Driver', title='Delta da Volta Mais Rápida'))

        gap_tabs = st.tabs(['Gap para o Vencedor', 'Gap para o Líder da Volta', 'Gap para Referência'])
        with gap_tabs[0]:
            if 'Gap to Winner' in sessao.columns:
                st.plotly_chart(px.line(sessao, x='Lap', y='Gap to Winner', color='Driver', title='Gap para o Vencedor'))
            else:
                st.info("⚠️ 'Crossing Time' não disponível. O gráfico de Gap para o Vencedor não será exibido.")
        with gap_tabs[1]:
            if 'Gap to Leader' in sessao.columns:
                st.plotly_chart(px.line(sessao, x='Lap', y='Gap to Leader', color='Driver', title='Gap para o Líder'))
            else:
                st.info("⚠️ 'Crossing Time' não disponível. O gráfico de Gap para o Líder não será exibido.")
        with gap_tabs[2]:
            if 'Cumulative Crossing' in sessao.columns:
                driver_options = (
                    sessao[['Car_ID', 'Driver']].dropna().drop_duplicates().sort_values('Driver')
                )
                ref_driver = st.selectbox(
                    'Selecione o carro de referência:', driver_options['Driver'], key='gap_to_reference_driver',
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
                    title=f'Gap para Referência ({ref_driver})',
                ))
            else:
                st.info("⚠️ 'Crossing Time' não disponível. O gráfico de Gap para Referência não será exibido.")

        # Position Change chart
        st.subheader('Mudança de Posição')
        if 'Gap to Leader' in sessao.columns:
            pos_df = sessao.copy()
            pos_df['Position'] = (
                pos_df.groupby('Lap')['Gap to Leader'].rank(method='first').astype(int)
            )
            fig_pos = px.line(
                pos_df.sort_values(['Driver', 'Lap']),
                x='Lap', y='Position', color='Driver',
                markers=True,
                title='Mudança de Posição por Volta',
            )
            fig_pos.update_yaxes(autorange='reversed', title='Posição', dtick=1)
            fig_pos.update_xaxes(title='Volta', dtick=1)
            fig_pos.update_traces(marker_size=5)
            fig_pos.update_layout(
                yaxis=dict(tickprefix='P'),
                hovermode='x unified',
            )
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info("⚠️ 'Crossing Time' não disponível. O gráfico de Mudança de Posição não será exibido.")

    # =======================================================================
    elif option == 'Histogramas':
    # =======================================================================
        skip_cols = {'Car_ID', 'Driver', 'Team', 'Manufacturer'}
        for var in ANALISE_CARROS:
            if var in skip_cols:
                continue
            st.plotly_chart(px.histogram(sessao_filtrado[var], nbins=25, title=f'Distribuição de {var}'))

    # =======================================================================
    elif option == 'Outros':
    # =======================================================================
        st.subheader('Eficiência dos Carros')
        tab1, tab2 = st.tabs(['Volta Mais Rápida por Equipe', 'Média por Equipe'])

        with tab1:
            st.markdown('### Volta Mais Rápida por Equipe')
            fastest_per_team = (
                sessao_filtrado.sort_values('Lap Tm (S)')
                .groupby('Team').first().reset_index()
            )
            st.plotly_chart(_plot_efficiency(fastest_per_team, '(Volta Mais Rápida por Equipe)'), use_container_width=True)
            st.markdown('''
- **↖ Superior Esquerdo** → Alta eficiência geral (reta + curva)
- **↗ Superior Direito** → Baixa downforce (boa reta, curva ruim)
- **↙ Inferior Esquerdo** → Alta downforce (boa curva, reta ruim)
- **↘ Inferior Direito** → Baixa eficiência (nenhuma das duas)
''')

        with tab2:
            st.markdown('### Média por Equipe')
            avg_per_team = sessao_filtrado.groupby('Team', as_index=False)[['Lap Tm (S)', 'SPT']].mean()
            rep_car      = sessao_filtrado.groupby('Team')['Car_ID'].first().reset_index()
            avg_per_team = avg_per_team.merge(rep_car, on='Team')
            st.plotly_chart(_plot_efficiency(avg_per_team, '(Média por Equipe)'), use_container_width=True)
            st.markdown('''
- **↗ Superior Direito** → Alta eficiência geral (reta + curva)
- **↖ Superior Esquerdo** → Baixa downforce (boa reta, curva ruim)
- **↘ Inferior Direito** → Alta downforce (boa curva, reta ruim)
- **↙ Inferior Esquerdo** → Baixa eficiência (nenhuma das duas)
''')

        sector_tabs_cfg = {
            'Gap para o Carro Mais Rápido na Média - Volta': 'Lap Tm (S)',
            'Gap para o Carro Mais Rápido na Média - S1':    'S1 Tm',
            'Gap para o Carro Mais Rápido na Média - S2':    'S2 Tm',
            'Gap para o Carro Mais Rápido na Média - S3':    'S3 Tm',
        }
        tabs = st.tabs(list(sector_tabs_cfg.keys()))
        for tab, (tab_name, coluna) in zip(tabs, sector_tabs_cfg.items()):
            with tab:
                df_avg = sessao_filtrado.groupby('Driver')[coluna].mean().reset_index()
                st.altair_chart(_gap_bar_chart(df_avg, coluna, tab_name), use_container_width=True)

        # -------------------------------------------------------------------
        # Percentual difference — ALL drivers
        # -------------------------------------------------------------------
        st.header('Diferença percentual para a melhor volta — Todos os Pilotos')
        tabs_dif = st.tabs(all_drivers)
        for tab, driver_name in zip(tabs_dif, all_drivers):
            with tab:
                df = sessao_filtrado[sessao_filtrado['Driver'] == driver_name].copy()
                if df.empty:
                    st.write('Nenhuma volta disponível para este piloto após o filtro.')
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
                    title=f'{driver_name} — Diferença % por volta',
                )
                fig.update_traces(textposition='outside')
                fig.add_vline(x=best_lap_num, line_dash='dash', line_color='white',
                              annotation_text='Melhor volta', annotation_position='top')
                for _, bloco in df.groupby('Bloco'):
                    add_trend_line(fig, bloco['Lap'], bloco['Diff %'])
                fig.update_layout(
                    yaxis_title='Diferença para a melhor volta (%)',
                    xaxis_title='Volta',
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
                    title=f'Distribuição de {var} por Fabricante',
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # By driver — with driver filter multiselect
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
                display_cols = [c for c in
                    ['Lap', 'Lap Tm (S)', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT', 'Lap Traffic?', 'Gap to Leader', 'Gap to Winner']
                    if c in df_drv.columns]
                st.dataframe(df_drv[display_cols].reset_index(drop=True), use_container_width=True)
