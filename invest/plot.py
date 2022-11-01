import plotly.graph_objects as go
from toolz.functoolz import juxt
import pandas as pd

def plot_candle(price_data, indicators=[]):

    layout = go.Layout(
        yaxis=dict(title="Price"),
        yaxis2=dict(title="Volume", overlaying="y", side="right"),
    )

    technical_indicators = juxt(indicators)(price_data)

    prices_date = pd.to_datetime(price_data["Date"])

    fig = go.Figure(
        layout=layout,
        data=[
            go.Candlestick(
                x=prices_date,
                open=price_data["Open"],
                high=price_data["High"],
                low=price_data["Low"],
                close=price_data["Close"],
                yaxis="y1",
                name="Price",
            ),
            go.Bar(
                x=prices_date,
                y=price_data["Volume"],
                name="Volume",
                marker={"color": "blue"},
                yaxis="y2",
            ),
        ]
        + list(technical_indicators),
    )

    fig.update(layout_yaxis_range=[0, max(price_data["High"] * 1.1)])
    return fig