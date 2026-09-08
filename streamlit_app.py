import streamlit as st

st.set_page_config(
    page_title="English → Hindi AI Dubbing",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 English → Hindi AI Dubbing")
st.write(
    "Upload an English video and create a Hindi dubbed version."
)

uploaded_file = st.file_uploader(
    "Upload English video",
    type=["mp4", "mkv", "mov", "webm", "avi", "m4v"],
)

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

    st.video(uploaded_file)

    st.info(
        "Upload is working. The AI processing pipeline will be connected next."
    )