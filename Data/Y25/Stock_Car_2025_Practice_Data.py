# Stock_Car_2025_Practice_Data.py
# 2025 uses the same practice/qualifying report as 2026; only the season lookups differ (see sc_shared.SEASONS).
from Data.Y26.Stock_Car_2026_Practice_Data import show as _show


def show():
    _show(year=2025)
