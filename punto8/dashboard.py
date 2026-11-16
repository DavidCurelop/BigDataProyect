from __future__ import annotations

import json
import os
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def fetch_api(path: str, params: Optional[dict] = None) -> pd.DataFrame:
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    query = f"?{urllib.parse.urlencode(clean)}" if clean else ""
    with urllib.request.urlopen(f"{API_BASE_URL}{path}{query}", timeout=15) as resp:
        return pd.DataFrame(json.loads(resp.read().decode("utf-8")))


@st.cache_data(ttl=300)
def cached_api(path: str, params: Optional[dict] = None) -> pd.DataFrame:
    return fetch_api(path, params)


def main() -> None:
    st.set_page_config(page_title="S&P 500 Lakehouse Dashboard", layout="wide")
    st.title("S&P 500 Equities Lakehouse — Analytics")
    st.caption(f"API Endpoint: `{API_BASE_URL}`")

    try:
        sectors_df = cached_api("/sectors").sort_values("market_cap_rank")
        gainers_df = cached_api("/top-gainers", {"limit": 505}).sort_values("overall_rank")
        leaders_df = cached_api("/volume-leaders", {"limit": 5}).sort_values(["sector", "sector_volume_rank"])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        st.error(f"Cannot reach analytics API at {API_BASE_URL}: {exc}")
        st.stop()

    sector_names = ["All", *sorted(sectors_df["sector"].dropna().unique().tolist())]
    chosen_sector = st.sidebar.selectbox("Sector Filter", sector_names)

    filtered_gainers = gainers_df if chosen_sector == "All" else gainers_df[gainers_df["sector"] == chosen_sector]
    tickers = sorted(filtered_gainers["ticker"].dropna().unique().tolist())
    chosen_ticker = st.sidebar.selectbox("Ticker (Price & SMA-50)", tickers, index=tickers.index("AAPL") if "AAPL" in tickers else 0)
    lookback_days = st.sidebar.slider("Lookback Trading Days", min_value=30, max_value=252, value=180, step=15)

    top_gainer = filtered_gainers.iloc[0]
    top_vol_sector = sectors_df.sort_values("avg_daily_volume", ascending=False).iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tracked Tickers", len(filtered_gainers))
    c2.metric("Top Gainer", f"{top_gainer['ticker']}", f"{top_gainer['total_return_pct']:.2f}%")
    c3.metric("Top Market-Cap Sector", sectors_df.iloc[0]["sector"], f"${sectors_df.iloc[0]['sector_market_cap'] / 1e12:.2f}T")
    c4.metric("Highest Avg Volume Sector", top_vol_sector["sector"], f"{top_vol_sector['avg_daily_volume'] / 1e6:.2f}M/day")

    st.subheader(f"{chosen_ticker} — Close Price vs SMA-50 & Volume (Q4 & Q5)")
    hist_df = cached_api(f"/stocks/{urllib.parse.quote(chosen_ticker)}", {"days": lookback_days})
    if not hist_df.empty:
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        latest = hist_df.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Latest Close", f"${latest['close']:.2f}")
        m2.metric("SMA-50", f"${latest['sma_50']:.2f}")
        m3.metric("% vs SMA-50", f"{latest['pct_vs_sma50']:.2f}%")
        ret = latest.get("daily_return_pct")
        m4.metric("Daily Return", f"{ret:.2f}%" if pd.notna(ret) else "N/A")
        st.line_chart(hist_df.set_index("date")[["close", "sma_50"]])
        st.bar_chart(hist_df.set_index("date")[["volume"]])

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Top 15 Sectors by Avg Daily Volume (Q2)")
        st.bar_chart(sectors_df.nlargest(15, "avg_daily_volume").set_index("sector")[["avg_daily_volume"]])
    with col_right:
        st.subheader("Top 15 Gainers by Total Return % (Q1)")
        st.bar_chart(filtered_gainers.head(15).set_index("ticker")[["total_return_pct"]])

    st.subheader("Sector Risk vs Return (Q3 & Q4)")
    st.scatter_chart(sectors_df, x="daily_volatility_pct", y="avg_daily_return_pct")
    st.dataframe(
        sectors_df[["market_cap_rank", "sector", "num_companies", "sector_market_cap", "avg_daily_volume", "avg_daily_return_pct", "daily_volatility_pct"]],
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Top Volume Leaders by Sector (Q2)")
    filtered_leaders = leaders_df if chosen_sector == "All" else leaders_df[leaders_df["sector"] == chosen_sector]
    st.dataframe(filtered_leaders, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
