import streamlit as st

if "username" in st.session_state:
    st.write(f"こんにちは、{st.session_state['username']}さん！")
else:
    st.warning("ログインしてください。")
    st.stop()

st.title("業務報告")
st.write("ここに通常ユーザー向けの機能を実装します。")
