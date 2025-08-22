import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# ------------------------
# Configuration
# ------------------------
st.set_page_config(page_title="Session Panel", layout="centered")

# Auto-refresh every 1 second
st_autorefresh(interval=1000, limit=None)

# ------------------------
# Session schedule
# ------------------------
sessions = [
    {"name": "Free Practice 1", "start": "2025-08-22 15:00", "duration": 40},  # Friday
    {"name": "Free Practice 2", "start": "2025-08-22 18:00", "duration": 40},  # Friday
    {"name": "Qualifying - Group 1", "start": "2025-08-23 15:35", "duration": 20}, # Saturday
    {"name": "Qualifying - Group 2", "start": "2025-08-23 16:05", "duration": 20}, # Saturday
    {"name": "Race 1", "start": "2025-08-23 18:00", "duration": 50},               # Saturday
    {"name": "Race 2", "start": "2025-08-24 13:00", "duration": 50},               # Sunday
]

# Convert start times into datetime objects
for s in sessions:
    start_dt = datetime.strptime(s["start"], "%Y-%m-%d %H:%M")
    s["start_dt"] = start_dt
    s["end_dt"] = start_dt + timedelta(minutes=s["duration"])

# ------------------------
# Layout
# ------------------------
st.markdown("<h1 style='text-align:center;'>Session Panel</h1>", unsafe_allow_html=True)

# Current time and date
now = datetime.now()
st.markdown(
    f"""
    <div style='text-align:center; font-size:40px; font-weight:bold;'>
        {now.strftime('%H:%M:%S')}
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
            <p><b>Start:</b> {current_session['start_dt'].strftime('%d/%m %H:%M')} &nbsp;&nbsp; 
               <b>End:</b> {current_session['end_dt'].strftime('%d/%m %H:%M')}</p>
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
            <p><b>Start:</b> {next_session['start_dt'].strftime('%d/%m %H:%M')}</p>
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
