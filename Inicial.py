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
    st.markdown("- Data processed using **average time** and **average speed** per driver/team/manufacturer.")
    st.markdown("- Intended to reflect overall race pace and consistency.")

with col2:
    st.markdown("#### Practice & Qualifying")
    st.markdown("- Data processed using each driver/team/manufacturer's **best time** and **highest speed**.")
    st.markdown("- Intended to reflect maximum single-lap/sector performance.")

# Optional section for explaining the charts
with st.expander("How to interpret the charts"):
    st.write("- All charts are based on the data provided by the category timeboard provider (Chronon for Stock Car and Cronoelo for GT Series).")
    st.write("- Gaps are displayed in time deltas relative to the race.")
    st.write("- Lines, colors, boxes and dots represent individual drivers or data groupings.")

# New section for the "Watch" page
st.subheader("Watch Page")
st.info(
    "The **Watch** page provides real-time information on the weekend sessions, including:\n"
    "- **Current Day & Time:** shows the current date and time.\n"
    "- **Session Schedule:** start and end times for each session.\n"
    "- **Elapsed Time & Time Remaining:** tracks how long a session has been running and how much time is left.\n"
    "- **Next Session Info:** displays the upcoming session, its duration, and countdown until it begins.\n"
)

st.markdown("""
### Overview
The Watch page helps you stay updated with the weekend racing schedule. It allows you to quickly know:
- Which session is currently running.
- How long it has been running.
- When the next session will start.
- The total duration of each session.
- Countdown timers for upcoming sessions.
""")



