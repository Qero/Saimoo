import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta


def render_candlestick(df: pd.DataFrame, title: str = "K线图"):
    """绘制交互式 K 线图"""
    if df.empty:
        return go.Figure()

    # Ensure date is string format YYYY-MM-DD for category axis
    # This prevents Plotly from interpreting it as datetime with time component
    df = df.copy()
    # Ensure index is sorted 0..N for consistent x-axis mapping
    df = df.sort_values('date').reset_index(drop=True)
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

    # Create subplots: 2 rows (Price, Volume), shared x-axis
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(title, "成交量"), row_width=[0.2, 0.7]
    )

    # 1. Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["date_str"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="K线"
        ),
        row=1,
        col=1,
    )

    # 2. MA Lines
    # Standard MAs: 5, 10, 20, 30, 60, 120, 250
    ma_periods = [5, 10, 20, 30, 60, 120, 250]
    # Use a color palette or let Plotly auto-assign colors
    # To keep it clean, maybe we only show a few by default or make them toggleable in legend
    for ma in ma_periods:
        ma_col = f"ma{ma}"
        if len(df) >= ma:
            df[ma_col] = df["close"].rolling(window=ma).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date_str"],
                    y=df[ma_col],
                    mode="lines",
                    name=f"MA{ma}",
                    line=dict(width=1),  # Thin lines to avoid clutter
                ),
                row=1,
                col=1,
            )

    # 3. Volume Bar
    # Color volume bars based on price change
    colors = ["red" if row["close"] >= row["open"] else "green" for i, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df["date_str"], y=df["volume"], marker_color=colors, name="成交量"), row=2, col=1)

    # Layout updates
    fig.update_layout(
        xaxis_rangeslider_visible=False,  # Disable default rangeslider
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
    )

    # Hide non-trading days gaps by using category axis
    # Calculate ticks for the first trading day of each month

    # Find indices where month changes
    # Since data is daily, we can check if month of current row != month of previous row
    # The first row is always a tick candidate
    df["month"] = df["date"].dt.to_period("M")
    # Use boolean indexing to find the first occurrence of each month
    monthly_ticks = df.drop_duplicates(subset=["month"], keep="first")

    tick_vals = monthly_ticks["date_str"].tolist()
    tick_text = monthly_ticks["date"].dt.strftime("%Y-%m").tolist()

    fig.update_xaxes(type="category", tickmode="array", tickvals=tick_vals, ticktext=tick_text, tickangle=0)
    
    # Set default range to last 1 year (approx 250 trading days or calculated by date)
    # Since we use category axis, range is based on index [0, len-1]
    # We set the range using update_xaxes(range=[...]) which is more robust for subplots
    if len(df) > 0:
        end_idx = len(df) - 1 + 0.5 # Add padding for the last candle
        
        latest_date = df['date'].iloc[-1]
        start_date_limit = latest_date - timedelta(days=365)
        
        # Find index of first date >= start_date_limit
        start_idx = 0
        filtered = df[df['date'] >= start_date_limit]
        if not filtered.empty:
            start_idx = filtered.index[0] - 0.5 # Subtract padding for the first candle
            
        fig.update_xaxes(range=[start_idx, end_idx])
    
    return fig
