import streamlit as st
import yfinance as yf
import openai
import datetime

openai.api_key = st.secrets["OPENAI_API_KEY"]

us_stocks = ["NVDA", "TSLA", "PLTR"]
tw_stocks = ["0056.TW", "2409.TW", "3035.TW"]

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

from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analyze_with_gpt(stock_data, label="台股"):
    text = f"以下是{label}股票清單與資訊：\n"
    for s in stock_data:
        text += f"- {s['代號']} {s['名稱']}（價格：{s['價格']}，本益比：{s['PE']}）\n"
    text += "請從中選出三檔最有機會在一個月內上漲 100% 的股票，並說明原因（用繁體中文簡潔說明）。"

    res = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return res.choices[0].message.content

st.title("📈 本週 GPT 股票潛力分析")
st.markdown("這個工具每週自動分析**台股與美股**，找出最有機會在一個月內翻倍的潛力股（使用 GPT 分析）")

if st.button("🔍 開始本週分析"):
    with st.spinner("正在抓取股票資料與生成分析..."):

        us_data = get_stock_data(us_stocks)
        tw_data = get_stock_data(tw_stocks)

        us_result = analyze_with_gpt(us_data, "美股")
        tw_result = analyze_with_gpt(tw_data, "台股")

        st.subheader("🇺🇸 GPT 分析：美股推薦")
        st.text(us_result)

        st.subheader("🇹🇼 GPT 分析：台股推薦")
        st.text(tw_result)

        today = datetime.date.today()
        st.caption(f"更新時間：{today}")

else:
    st.info("請按下上方按鈕開始分析。")
