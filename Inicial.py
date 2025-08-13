import streamlit as st

# Header image and title
st.image('header.png', use_column_width=True)
st.title('🏎️ Instructions')
st.header('📅 Data from 2025 Rounds')

# Key data filtering info
st.info("📌 All data is filtered to include only laps within 4% of the fastest lap and with at least 50% of the leader's lap count.")

# Introductory explanation
st.markdown("""
### 👇 What you’ll find in this dashboard:
- **Race**: Graphs based on **average lap times** during races.
- **Practice**: Comparisons based on **fastest laps** and **top speeds**.
- **Series**: Each series has its own page.

⚠️ **Important:** You can't view data from one series on another's page.  
To add **Nascar Brasil**, I’ll need the lap-by-lap CSV file — I’m not doing that by hand 😅
""")

# Navigation summary section
st.subheader("🔍 Explore the Available Data")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏁 Race Sessions")
    st.markdown("- Average lap time graphs")
    st.markdown("- Driver comparisons")
    st.markdown("- Real-time gap charts")

with col2:
    st.markdown("### 🛠️ Practice & Qualifying")
    st.markdown("- Fastest laps")
    st.markdown("- Top speeds")
    st.markdown("- Stint-based comparisons")

# FAQ / Help section
with st.expander("❓ How to read the graphs?"):
    st.write("- Average lap times reflect race pace.")
    st.write("- Graphs show real gaps based on time, not position.")
    st.write("- Colors and lines represent different drivers or stints.")

# Season highlights (example metrics)
st.subheader("📈 2025 Season Highlights")
col1, col2, col3 = st.columns(3)
col1.metric("Fastest in Qualifying", "Driver X", "-0.153s")
col2.metric("Best Race Average", "Driver Y", "1:34.872")
col3.metric("Top Speed", "Driver Z", "312.4 km/h")
