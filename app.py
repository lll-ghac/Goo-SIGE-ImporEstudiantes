import streamlit as st

pg = st.navigation([
    st.Page("pages/E_Ecuador.py", title="E-Ecuador"),
    st.Page("pages/Otra_Escuelita.py", title="Otra Escuelita"),
    st.Page("pages/Tutorial.py", title="Tutorial"),
])
pg.run()
