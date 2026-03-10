import os
import requests
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# 1. 初始化與讀取環境變數 (加上 .strip() 預防隱藏字元)
load_dotenv()
url = os.environ.get("SUPABASE_URL", "").strip()
key = os.environ.get("SUPABASE_KEY", "").strip()
tg_token = os.environ.get("TELEGRAM_TOKEN", "").strip()
tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

supabase = create_client(url, key)

def send_telegram_msg(message):
    """發送訊息至 Telegram 機器人"""
    api_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": tg_chat_id,
        "text": message,
        "parse_mode": "Markdown"  # 使用 Markdown 讓訊息更美觀
    }
    try:
        response = requests.post(api_url, data=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"發送失敗: {e}")

def check_and_alert():
    # 2. 查詢溢價率為負數的標的 (premium_percent < 0)
    # 從你之前建立的 View: profitable_bonds_list 讀取
    try:
        res = supabase.table("profitable_bonds_list").select("*").lt("premium_percent", 0).execute()
        bonds = res.data
        
        if bonds:
            # 建立華爾街風格的警報訊息
            msg = "🔔 *[CB 套利警報 - 負溢價發現]* 🔔\n\n"
            for bond in bonds:
                msg += f"📊 *{bond['bond_name']}* ({bond['bond_code']})\n"
                msg += f" ├ 溢價率: `{bond['premium_percent']}%` 🚨\n"
                msg += f" ├ 現股參考價: `{bond['stock_ref_price']}`\n"
                msg += f" └ 最後更新: {bond['last_updated']}\n"
                msg += "----------------------------\n"
            
            send_telegram_msg(msg)
            print(f"成功發送 {len(bonds)} 檔標的警報！")
        else:
            print("目前市場穩定，無負溢價標的。")
            
    except Exception as e:
        print(f"資料庫查詢錯誤: {e}")

if __name__ == "__main__":
    check_and_alert()