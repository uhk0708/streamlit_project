# streamlit_app.py
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.title("간단한 캔버스")

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=5,
    stroke_color="#000000",
    background_color="#FFFFFF",
    height=400,
    width=600,
    drawing_mode="freedraw",
    key="canvas",
)

if st.button("초기화"):
    st.experimental_rerun()

if canvas_result.image_data is not None:
    st.image(canvas_result.image_data)
