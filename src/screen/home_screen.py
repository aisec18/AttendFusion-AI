import streamlit as st
from src.components.header import header_home
from src.ui.base_layout import style_background_home, style_base_layout, style_background_dashboard
from src.components.footer import footer_home
def home_screen():
   
    style_background_home()
    style_base_layout()
    
    header_home()

    col1, col2 = st.columns(2,gap="large")

    with col1:
        st.header("I am student")
        st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=120)
        if st.button('student portal',type='primary'):
            st.session_state['login_type'] = 'student'
            st.rerun()

    with col2:
        st.header("I am teacher")
        st.image("https://i.ibb.co/CsmQQV6X/mascot-prof.png", width=145)
        if st.button('teacher portal',type='primary'):
            st.session_state['login_type'] = 'teacher'
            st.rerun()
    footer_home()