import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import datetime

# 管理者のみアクセス可
if st.session_state.get("role") != "admin":
    st.error("このページは管理者のみアクセス可能です。")
    st.stop()

# 認証設定
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "予約一覧"

@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

# データ取得関数
def fetch_pending_reports():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
    data = sheet.get_all_values()

    if len(data) < 3:
        return pd.DataFrame(), sheet

    headers = data[2]
    records = data[3:]

    df = pd.DataFrame(records, columns=headers)
    
    # 必要な列だけ抜粋 & T列（"承認"）が空欄の行のみ
    cols_to_display = ["ID", "登録日", "登録者", "ゴルフ場", "業務", "報告", "ラウンド数", "チェック", "エラー箇所"]
    column_indices = [0, 10, 11, 13, 14, 15, 16, 18, 20]
    
    filtered = [row for row in records if len(row) > 19 and row[19].strip() != "承認"]
    df_filtered = pd.DataFrame(filtered, columns=headers).iloc[:, column_indices]

    # 日付ソート（登録日列が18列目→index=17）
    df_filtered["登録日"] = pd.to_datetime(df_filtered["登録日"], errors='coerce')
    df_filtered = df_filtered.sort_values(by="登録日", ascending=False).reset_index(drop=True)

    return df_filtered, sheet

# ページUI
st.title("📝 日報承認（管理者専用）")

# 日付フィルター
selected_date = st.date_input("日付で絞り込む（登録日）", value=None)
df, sheet = fetch_pending_reports()

if selected_date:
    df = df[df["登録日"].dt.date == selected_date]

if df.empty:
    st.info("承認待ちの日報はありません。")
    st.stop()

# 承認チェックボックス列
if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
    st.session_state.approval_flags = [False] * len(df)

st.write("以下は未承認の日報一覧です：")

df, sheet = fetch_pending_reports()
st.session_state.approval_flags = [False] * len(df)  # ← ここで確実に初期化


# 表 + チェックボックス表示
for i, row in df.iterrows():
    cols = st.columns([0.05, 0.95])
    st.session_state.approval_flags[i] = cols[0].checkbox("", value=st.session_state.approval_flags[i], key=f"chk_{i}")
    cols[1].markdown(
        f"""
        **ID:** {row[0]}｜**登録日:** {row[1]}｜**登録者:** {row[2]}  
        **ゴルフ場:** {row[3]}｜**業務:** {row[4]}｜**報告:** {row[5]}  
        **ラウンド数:** {row[6]}｜**報告事項:** {row[7]}
        """
    )

# ボタンで処理
col_a, col_b = st.columns(2)
with col_a:
    if st.button("✅ 承認する"):
        for i, flag in enumerate(st.session_state.approval_flags):
            if flag:
                row_num = i + 3  # 実際の行番号（ヘッダー分オフセット）
                sheet.update_cell(row_num, 20, "承認")  # T列 → index=19 + 1
        st.success("承認を完了しました。")
        st.experimental_rerun()

with col_b:
    if st.button("❌ 却下する"):
        for i, flag in enumerate(st.session_state.approval_flags):
            if flag:
                row_num = i + 3
                sheet.update_cell(row_num, 20, "却下")
        st.warning("却下を完了しました。")
        st.experimental_rerun()

