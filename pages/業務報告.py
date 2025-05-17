import streamlit as st

if st.session_state.get("role") != "user":
    st.warning("このページは通常ユーザー専用です。")
    st.stop()

st.title("業務報告")
st.write("ここに通常ユーザー向けの機能を実装します。")
