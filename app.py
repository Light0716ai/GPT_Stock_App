import streamlit as st
import yfinance as yf
from openai import OpenAI
import datetime

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

us_stocks = ["NVDA", "TSLA", "PLTR"]
tw_stocks = ["0056.TW", "2409.TW", "3035.TW"]

# 查詢 GPT 帳號配額
def check_openai_quota():
    try:
        billing_info = client.billing.usage()
        quota_info = client.billing.subscription()
        used = billing_info.get("total_usage", 0) / 100  # 轉成 USD
        limit = quota_info.get("hard_limit_usd", 0)
        remaining = limit - used
        return f"🧾 OpenAI 使用額度：${used:.2f} / ${limit:.2f}（剩餘 ${remaining:.2f}）"
    except Exception as e:
        return f"⚠️ 無法查詢 API 額度：{str(e)}"

# 抓股價資訊
def get_stock_data(tickers):
    stock_list = []
    for symbol in tickers:
        stock = yf.Ticker(symbol)
        info = stock.info
        price = info.get("currentPrice", "N/A")
        name = info.get("shortName", "N/A")
        pe = info.get("trailingPE", "N/A")
        stock_list.append({
            "代號": symbol,
            "名稱": name,
            "價格": price,
            "PE": pe
        })
    return stock_list

# 呼叫 GPT 產生分析
def analyze_with_gpt(stock_data, label="台股"):
    text = f"以下是{label}股票清單與資訊：\n"
    for s in stock_data:
        text += f"- {s['代號']} {s['名稱']}（價格：{s['價格']}，本益比：{s['PE']}）\n"
    text += "請從中選出三檔最有機會在一個月內上漲 100% 的股票，並說明原因（用繁體中文簡潔說明）。"

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "user", "content": text}
            ]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT 錯誤：{str(e)}"

# ===== UI 顯示區 =====
st.markdown("""
<style>
    .main {
        background-color: #f6f6f6;
        padding: 2rem;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #333333;
    }
    .section {
        background-color: white;
        border-radius: 16px;
        padding: 20px;
        margin-top: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .btn {
        font-size: 1rem;
        padding: 0.6rem 1.2rem;
        border-radius: 12px;
        background-color: #0044cc;
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">📊 本週 GPT 股票潛力分析</div>', unsafe_allow_html=True)
st.caption("這個工具每週自動分析台股與美股，找出最有機會在一個月內翻倍的潛力股（使用 GPT 分析）")

st.markdown(check_openai_quota())

if st.button("🔍 開始本週分析"):
    with st.spinner("正在抓取股票資料與生成分析..."):
        us_data = get_stock_data(us_stocks)
        tw_data = get_stock_data(tw_stocks)

        us_result = analyze_with_gpt(us_data, "美股")
        tw_result = analyze_with_gpt(tw_data, "台股")

        st.markdown('<div class="section">🇺🇸 <b>GPT 分析：美股推薦</b></div>', unsafe_allow_html=True)
        st.code(us_result, language="markdown")

        st.markdown('<div class="section">🇹🇼 <b>GPT 分析：台股推薦</b></div>', unsafe_allow_html=True)
        st.code(tw_result, language="markdown")

        today = datetime.date.today()
        st.caption(f"更新時間：{today}")
else:
    st.info("請按下上方按鈕開始分析。")
