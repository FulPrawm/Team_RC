import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

st.title("📊 Relatório PowerPoint")

# Link RAW do GitHub
ppt_url = "https://raw.githubusercontent.com/FulPrawm/Team_RC/main/Data/Y26/26ET01_STOCK%20CAR%20_CURVELO_PR%C3%89%20ETAPA.pptx"

# Encode da URL
encoded_url = urllib.parse.quote(ppt_url, safe="")

# Viewer Microsoft
viewer_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"

components.iframe(viewer_url, height=900)