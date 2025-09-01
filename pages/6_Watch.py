import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # stdlib (Python 3.9+)

# ------------------------
# Configuration
# ------------------------
st.set_page_config(page_title="Session Panel", layout="centered")
st_autorefresh(interval=1000, limit=None)  # auto-refresh every 1s

# ------------------------
# Timezone (UTC-3)
# ------------------------
tz = ZoneInfo("America/Sao_Paulo")  # use "America/Sao_Paulo" for UTC-3 (handles DST)

# ------------------------
# Session schedule (keep same format)
# ------------------------
sessions = [
    {"name": "SD", "start": "2025-09-05 09:00", "duration": 35},
    {"name": "FP1", "start": "2025-09-05 11:20", "duration": 65},
    {"name": "FP2", "start": "2025-09-05 15:25", "duration": 65},
    {"name": "Q1 - Group 1", "start": "2025-09-06 15:35", "duration": 8},
    {"name": "Q1 - Group 2", "start": "2025-09-06 16:05", "duration": 8},
    {"name": "Q2", "start": "2025-09-06 16:05", "duration": 8},
    {"name": "Q3", "start": "2025-09-06 16:05", "duration": 8},
    {"name": "Race 1", "start": "2025-09-06 14:33", "duration": 30},
    {"name": "Race 2", "start": "2025-09-07 14:10", "duration": 50},
]

# Convert start times into timezone-aware datetime objects (UTC-3)
for s in sessions:
    # parse naive datetime then attach tzinfo (no time shift)
    naive = datetime.strptime(s["start"], "%Y-%m-%d %H:%M")
    start_dt = naive.replace(tzinfo=tz)
    s["start_dt"] = start_dt
    s["end_dt"] = start_dt + timedelta(minutes=s["duration"])

# ------------------------
# Layout
# ------------------------
st.markdown("<h1 style='text-align:center;'>Session Panel</h1>", unsafe_allow_html=True)

# Current time and date (server time converted to UTC-3)
now = datetime.now(tz)
st.markdown(
    f"""
    <div style='text-align:center; font-size:40px; font-weight:bold;'>
        {now.strftime('%H:%M:%S')} ({now.tzname()})
    </div>
    <div style='text-align:center; font-size:20px;'>
        {now.strftime('%d/%m/%Y')}
    </div>
    """,
    unsafe_allow_html=True
)

# Detect current and next session
current_session = None
next_session = None
for i, s in enumerate(sessions):
    if s["start_dt"] <= now < s["end_dt"]:
        current_session = s
        if i + 1 < len(sessions):
            next_session = sessions[i + 1]
        break
    if now < s["start_dt"]:
        next_session = s
        break

# ---------------- Current Session ----------------
if current_session:
    elapsed = now - current_session["start_dt"]
    remaining = current_session["end_dt"] - now
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Current Session: {current_session['name']}</h2>
            <p><b>Start:</b> {current_session['start_dt'].strftime('%d/%m %H:%M %Z')} &nbsp;&nbsp; 
               <b>End:</b> {current_session['end_dt'].strftime('%d/%m %H:%M %Z')}</p>
            <p><b>Elapsed Time:</b> {str(elapsed).split('.')[0]} &nbsp;&nbsp;
               <b>Remaining Time:</b> {str(remaining).split('.')[0]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#2e7d32; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Current Session: -</h2>
            <p><b>Start:</b> - &nbsp;&nbsp; <b>End:</b> -</p>
            <p><b>Elapsed Time:</b> - &nbsp;&nbsp; <b>Remaining Time:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- Next Session ----------------
if next_session:
    countdown = next_session["start_dt"] - now
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Next Session: {next_session['name']}</h2>
            <p><b>Start:</b> {next_session['start_dt'].strftime('%d/%m %H:%M %Z')}</p>
            <p><b>Duration:</b> {next_session['duration']:02d} min</p>
            <p><b>Countdown:</b> <span style='font-size:30px; color:#00e676;'>
            {str(countdown).split('.')[0]}</span></p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='background:#424242; color:white; padding:20px; border-radius:15px; margin-top:20px;'>
            <h2>Next Session: -</h2>
            <p><b>Start:</b> -</p>
            <p><b>Duration:</b> -</p>
            <p><b>Countdown:</b> -</p>
        </div>
        """,
        unsafe_allow_html=True
    )
