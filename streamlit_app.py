import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

# 1. 初始化與讀取環境變數
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# 2. 設定網頁標題
st.set_page_config(page_title="CB 自動化監控儀表板", layout="wide")
st.title("📈 可轉債自動化監控系統")
st.subheader("由文學系 AI 微學程開發")

# 3. 從 Supabase 讀取資料
# 我們直接讀取你之前建立的 SQL View: profitable_bonds_list
def get_data():
    response = supabase.table("profitable_bonds_list").select("*").execute()
    return pd.DataFrame(response.data)

df = get_data()

# 4. 側邊欄過濾器
st.sidebar.header("篩選條件")
max_premium = st.sidebar.slider("最高溢價率 (%)", -5.0, 10.0, 1.0)

# 5. 顯示數據與視覺化
filtered_df = df[df['premium_percent'] <= max_premium]

col1, col2 = st.columns(2)

with col1:
    st.write(f"### 低溢價標的清單 (共 {len(filtered_df)} 檔)")
    st.dataframe(filtered_df, use_container_width=True)

with col2:
    st.write("### 溢價率分布圖")
    if not filtered_df.empty:
        st.bar_chart(data=filtered_df, x="bond_name", y="premium_percent")
    else:
        st.warning("目前沒有符合條件的標的 QWQ")