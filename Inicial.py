import streamlit as st

# Header image and title
st.image('header.png', use_container_width=True)
st.title('Instructions')
st.subheader('Data from 2025 Rounds')

# Main data filtering information
st.info(
    "All data shown is filtered to include only laps within 4% of the fastest lap of the session "
    "and from drivers who completed at least 50% of the total laps completed by the session leader."
)

# Clarifying how 'Race' and 'Practice' pages differ
st.info(
    "**Note on 'Race' vs. 'Practice' pages:**\n"
    "- The visualizations are the same on both pages.\n"
    "- The difference lies in the data aggregation method:\n"
    "    - **Race:** lap times and speeds are averaged across valid laps.\n"
    "    - **Practice:** only the best times and highest speeds are used per driver."
)

# General description of the dashboard
st.markdown("""
### Overview
This dashboard provides performance data from multiple 2025 racing sessions, divided by series and session type.

Each racing series has a dedicated page. Data from one series cannot be analyzed through another series' page.

If you'd like to see data for **Nascar Brasil**, a structured CSV with lap-by-lap data is required.
""")

# Summary of the types of session analysis
st.subheader("Session Analysis Criteria")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Race Sessions")
    st.markdown("- Data processed using **average lap time** and **average top speed** per driver.")
    st.markdown("- Intended to reflect overall race pace and consistency.")

with col2:
    st.markdown("#### Practice & Qualifying")
    st.markdown("- Data processed using each driver's **best lap time** and **highest top speed**.")
    st.markdown("- Intended to reflect maximum single-lap performance.")

# Optional section for explaining the charts
with st.expander("How to interpret the charts"):
    st.write("- All charts are based on time and speed data.")
    st.write("- Gaps are displayed in time deltas relative to the session leader.")
    st.write("- Lines and colors represent individual drivers or data groupings.")



