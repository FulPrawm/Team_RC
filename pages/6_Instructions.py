import streamlit as st

# Header image and title
st.image('header.png', use_container_width=True)
st.title('Instructions')
st.subheader('Data by Year and Session')

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
This dashboard provides performance data from multiple racing sessions, organized by **year** and session type.

Before accessing Race or Practice data, the user must select the desired **year** from the sidebar.

Each racing series has a dedicated page. Data from one series cannot be analyzed through another series' page.
""")

# Summary of the types of session analysis
st.subheader("Session Analysis Criteria")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Race Sessions")
    st.markdown("- Data processed using **average time** and **average speed** per driver/team/manufacturer.")
    st.markdown("- Intended to reflect overall race pace and consistency.")

with col2:
    st.markdown("#### Practice Sessions")
    st.markdown("- Data processed using each driver/team/manufacturer's **best time** and **highest speed**.")
    st.markdown("- Intended to reflect maximum single-lap/sector performance.")

# Optional section for explaining the charts
with st.expander("How to interpret the charts"):
    st.write("- All charts are based on the data provided by the category timeboard provider (Chronon for Stock Car).")
    st.write("- Gaps are displayed in time deltas relative to the session.")
    st.write("- Lines, colors, boxes, and dots represent individual drivers or data groupings.")

# Section for the Watch page
st.subheader("Watch Page")
st.info(
    "The **Watch** page provides real-time information on the weekend sessions and allows you to edit session times directly from the page, without accessing the code.\n"
    "- **Current Day & Time:** shows the current date and time.\n"
    "- **Session Schedule:** start and end times for each session (editable).\n"
    "- **Elapsed Time & Time Remaining:** tracks how long a session has been running and how much time is left.\n"
    "- **Next Session Info:** displays the upcoming session, its duration, and countdown until it begins."
)

st.markdown("""
### Overview
The Watch page helps you stay updated with the weekend racing schedule. You can quickly know:
- Which session is currently running.
- How long it has been running.
- When the next session will start.
- The total duration of each session.
- Countdown timers for upcoming sessions.
- Edit session times directly from the page.
""")

# Section for the MoTeC Graphs page
st.subheader("MoTeC Graphs Page")
st.info(
    "The **MoTeC Graphs** page allows you to generate scatter plot reports from MoTeC data.\n"
    "- You first generate an Excel report from the MoTeC software.\n"
    "- Modify the Excel file as needed.\n"
    "- Open the modified Excel directly from this page to create scatter plot visualizations."
)

st.markdown("""
### Overview
This page is intended for advanced data analysis and visualization:
- Generates scatter plots to analyze lap-by-lap data and trends.
- Requires pre-processing the Excel files before loading.
- Helps visualize performance differences between drivers, laps, and sessions.
""")
