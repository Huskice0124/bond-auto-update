import os
import streamlit as st
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# 1. 初始化與環境變數
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# --- 資料抓取函式 ---

def get_current_bonds():
    """抓取目前所有可轉債的最新狀態"""
    response = supabase.table("convertible_bonds").select("*").execute()
    return pd.DataFrame(response.data)

def get_bond_history(bond_code):
    """抓取特定債券的歷史價格紀錄"""
    # 1. 這裡的 stock_ref_price 改成 stock_price (或你資料庫裡真實的名稱)
    response = supabase.table("bond_history") \
        .select("created_at, stock_price") \
        .eq("bond_code", bond_code) \
        .order("created_at", desc=False) \
        .execute() 
    
    if not response.data:
        return None
        
    df = pd.DataFrame(response.data)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Asia/Taipei')
    df = df.set_index('created_at')
    return df
        
    df = pd.DataFrame(response.data)
    # 轉換時間並校正為台灣時區 (+8)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Asia/Taipei')
    df = df.set_index('created_at')
    return df

# --- Streamlit 介面設計 ---

st.set_page_config(page_title="可轉債 AI 監控系統", layout="wide")

st.title("📈 可轉債套利監控面板")
st.markdown("這是一個結合 **AI 微學程** 自動化流程與 **金融數據分析** 的實驗專題。")

# --- 區塊一：即時監控清單 ---
st.header("🔍 目前市場標的")
df_current = get_current_bonds()

if not df_current.empty:
    # 整理表格欄位名稱，讓它更直觀
    display_df = df_current[['bond_code', 'stock_ref_price', 'last_updated']].copy()
    display_df.columns = ['債券代碼', '最新現股價格', '最後更新時間']
    
    # 使用 dataframe 顯示，並加上高度自適應
    st.dataframe(display_df, use_container_width=True)
else:
    st.warning("目前資料庫中沒有數據，請檢查 GitHub Actions 是否正常執行。")

st.divider()

# --- 區塊二：歷史趨勢分析 (Option B) ---
st.header("🕰 歷史走勢追蹤")

if not df_current.empty:
    # 動態產生下拉選單：從資料庫現有的代碼中提取
    all_bond_codes = df_current['bond_code'].unique().tolist()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_code = st.selectbox("請選擇債券代碼", all_bond_codes)
        st.info(f"正在顯示 {selected_code} 的歷史變動趨勢。")
        
    with col2:
        df_history = get_bond_history(selected_code)
        
        if df_history is not None:
            # 畫出折線圖
            st.line_chart(df_history['stock_ref_price'])
        else:
            st.warning("該標的目前尚無歷史紀錄，請等待自動腳本累積數據。")
else:
    st.info("暫無選單資料。")

# --- 側邊欄：專題資訊 ---
with st.sidebar:
    st.header("關於本專題")
    st.write("👨‍💻 開發者：文學系跨 AI 開發者")
    st.write("🤖 技術棧：Python, Supabase, GitHub Actions, Streamlit")
    if st.button("手動重新整理數據"):
        st.rerun()