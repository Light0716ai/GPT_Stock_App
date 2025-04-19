import streamlit as st
import yfinance as yf
from openai import OpenAI
import datetime
import requests

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

us_stocks = ["NVDA", "TSLA", "PLTR"]
tw_stocks = ["0056.TW", "2409.TW", "3035.TW"]

def check_openai_quota():
    try:
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"
        }
        sub_url = "https://api.openai.com/v1/dashboard/billing/subscription"
        sub_resp = requests.get(sub_url, headers=headers)
        limit = sub_resp.json().get("hard_limit_usd", 0)

        usage_url = "https://api.openai.com/v1/dashboard/billing/usage"
        today = datetime.date.today().isoformat()
        start_date = datetime.date.today().replace(day=1).isoformat()
        usage_url += f"?start_date={start_date}&end_date={today}"
        usage_resp = requests.get(usage_url, headers=headers)
        used = usage_resp.json().get("total_usage", 0) / 100
        remaining = limit - used
        return f"OpenAI 使用額度：${used:.2f} / ${limit:.2f}（剩餘 ${remaining:.2f}）"
    except Exception as e:
        return f"⚠️ 無法查詢 API 額度：{str(e)}"

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

def analyze_with_gpt(stock_data, label="台股"):
    text = f"以下是{label}股票清單與資訊：\n"
    for s in stock_data:
        text += f"- {s['代號']} {s['名稱']}（價格：{s['價格']}，本益比：{s['PE']}）\n"
    text += "請從中選出三檔最有機會在一個月內上漲 100% 的股票，並說明原因（用繁體中文簡潔說明）。"

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "user", "content": text}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT 錯誤：{str(e)}"

st.title("本週 GPT 股票潛力分析")
st.caption("這個工具每週自動分析台股與美股，找出最有機會在一個月內翻倍的潛力股（使用 GPT 分析）")
st.text(check_openai_quota())

def render_stock_section(title, data, explanation, is_tw=False):
    st.subheader(title)
    block = ""
    lines = explanation.strip().split("\n")
    for i in range(len(data)):
        symbol = data[i]["代號"]
        name = data[i]["名稱"]
        price = data[i]["價格"]
        cur = "元" if is_tw else "$"
        explanation_line = lines[i] if i < len(lines) else ""
        block += f"{symbol:<6}{name:<10}{cur}{price}\n"
        block += f"GPT {explanation_line.strip()}\n\n"
    st.text(block)

if st.button("開始本週分析"):
    with st.spinner("分析中..."):
        us_data = get_stock_data(us_stocks)
        tw_data = get_stock_data(tw_stocks)

        us_result = analyze_with_gpt(us_data, "美股")
        tw_result = analyze_with_gpt(tw_data, "台股")

        render_stock_section("美股", us_data, us_result, is_tw=False)
        render_stock_section("台股", tw_data, tw_result, is_tw=True)

        today = datetime.date.today()
        st.caption(f"更新時間：{today}")
else:
    st.info("請按下上方按鈕開始分析。")
