# sc_shared.py
# Shared constants and utility functions used by both Race and Practice modules.

import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

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
# Shared helper functions
# ---------------------------------------------------------------------------

def enrich_session(sessao: pd.DataFrame) -> pd.DataFrame:
    """
    Add Team, Manufacturer and Driver columns to a raw session DataFrame.
    Returns the same DataFrame (modified in place for efficiency).
    """
    sessao['Team']         = sessao['Car_ID'].map(TEAMS_DICT)
    sessao['Manufacturer'] = sessao['Team'].map(TEAM_TO_MANUFACTURER)
    sessao['Driver']       = sessao['Car_ID'].map(DRIVERS_DICT)
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

def highlight_driver(s: pd.Series) -> list[str]:
    return [
        f"background-color: {COLORS_DRIVER[v][0]}; color: {COLORS_DRIVER[v][1]}"
        if v in COLORS_DRIVER else ''
        for v in s
    ]

def highlight_team(s: pd.Series) -> list[str]:
    return [
        f"background-color: {COLORS_TEAM[v][0]}; color: {COLORS_TEAM[v][1]}"
        if v in COLORS_TEAM else ''
        for v in s
    ]

def highlight_manufacturer(s: pd.Series) -> list[str]:
    return [
        f"background-color: {COLORS_MANUFACTURER[v][0]}; color: {COLORS_MANUFACTURER[v][1]}"
        if v in COLORS_MANUFACTURER else ''
        for v in s
    ]


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
