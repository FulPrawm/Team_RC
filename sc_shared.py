# sc_shared.py
# Shared constants and utility functions used by both Race and Practice modules.

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

# Gap (in seconds) to the car ahead on the same lap, below which a lap is
# considered "traffic" rather than a clean lap. Shared by every module that
# derives a '% Clean Laps' metric from 'Lap Traffic?'.
TRAFFIC_THRESHOLD: float = 3.0

# ---------------------------------------------------------------------------
# Lookup dictionaries
# ---------------------------------------------------------------------------

TEAMS_DICT: dict[int, str] = {
    27: 'A. Mattheis TMG',   73: 'A. Mattheis TMG',
    12: 'A. Mattheis Vogel', 83: 'A. Mattheis Vogel',
    18: 'Blau Motorsport',   29: 'Blau Motorsport',
    293: 'Car Racing',       301: 'Car Racing',
    85: 'Cavaleiro Sports',  90: 'Cavaleiro Sports',
    81: 'Crown Racing',      95: 'Crown Racing',
    1:  'Eurofarma RC',      11: 'Eurofarma RC',
    10: 'Full Time GR',      80: 'Full Time GR',
    21: 'Mercado Livre Racing', 30: 'Mercado Livre Racing',
    97: 'RTR Racing Team',   25: 'RTR Racing Team',
    8:  'Scuderia Bandeiras', 33: 'Scuderia Bandeiras',
    51: 'Scuderia Bandeiras Sports', 111: 'Scuderia Bandeiras Sports',
    0:  'Scudeira Chiarelli', 22: 'Scuderia Chiarelli',
    121: 'Sterling Racing',  444: 'Sterling Racing',
    7:  'Team RC',           38: 'Team RC',
    4:  'TMG Racing',        19: 'TMG Racing',
    6:  'Mercado Livre Racing Team', 24: 'Albatroz Racing',
    72: 'Full Time GR'
}

# Mid-season team changes: car -> [(first_round, last_round, team)].
# Rounds outside every range fall back to TEAMS_DICT.
TEAM_CHANGES: dict[int, list[tuple[int, int, str]]] = {
    8:   [(6, 99, 'Full Time Sports')],   # Rafael Suzuki (Scuderia Bandeiras until ET05)
    111: [(9, 99, 'Full Time Sports')],   # Rubens Barrichello (Scuderia Bandeiras Sports until ET08)
    24:  [(1, 2, 'SG28')],                # Pipe Bartz (Albatroz Racing from ET03)
}

TEAM_TO_MANUFACTURER: dict[str, str] = {
    'A. Mattheis TMG':          'Toyota',
    'Car Racing':               'Toyota',
    'Crown Racing':             'Toyota',
    'Full Time GR':             'Toyota',
    'Mercado Livre Racing':     'Toyota',
    'Mercado Livre Racing Team':'Toyota',
    'RTR Racing Team':          'Toyota',
    'A. Mattheis Vogel':        'Chevrolet',
    'Cavaleiro Sports':         'Chevrolet',
    'Scuderia Bandeiras':       'Chevrolet',
    'Scuderia Chiarelli':       'Chevrolet',
    'TMG Racing':               'Chevrolet',
    'Blau Motorsport':          'Mitsubishi',
    'Eurofarma RC':             'Mitsubishi',
    'Albatroz Racing':          'Mitsubishi',
    'Scuderia Bandeiras Sports':'Mitsubishi',
    'Sterling Racing':          'Mitsubishi',
    'Team RC':                  'Mitsubishi',
}

DRIVERS_DICT: dict[int, str] = {
    0: 'Cacá Bueno',        1: 'Felipe Fraga',
    4: 'Julio Campos',      6: 'Hélio Castroneves',
    7: 'Sérgio Sette Câmara', 8: 'Rafael Suzuki',
    10: 'Ricardo Zonta',   11: 'Gaetano Di Mauro',
    12: 'Lucas Foresti',   18: 'Allam Khodair',
    19: 'Felipe Massa',    21: 'Thiago Camilo',
    22: 'André Moraes',    24: 'Pipe Bartz',
    27: 'Renan Guerra',    29: 'Daniel Serra',
    30: 'Cesar Ramos',     33: 'Nelson Piquet Jr',
    38: 'Zezinho Muggiati', 51: 'Átila Abreu',
    73: 'Enzo Elias',      80: 'Alfredinho Ibiapina',
    81: 'Arthur Leist',    83: 'Gabriel Casagrande',
    85: 'Guilherme Salas', 90: 'Ricardo Mauricio',
    95: 'Lucas Kohl',      97: 'Bruna Tomaselli',
    111: 'Rubens Barrichello', 121: 'Felipe Baptista',
    293: 'Léo Reis',       301: 'Rafa Reis',
    444: 'Vicente Orige',   25: 'Tatiana Calderón',
    72: 'Antonella Bassani'
}

# Colors for specific drivers / teams / manufacturers
COLORS_DRIVER: dict[str, tuple[str, str]] = {
    'Gaetano Di Mauro':     ('lightblue', 'black'),
    'Sérgio Sette Câmara':  ('gray',      'white'),
    'Felipe Fraga':         ('yellow',    'black'),
    'Zezinho Muggiati':     ('#0057B8',   'white'),
}
COLORS_TEAM: dict[str, tuple[str, str]] = {
    'Eurofarma RC': ('yellow', 'black'),
    'Team RC':      ('gray',   'white'),
}
COLORS_MANUFACTURER: dict[str, tuple[str, str]] = {
    'Mitsubishi': ('red', 'white'),
}

# Custom bar colors used in gap charts (keyed by driver name)
CORES_PERSONALIZADAS: dict[str, str] = {
    'Gaetano Di Mauro':    'blue',
    'Sérgio Sette Câmara': 'gray',
    'Felipe Fraga':        'yellow',
    'Zezinho Muggiati':    '#0057B8',
}

# Cars belonging to each team for team-specific views
TEAM_CARS: dict[str, list[int]] = {
    'Eurofarma RC': [1, 11],
    'Team RC':      [7, 38],
}
TEAM_CAR_COLORS: dict[int, str] = {
    11: 'blue', 7: 'gray', 1: 'yellow', 38: '#0057B8',
}
TEAM_CAR_NAMES: dict[int, str] = {
    11: 'Gaetano Di Mauro',
    7:  'Sérgio Sette Câmara',
    1:  'Felipe Fraga',
    38: 'Zezinho Muggiati',
}

# ---------------------------------------------------------------------------
# 2025 season lookups
# ---------------------------------------------------------------------------

TEAMS_DICT_2025: dict[int, str] = {
    18: 'Blau Motorsport', 29: 'Blau Motorsport',
    38: 'Car Racing Sterling', 301: 'Car Racing Sterling',
    21: 'Ipiranga Racing', 30: 'Ipiranga Racing',
    12: 'Amattheis Vogel', 83: 'Amattheis Vogel',
    10: 'RCM Motorsport', 44: 'RCM Motorsport', 31: 'RCM Motorsport',
    8: 'TMG Racing', 19: 'TMG Racing', 70: 'TMG Racing',
    11: 'Eurofarma RC', 88: 'Eurofarma RC',
    4: 'Crown Racing', 81: 'Crown Racing',
    85: 'Cavaleiro Sports', 90: 'Cavaleiro Sports',
    5: 'FT Cavaleiro', 111: 'FT Cavaleiro',
    73: 'Scuderia Bandeiras', 51: 'Scuderia Bandeiras',
    444: 'Scuderia Bandeiras Sports', 33: 'Scuderia Bandeiras Sports',
    121: 'Car Racing KTF', 101: 'Car Racing KTF',
    7: 'FT Gazoo Racing', 9: 'FT Gazoo Racing', 72: 'FT Gazoo Racing',
    95: 'Scuderia Chiarelli', 0: 'Scuderia Chiarelli',
    6: 'A. Mattheis Motorsport',
}

TEAM_TO_MANUFACTURER_2025: dict[str, str] = {
    'Eurofarma RC':              'Mitsubishi',
    'Blau Motorsport':           'Mitsubishi',
    'RCM Motorsport':            'Mitsubishi',
    'Scuderia Bandeiras Sports': 'Mitsubishi',
    'Car Racing KTF':            'Mitsubishi',
    'Car Racing Sterling':       'Toyota',
    'Ipiranga Racing':           'Toyota',
    'Crown Racing':              'Toyota',
    'FT Cavaleiro':              'Toyota',
    'FT Gazoo Racing':           'Toyota',
    'Amattheis Vogel':           'Chevrolet',
    'TMG Racing':                'Chevrolet',
    'Cavaleiro Sports':          'Chevrolet',
    'Scuderia Bandeiras':        'Chevrolet',
    'Scuderia Chiarelli':        'Chevrolet',
    'A. Mattheis Motorsport':    'Chevrolet',
}

DRIVERS_DICT_2025: dict[int, str] = {
    18: 'Allam Khodair',     29: 'Daniel Serra',
    38: 'Zezinho Muggiati',  301: 'Rafael Reis',
    21: 'Thiago Camilo',     30: 'Cesar Ramos',
    12: 'Lucas Foresti',     83: 'Gabriel Casagrande',
    10: 'Ricardo Zonta',     44: 'Bruno Baptista',
    8: 'Rafael Suzuki',      19: 'Felipe Massa',     70: 'Rafael Suzuki',
    11: 'Gaetano Di Mauro',  88: 'Felipe Fraga',
    4: 'Julio Campos',       81: 'Arthur Leist',
    85: 'Guilherme Salas',   90: 'Ricardo Mauricio',
    5: 'Denis Navarro',      111: 'Rubens Barrichello',
    73: 'Enzo Elias',        51: 'Átila Abreu',
    444: 'Vicente Orige',    33: 'Nelsinho Piquet',
    121: 'Felipe Baptista',  101: 'Gianluca Petecof',
    7: 'JP Oliveira',        9: 'Arthur Gama',
    95: 'Lucas Kohl',        0: 'Cacá Bueno',
    6: 'Hélio Castroneves',  72: 'Antonella Bassani',
    31: 'Marcos Regadas',
}

COLORS_DRIVER_2025: dict[str, tuple[str, str]] = {
    'Ricardo Zonta':     ('red',       'white'),
    'Gaetano Di Mauro':  ('lightblue', 'black'),
    'Bruno Baptista':    ('gray',      'white'),
    'Felipe Fraga':      ('yellow',    'black'),
    'Marcos Regadas':    ('gray',      'white'),
    'Zezinho Muggiati':  ('#0057B8',   'white'),
}
COLORS_TEAM_2025: dict[str, tuple[str, str]] = {
    'Eurofarma RC':   ('yellow', 'black'),
    'RCM Motorsport': ('gray',   'white'),
}

CORES_PERSONALIZADAS_2025: dict[str, str] = {
    'Ricardo Zonta':    'red',
    'Gaetano Di Mauro': 'blue',
    'Bruno Baptista':   'gray',
    'Felipe Fraga':     'yellow',
    'Marcos Regadas':   'gray',
    'Zezinho Muggiati': '#0057B8',
}
TEAM_CAR_COLORS_2025: dict[int, str] = {
    10: 'red', 11: 'blue', 44: 'gray', 88: 'yellow', 31: 'gray', 38: '#0057B8',
}
TEAM_CAR_NAMES_2025: dict[int, str] = {
    10: 'Ricardo Zonta',
    11: 'Gaetano Di Mauro',
    44: 'Bruno Baptista',
    88: 'Felipe Fraga',
    31: 'Marcos Regadas',
    38: 'Zezinho Muggiati',
}


@dataclass(frozen=True)
class SeasonConfig:
    """Everything that differs from one season to another."""
    year: int
    teams: dict
    team_to_manufacturer: dict
    drivers: dict
    team_changes: dict
    colors_driver: dict
    colors_team: dict
    colors_manufacturer: dict
    cores_personalizadas: dict
    team_car_colors: dict
    team_car_names: dict
    default_drivers: list

    @property
    def folder(self) -> str:
        return f'Y{self.year % 100}'


SEASONS: dict[int, SeasonConfig] = {
    2025: SeasonConfig(
        year=2025,
        teams=TEAMS_DICT_2025,
        team_to_manufacturer=TEAM_TO_MANUFACTURER_2025,
        drivers=DRIVERS_DICT_2025,
        team_changes={},
        colors_driver=COLORS_DRIVER_2025,
        colors_team=COLORS_TEAM_2025,
        colors_manufacturer=COLORS_MANUFACTURER,
        cores_personalizadas=CORES_PERSONALIZADAS_2025,
        team_car_colors=TEAM_CAR_COLORS_2025,
        team_car_names=TEAM_CAR_NAMES_2025,
        default_drivers=['Felipe Fraga', 'Gaetano Di Mauro', 'Ricardo Zonta', 'Bruno Baptista'],
    ),
    2026: SeasonConfig(
        year=2026,
        teams=TEAMS_DICT,
        team_to_manufacturer=TEAM_TO_MANUFACTURER,
        drivers=DRIVERS_DICT,
        team_changes=TEAM_CHANGES,
        colors_driver=COLORS_DRIVER,
        colors_team=COLORS_TEAM,
        colors_manufacturer=COLORS_MANUFACTURER,
        cores_personalizadas=CORES_PERSONALIZADAS,
        team_car_colors=TEAM_CAR_COLORS,
        team_car_names=TEAM_CAR_NAMES,
        default_drivers=['Felipe Fraga', 'Gaetano Di Mauro', 'Sérgio Sette Câmara', 'Zezinho Muggiati'],
    ),
}


def get_season(year: int = 2026) -> SeasonConfig:
    return SEASONS[year]


# ---------------------------------------------------------------------------
# Shared helper functions
# ---------------------------------------------------------------------------

def _round_number(etapa) -> int | None:
    """Extract the round number from a folder/file name such as 'ET06_Cascavel_II'."""
    m = re.search(r'ET(\d+)', str(etapa), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def enrich_session(sessao: pd.DataFrame, etapa: str | None = None, year: int = 2026) -> pd.DataFrame:
    """
    Add Team, Manufacturer and Driver columns to a raw session DataFrame.
    `etapa` (e.g. 'ET06_Cascavel_II' or 'ET06_R1') selects the mid-season team
    changes of the season `year`; without it, the season's team dict is used as-is.
    Returns the same DataFrame (modified in place for efficiency).
    """
    season = get_season(year)
    sessao['Team']         = sessao['Car_ID'].map(season.teams)
    # Manufacturer belongs to the car, so it is resolved before any team change.
    sessao['Manufacturer'] = sessao['Team'].map(season.team_to_manufacturer)
    sessao['Driver']       = sessao['Car_ID'].map(season.drivers)

    rnd = _round_number(etapa)
    if rnd is not None:
        for car_id, changes in season.team_changes.items():
            team = next((t for first, last, t in changes if first <= rnd <= last), None)
            if team is not None:
                sessao.loc[sessao['Car_ID'] == car_id, 'Team'] = team
    return sessao


def convert_to_seconds(x) -> float:
    """Convert a 'M:SS.mmm' string or numeric value to float seconds."""
    if isinstance(x, str) and ':' in x:
        minutes, seconds = x.split(':', 1)
        return float(minutes) * 60 + float(seconds)
    try:
        return float(x)
    except (ValueError, TypeError):
        return pd.NA


def coerce_numeric_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Force a list of columns to numeric, coercing errors to NaN."""
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


# ---------------------------------------------------------------------------
# Highlight style functions (for st.dataframe styling)
# ---------------------------------------------------------------------------

def _highlight(s: pd.Series, colors: dict) -> list[str]:
    return [
        f"background-color: {colors[v][0]}; color: {colors[v][1]}" if v in colors else ''
        for v in s
    ]

def make_highlighters(year: int = 2026):
    """Return (highlight_driver, highlight_team, highlight_manufacturer) for a season."""
    season = get_season(year)
    return (
        lambda s: _highlight(s, season.colors_driver),
        lambda s: _highlight(s, season.colors_team),
        lambda s: _highlight(s, season.colors_manufacturer),
    )

def highlight_driver(s: pd.Series) -> list[str]:
    return _highlight(s, COLORS_DRIVER)

def highlight_team(s: pd.Series) -> list[str]:
    return _highlight(s, COLORS_TEAM)

def highlight_manufacturer(s: pd.Series) -> list[str]:
    return _highlight(s, COLORS_MANUFACTURER)


# ---------------------------------------------------------------------------
# Trend-line helper (used in Race "Lines" and team diff charts)
# ---------------------------------------------------------------------------

def add_trend_line(fig: go.Figure, x_vals, y_vals, color: str = 'lightgray') -> None:
    """Fit a linear regression and add a dashed trend line to a Plotly figure."""
    if len(x_vals) < 2:
        return
    X = x_vals.values.reshape(-1, 1)
    y_pred = LinearRegression().fit(X, y_vals.values).predict(X)
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_pred,
        mode='lines',
        line=dict(color=color, width=2, dash='dot'),
        opacity=0.4,
        showlegend=False,
    ))


# ---------------------------------------------------------------------------
# Traffic / clean-lap detection (used by Race and Season modules)
# ---------------------------------------------------------------------------

def detect_traffic(sessao: pd.DataFrame, threshold: float = TRAFFIC_THRESHOLD) -> pd.DataFrame:
    """
    Flag each row's lap as traffic ('Yes'/'No') based on the gap (in 'Crossing
    Seconds') to the car ahead on the same lap. `sessao` must contain a single
    session's laps — mixing laps from different sessions in one call would let
    a car from one race be treated as "ahead" of a car from another.
    """
    df = sessao.sort_values(['Lap', 'Crossing Seconds']).copy()
    prev_crossing = df.groupby('Lap')['Crossing Seconds'].shift(1)
    gap_ahead     = df['Crossing Seconds'] - prev_crossing
    df['Lap Traffic?'] = np.where(
        gap_ahead.notna() & (gap_ahead < threshold),
        'Yes', 'No',
    )
    return df


def clean_lap_pct(traffic: pd.Series) -> float:
    """% of non-traffic laps in a 'Lap Traffic?' series. NaN if none are known."""
    known = traffic.dropna()
    return (known == 'No').mean() * 100 if len(known) else np.nan
