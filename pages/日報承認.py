import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# ====== 認証とクライアント取得 ======
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "予約一覧"

@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(credentials)


# ====== データ取得関数 ======
def load_pending_reports():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
    data = sheet.get_all_values()

    headers = data[2]  # 3行目: ヘッダー
    records = data[3:]  # 4行目以降: データ

    df = pd.DataFrame(records, columns=headers)
    df["行番号"] = range(4, 4 + len(df))  # 実スプレッドシートの行番号を記録

    # 承認されていない行だけ抽出（T列＝index=19）
    df = df[df[df.columns[19]].fillna("") != "承認"]

    # 登録日列を日付型に変換
    try:
        df["登録日"] = pd.to_datetime(df["登録日"])
    except:
        df["登録日"] = pd.NaT

    return df, sheet


# ====== UIと処理 ======
def main():
    if st.session_state.get("role") != "admin":
        st.warning("このページは管理者専用です。")
        st.stop()

    st.title("📝 日報承認ページ")

    df, sheet = load_pending_reports()

    # --- サイドバー：絞り込み ---
    st.sidebar.subheader("🔍 絞り込み条件")

    unique_dates = df["登録日"].dt.date.dropna().unique()
    unique_users = df["報告者"].dropna().unique()

    selected_date = st.sidebar.selectbox("登録日で絞り込み", options=["全て"] + sorted(map(str, unique_dates)))
    selected_user = st.sidebar.selectbox("報告者で絞り込み", options=["全て"] + sorted(unique_users))

    if selected_date != "全て":
        df = df[df["登録日"].dt.date == datetime.strptime(selected_date, "%Y-%m-%d").date()]
    if selected_user != "全て":
        df = df[df["報告者"] == selected_user]

    if df.empty:
        st.info("該当する未承認の日報はありません。")
        return

    # フラグ & コメント初期化
    if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
        st.session_state.approval_flags = [False] * len(df)

    if "reject_comments" not in st.session_state or len(st.session_state.reject_comments) != len(df):
        st.session_state.reject_comments = [""] * len(df)

    st.subheader("📋 承認対象一覧")

    # for i, row in df.reset_index(drop=True).iterrows():
    #     unique_key = f"{row['ID']}_{i}"  # ID + index をキーに
    #     cols = st.columns([0.05, 0.7, 0.25])
    #     st.session_state.approval_flags[i] = cols[0].checkbox("", key=f"chk_{unique_key}")
    #     cols[1].markdown(
    #         f"**ID:** {row['ID']}｜**登録日:** {row['登録日'].strftime('%Y/%m/%d')}｜"
    #         f"**報告者:** {row['報告者']}｜**報告:** {row['報告']}"
    #     )
    #     st.session_state.reject_comments[i] = cols[2].text_input("却下コメント", value=st.session_state.reject_comments[i], key=f"comment_{unique_key}")
    
    for i, row in df.reset_index(drop=True).iterrows():
    unique_key = f"{row['ID']}_{i}"
    cols = st.columns([0.05, 0.7, 0.25])
    st.session_state.approval_flags[i] = cols[0].checkbox("", key=f"chk_{unique_key}")
    
    date_str = row["登録日"].strftime("%Y/%m/%d") if pd.notnull(row["登録日"]) else "未登録"
    
    cols[1].markdown(
        f"**ID:** {row['ID']}｜**登録日:** {date_str}｜"
        f"**登録者:** {row['登録者']}｜**報告:** {row['報告']}"
    )
    
    st.session_state.reject_comments[i] = cols[2].text_input(
        "却下コメント", value=st.session_state.reject_comments[i], key=f"comment_{unique_key}"
    )

    
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 承認する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    sheet.update_cell(int(row_num), 20, "承認")  # T列
            st.success("承認完了！")
            st.rerun()

    with col2:
        if st.button("❌ 却下する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    comment = st.session_state.reject_comments[i]
                    sheet.update_cell(int(row_num), 20, comment or "却下")
            st.warning("却下完了！")
            st.rerun()


if __name__ == "__main__":
    main()
