from datetime import date, timedelta

import pandas as pd
import streamlit as st

from saimoo.services.data_service import DataService
from saimoo.utils.types import AdjustType
from saimoo.web.components import render_candlestick

st.set_page_config(page_title="Saimoo Quant", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def get_service():
    return DataService()


@st.cache_data(ttl=3600 * 24)
def get_stock_options_cached():
    """Cache the stock list data"""
    try:
        import akshare as ak

        df = ak.stock_info_a_code_name()
        if df.empty:
            return ["600000 | 浦发银行"]
        # Convert code to string and pad if necessary (akshare usually returns 6 digits)
        df["code"] = df["code"].astype(str).str.zfill(6)
        return [f"{row['code']} | {row['name']}" for _, row in df.iterrows()]
    except Exception:
        return ["600000 | 浦发银行 (API Error)"]


def main():
    service = get_service()

    # --- Sidebar ---
    st.sidebar.title("Saimoo 📈")

    # Stock Selection
    stock_options = get_stock_options_cached()

    # Default index for 600000
    default_idx = 0
    for i, opt in enumerate(stock_options):
        if opt.startswith("600000"):
            default_idx = i
            break

    selected_stock = st.sidebar.selectbox(
        "股票选择", options=stock_options, index=default_idx, help="支持搜索股票代码或名称"
    )

    # Parse selected stock
    if " | " in selected_stock:
        symbol, stock_name_val = selected_stock.split(" | ", 1)
    else:
        symbol = selected_stock
        stock_name_val = symbol

    # Date Range
    # start_date and end_date removed as per user request
    # We load all available local data
    
    # Adjust Type
    adjust_map = {"不复权": AdjustType.NONE, "前复权": AdjustType.QFQ, "后复权": AdjustType.HFQ}
    adjust_label = st.sidebar.selectbox("复权类型", list(adjust_map.keys()), index=1)
    adjust = adjust_map[adjust_label]

    # Action Buttons
    if st.sidebar.button("查询数据", type="primary"):
        st.session_state["trigger_query"] = True

    st.sidebar.markdown("---")
    # Sync 5 years (1825 days) of data
    if st.sidebar.button("同步数据 (最近5年)"):
        with st.spinner(f"正在同步 {symbol}..."):
            count = service.sync_data(symbol, days=1825, adjust=adjust)
            if count > 0:
                st.sidebar.success(f"成功同步 {count} 条数据")
            else:
                st.sidebar.warning("未获取到新数据")

    # --- Main Area ---
    st.title(f"{stock_name_val}")

    # Load Data
    # Only load data when trigger_query is True or if it's the first run (default)
    # But since streamlit reruns the whole script on interaction, we just load based on current inputs.
    # To optimize, we could use st.session_state to store the dataframe, but for now let's keep it simple.

    with st.spinner("加载数据中..."):
        # Always use local source for reading
        # Use a wide date range to fetch all available local data
        # Or better, update DataService to support fetching all data without date filter if None passed
        # But for now, let's just use a very early start date
        early_start = date(2000, 1, 1)
        future_end = date.today() + timedelta(days=1)
        df = service.get_bars_dataframe(symbol, early_start, future_end, adjust, source="local")

    if df.empty:
        st.warning(f"未找到 {symbol} 的本地数据。")
        st.info("提示: 本地数据库可能无数据，请尝试点击侧边栏的「同步数据」。")
        return

    # 1. Header Metrics
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # Check if latest bar is today (incomplete day)
    # If so, show amount/turnover from previous day
    is_today = latest["date"].date() == date.today()
    metrics_source = prev if is_today and len(df) > 1 else latest
    metrics_date_label = f" ({metrics_source['date'].date()})" if is_today else ""

    change = latest["close"] - prev["close"]
    pct = (change / prev["close"]) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新收盘", f"{latest['close']:.2f}", f"{change:.2f} ({pct:.2f}%)")
    col2.metric("成交量 (手)", f"{latest['volume'] / 100:.0f}")
    col3.metric(f"成交额 (万){metrics_date_label}", f"{metrics_source['amount'] / 10000:.2f}")
    col4.metric(
        f"换手率{metrics_date_label}",
        f"{metrics_source['turnover']:.3f}%" if pd.notnull(metrics_source["turnover"]) else "N/A",
    )

    # 2. Chart
    st.plotly_chart(render_candlestick(df, title=f"{stock_name_val} {adjust_label}"), use_container_width=True)

    # 3. Data Table
    with st.expander("查看历史数据明细"):
        st.dataframe(
            df.sort_values("date", ascending=False).style.format(
                {
                    "open": "{:.2f}",
                    "high": "{:.2f}",
                    "low": "{:.2f}",
                    "close": "{:.2f}",
                    "volume": "{:.0f}",
                    "pct_chg": "{:.2f}%",
                    "amount": "{:.0f}",
                },
                na_rep="--",  # Handle None/NaN values gracefully
            ),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
