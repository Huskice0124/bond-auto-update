import os
import yfinance as yf
from supabase import create_client
# dotenv package is imported as `dotenv`, not python_dotenv
from dotenv import load_dotenv
import time

# 1. 初始化環境變數與 Supabase 客戶端
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ 錯誤：找不到 SUPABASE_URL 或 SUPABASE_KEY 環境變數。")
    exit(1)

supabase = create_client(url, key)

def get_taiwan_stock_price(bond_code):
    """
    將 5 碼的可轉債代碼 (例如 11011) 轉為 4 碼現股代碼 (1101)，
    並嘗試從 yfinance 抓取價格（包含上市 .TW 與 上櫃 .TWO）。
    """
    # 取前四碼作為現股代碼
    base_code = str(bond_code)[:4]
    
    # 台股可能上市 (.TW) 或上櫃 (.TWO)，嘗試兩種後綴
    for suffix in [".TW", ".TWO"]:
        ticker_symbol = f"{base_code}{suffix}"
        try:
            ticker = yf.Ticker(ticker_symbol)
            # 使用 fast_info 獲取最新成交價，效率較高
            price = ticker.fast_info.last_price
            
            # 檢查價格是否合法 (非 NaN 且大於 0)
            if price and price > 0:
                return price, ticker_symbol
        except Exception:
            continue
            
    return None, None

def main():
    print("🚀 開始執行可轉債現股價格更新任務...")
    
    # 2. 從 Supabase 抓取所有債券代碼
    # 注意：這裡對應你建立的欄位名稱 bond_code
    try:
        response = supabase.table("convertible_bonds").select("bond_code").execute()
        bonds = response.data
    except Exception as e:
        print(f"❌ 無法從 Supabase 讀取資料: {e}")
        return

    if not bonds:
        print("⚠️ 資料庫中沒有任何債券資料。")
        return

    updated_count = 0
    
    # 3. 逐一更新價格
    for record in bonds:
        bond_code = record['bond_code']
        
        # 獲取最新股價
        current_price, resolved_ticker = get_taiwan_stock_price(bond_code)
        
        if current_price:
            try:
                # 4. 更新 Supabase 中的 stock_ref_price 與 last_updated
                supabase.table("convertible_bonds") \
                    .update({
                        "stock_ref_price": current_price,
                        "last_updated": "now()" # 使用資料庫內建時間
                    }) \
                    .eq("bond_code", bond_code) \
                    .execute()
                # 🚀 4-2. 新增：同步寫入歷史紀錄表 (Option B 的核心)
                history_record = {
                    "bond_code": bond_code,
                    "stock_ref_price": current_price
                }
                supabase.table("bond_history").insert(history_record).execute()
                
                print(f"✅ 更新成功並存入歷史: 債券 {bond_code} 價格: {current_price}")
                updated_count += 1
                
            except Exception as e:
                print(f"❌ 處理債券 {bond_code} 時發生錯誤: {e}")
                
                print(f"✅ 更新成功: 債券 {bond_code} -> 現股 {resolved_ticker} 價格: {current_price}")
                updated_count += 1
            except Exception as e:
                print(f"❌ 更新債券 {bond_code} 時發生錯誤: {e}")
        else:
            print(f"⚠️ 無法找到債券 {bond_code} 對應的現股價格。")
        
        # 稍微延遲避免頻繁請求被 yfinance 封鎖
        time.sleep(0.5)

    print(f"\n✨ 任務完成！共更新 {updated_count} 筆資料。")

if __name__ == "__main__":
    main()