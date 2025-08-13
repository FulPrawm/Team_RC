 # Importando as bibliotecas
import streamlit as st

#header
st.image('header.png')
st.title('Instructions')
st.header('Data from 2025 rounds')
st.write('Please select the desired option on the menu on the left')
st.write('All data is filtered with laps inside a 4% gap of the fastest lap of the session and at least 50% of the laps completed for the leader')
st.write('Race - graphs relative to the timeboard of the races by AVERAGE time/speed')
st.write('Practice - graphs relative to the timeboard of practices and qualy by FASTEST time/HIGHEST speed')
st.write("Each Series has their own page, you CAN'T select a Stock Car page and expect GT Series data")
st.write("If you guys want a Nascar Brasil page, you need to give me their CSV lap-by-lap file, because there's no way Im going to do it by hand")
