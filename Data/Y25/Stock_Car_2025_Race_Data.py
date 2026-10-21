# Stock_Car_2025_Race_Data.py
# 2025 uses the same race report as 2026; only the season lookups differ (see sc_shared.SEASONS).
from Data.Y26.Stock_Car_2026_Race_Data import show as _show


def show():
    _show(year=2025)
