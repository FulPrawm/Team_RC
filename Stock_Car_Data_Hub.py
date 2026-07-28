import os
import streamlit as st

# ======================================
# Password Gate
# ======================================

def _check_password() -> bool:
    """Returns True if the user has entered the correct password."""

    def _submit():
        if st.session_state["pwd_input"] == "Meinharc#01":
            st.session_state["authenticated"] = True
        else:
            st.session_state["auth_error"] = True

    if st.session_state.get("authenticated"):
        return True

    st.title("Race Analysis System")
    st.subheader("🔒 Please enter the password to continue")

    st.text_input(
        "Password",
        type="password",
        key="pwd_input",
        on_change=_submit,
        placeholder="Enter password and press Enter",
    )

    if st.session_state.get("auth_error"):
        st.error("Incorrect password. Please try again.")
        st.session_state["auth_error"] = False

    return False


if not _check_password():
    st.stop()

# ======================================
# Imports (only after auth)
# ======================================

from Data.Y25.Stock_Car_2025_Race_Data import show as show_race_2025
from Data.Y25.Stock_Car_2025_Practice_Data import show as show_practice_2025
from Data.Y26.Stock_Car_2026_Race_Data import show as show_race_2026
from Data.Y26.Stock_Car_2026_Practice_Data import show as show_practice_2026
from Data.Y26.Stock_Car_2026_Round_Analysis import show as show_round_2026
from Data.Y26.Stock_Car_2026_Season_Analysis import show as show_season_2026

# ======================================
# Sidebar Configuration Panel
# ======================================

st.title("Race Analysis System")

with st.sidebar:
    st.header("Session Configuration")

    year_options = ["Select a year...", "2025", "2026"]
    selected_year = st.selectbox("Choose the year:", year_options)

    session_options = ["Select a session...", "Race Data", "Practice Data", "Round Analysis", "Season Analysis"]
    selected_session = st.selectbox("Choose the session:", session_options)

# ======================================
# Navigation Logic
# ======================================

if selected_year == "Select a year...":
    st.info("Please select a year to begin the analysis.")

elif selected_session == "Select a session...":
    st.warning("Please select a session type.")

else:
    if selected_year == "2025":
        if selected_session == "Race Data":
            show_race_2025()
        elif selected_session == "Practice Data":
            show_practice_2025()

    elif selected_year == "2026":
        if selected_session == "Race Data":
            show_race_2026()
        elif selected_session == "Practice Data":
            show_practice_2026()
        elif selected_session == "Round Analysis":
            show_round_2026()
        elif selected_session == "Season Analysis":
            show_season_2026()
