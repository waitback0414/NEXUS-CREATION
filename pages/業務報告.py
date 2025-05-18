import streamlit as st

if st.session_state.get("role") != "user":
    st.warning("このページは通常ユーザー専用です。")
    st.stop()

st.title("業務報告")
st.write("ここに通常ユーザー向けの機能を実装します。")

if "authentication_status" in st.session_state and st.session_state["authentication_status"]:
    st.write(f"ようこそ、{st.session_state['ID']}さん！")
