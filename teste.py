import streamlit as st
from Stock_Car_2025_Race_Data import show as show_race
from Stock_Car_2025_Practice_Data import show as show_practice

st.title("Race Analysis System")

modo = st.selectbox(
    "Select the type of session:",
    ["Race Data", "Practice Data"]
)

if modo == "Race Data":
    show_race()
else:
    show_practice()
