import streamlit as st
from Data.Y25.Stock_Car_2025_Race_Data import show as show_race_2025
from Data.Y25.Stock_Car_2025_Practice_Data import show as show_practice_2025
# Future:
# from Data.Y26.Stock_Car_2026_Race_Data import show as show_race_2026
# from Data.Y26.Stock_Car_2026_Practice_Data import show as show_practice_2026

st.title("Race Analysis System")

# ===============================
# Year Selection
# ===============================

year_options = ["Select a year...", "2025", "2026"]
selected_year = st.sidebar.selectbox("Choose the year:", year_options)

# ===============================
# Session Selection
# ===============================

session_options = ["Select a session...", "Race Data", "Practice Data"]
selected_session = st.sidebar.selectbox("Choose the session:", session_options)

# ===============================
# Page Logic
# ===============================

if selected_year == "Select a year...":
    st.info("Please select a year to continue.")

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
            st.info("Race 2026 not implemented yet.")
            # show_race_2026()
        elif selected_session == "Practice Data":
            st.info("Practice 2026 not implemented yet.")
            # show_practice_2026()
