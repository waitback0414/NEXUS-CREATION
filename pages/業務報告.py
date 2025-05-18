import streamlit as st

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("ログインしてください。")
    st.stop()

st.title("業務報告")
st.write(f"こんにちは、{st.session_state['username']}さん！")
