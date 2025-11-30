import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import datetime as dt
    import warnings

    import kand as ka
    import marimo as mo
    import plotly.graph_objs as go
    import polars as pl
    import yfinance_pl as yf

    warnings.simplefilter("ignore")
    return go, ka, mo, pl, yf


@app.cell
def _(mo):
    mo.md("""
    # 単純移動平均線（SMA）による株価分析

    ## 移動平均線とは？

    **移動平均線（Moving Average）** は、一定期間の株価の平均値を結んだ線です。
    株価のトレンドを把握するための最も基本的なテクニカル指標の一つです。

    ### 単純移動平均線（SMA: Simple Moving Average）

    単純移動平均線は、過去n日間の終値を単純に平均した値です。

    $$
    SMA_n = \frac{P_1 + P_2 + ... + P_n}{n}
    $$

    - $P_i$: i日目の終値
    - $n$: 期間（日数）

    ### このノートで使用する移動平均線

    | 移動平均線 | 期間 | 用途 |
    |-----------|------|------|
    | **SMA5** | 5日 | 短期トレンドの把握 |
    | **SMA25** | 25日 | 中期トレンドの把握 |

    ### 売買シグナル

    - **ゴールデンクロス**: 短期線（SMA5）が長期線（SMA25）を下から上に突き抜ける → **買いシグナル**
    - **デッドクロス**: 短期線（SMA5）が長期線（SMA25）を上から下に突き抜ける → **売りシグナル**
    """)
    return


@app.cell
def _(mo):
    stock_code = mo.ui.text("8381.T", placeholder="8381.T")
    mo.md(
        f"""
        ## 証券コードを入力する

        {stock_code}

        > 例: `7203.T`（トヨタ）、`9984.T`（ソフトバンクグループ）、`8381.T`（山陰合同銀行）
        """
    )
    return (stock_code,)


@app.cell
def _(mo):
    mo.md("""
    ## 株価データの取得

    `yfinance-pl`を使用してYahoo Financeから過去1年分の株価データを取得します。
    """)
    return


@app.cell
def _(stock_code, yf):
    ticker = yf.Ticker(stock_code.value)
    info = ticker.info
    hist = ticker.history(period="1y")
    hist
    return hist, info


@app.cell
def _(mo):
    mo.md("""
    ## 移動平均線の計算

    `kand`ライブラリの`sma()`関数を使用して、5日と25日の単純移動平均線を計算します。

    ```python
    ma5 = ka.sma(close, period=5)   # 5日移動平均
    ma25 = ka.sma(close, period=25) # 25日移動平均
    ```
    """)
    return


@app.cell
def _(hist, ka, pl):
    close = hist["close.amount"].to_numpy().astype("float64")
    hist_with_ma = hist.with_columns(
        ma5=pl.Series(ka.sma(close, period=5)),
        ma25=pl.Series(ka.sma(close, period=25)),
    )
    hist_with_ma
    return (hist_with_ma,)


@app.cell
def _(mo):
    mo.md("""
    ## チャートの可視化

    Plotlyを使用してローソク足チャートと移動平均線を描画します。

    - **ローソク足**: 日々の始値・高値・安値・終値を表示
      - 赤: 陽線（終値 > 始値）
      - 緑: 陰線（終値 < 始値）
    - **青線（SMA5）**: 5日移動平均線（短期トレンド）
    - **水色線（SMA25）**: 25日移動平均線（中期トレンド）
    """)
    return


@app.cell
def _(go, hist_with_ma, info, pl, stock_code):
    company_name = info.get("shortName", stock_code.value)
    ma_layout = {
        "height": 560,
        "width": 1028,
        "title": {
            "text": f"{company_name}の株価",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24, "weight": "bold"},
        },
        "xaxis": {
            "rangeslider": {"visible": False},
            "title": {"text": "日付"},
        },
        "yaxis1": {
            "domain": [0.05, 1.0],
            "title": "価格(JPY)",
            "side": "left",
            "tickformat": ",",
        },
        "legend": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
    }

    # Decimalを浮動小数点に変換（Int64は小数点以下を失う）
    df_plot = hist_with_ma.with_columns(
        [
            pl.col("open.amount").cast(pl.Float64),
            pl.col("high.amount").cast(pl.Float64),
            pl.col("low.amount").cast(pl.Float64),
            pl.col("close.amount").cast(pl.Float64),
        ]
    )
    dates = df_plot["date"].to_list()

    ma_data = [
        go.Candlestick(
            yaxis="y1",
            x=dates,
            open=df_plot["open.amount"],
            high=df_plot["high.amount"],
            low=df_plot["low.amount"],
            close=df_plot["close.amount"],
            increasing_line_color="red",
            decreasing_line_color="green",
            name=f"{company_name}の株価",
        ),
        go.Scatter(
            yaxis="y1",
            x=dates,
            y=df_plot["ma5"],
            name="SMA5",
            line={"color": "royalblue", "width": 1.2},
        ),
        go.Scatter(
            yaxis="y1",
            x=dates,
            y=df_plot["ma25"],
            name="SMA25",
            line={"color": "lightseagreen", "width": 1.2},
        ),
    ]

    ma_fig = go.Figure(data=ma_data, layout=go.Layout(ma_layout))

    # 月ごとにラベルを表示（各月の最初の取引日）
    month_indices = []
    month_labels = []
    prev_month = None
    for i, d in enumerate(dates):
        if prev_month != d.month:
            month_indices.append(dates[i])
            month_labels.append(d.strftime("%Y-%m"))
            prev_month = d.month

    ma_fig.update_layout(
        {
            "xaxis": {
                "showgrid": False,
                "tickmode": "array",
                "tickvals": month_indices,
                "ticktext": month_labels,
                "tickangle": -45,
            }
        }
    )
    ma_fig
    return


@app.cell
def _(mo):
    mo.md("""
    ## ゴールデンクロス・デッドクロスの検出

    移動平均線のクロスを検出して売買シグナルを特定します。

    ### 検出ロジック

    ```python
    # 前日と当日のSMA5とSMA25の差分を計算
    diff = SMA5 - SMA25
    prev_diff = diff.shift(1)

    # ゴールデンクロス: 前日は SMA5 < SMA25、当日は SMA5 > SMA25
    golden_cross = (prev_diff < 0) & (diff > 0)

    # デッドクロス: 前日は SMA5 > SMA25、当日は SMA5 < SMA25
    dead_cross = (prev_diff > 0) & (diff < 0)
    ```

    ### シグナルの解釈

    | シグナル | 意味 | 推奨アクション |
    |---------|------|---------------|
    | ゴールデンクロス | 上昇トレンドへの転換 | 買い検討 |
    | デッドクロス | 下降トレンドへの転換 | 売り検討 |

    > **注意**: クロスシグナルは遅行指標です。実際の売買判断には他の指標との組み合わせが推奨されます。
    """)
    return


@app.cell
def _(hist_with_ma, pl):
    # SMA5とSMA25の差分を計算
    df_cross = (
        hist_with_ma.with_columns(
            diff=(pl.col("ma5") - pl.col("ma25")),
        )
        .with_columns(
            prev_diff=pl.col("diff").shift(1),
        )
        .with_columns(
            # ゴールデンクロス: 前日は負（SMA5 < SMA25）、当日は正（SMA5 > SMA25）
            golden_cross=(pl.col("prev_diff") < 0) & (pl.col("diff") > 0),
            # デッドクロス: 前日は正（SMA5 > SMA25）、当日は負（SMA5 < SMA25）
            dead_cross=(pl.col("prev_diff") > 0) & (pl.col("diff") < 0),
        )
    )

    # ゴールデンクロスの日付を抽出
    golden_crosses = df_cross.filter(pl.col("golden_cross")).select(
        pl.col("date"),
        pl.col("close.amount").alias("price"),
        pl.lit("ゴールデンクロス").alias("signal"),
    )

    # デッドクロスの日付を抽出
    dead_crosses = df_cross.filter(pl.col("dead_cross")).select(
        pl.col("date"),
        pl.col("close.amount").alias("price"),
        pl.lit("デッドクロス").alias("signal"),
    )

    # シグナルを統合して日付順にソート
    signals = pl.concat([golden_crosses, dead_crosses]).sort("date")
    return (signals,)


@app.cell
def _(mo, pl, signals):
    n_golden = signals.filter(pl.col("signal") == "ゴールデンクロス").height
    n_dead = signals.filter(pl.col("signal") == "デッドクロス").height

    mo.md(
        f"""
        ### 検出結果

        - **ゴールデンクロス**: {n_golden}回
        - **デッドクロス**: {n_dead}回
        """
    )
    return


@app.cell
def _(signals):
    signals
    return


@app.cell
def _(mo):
    mo.md("""
    ## シグナル付きチャート

    ゴールデンクロス・デッドクロスをチャート上にマーカーで表示します。

    - **▲ 緑マーカー**: ゴールデンクロス（買いシグナル）
    - **▼ 赤マーカー**: デッドクロス（売りシグナル）
    """)
    return


@app.cell
def _(go, hist_with_ma, info, pl, signals, stock_code):
    _company_name = info.get("shortName", stock_code.value)

    # Decimalを浮動小数点に変換
    _df_plot = hist_with_ma.with_columns(
        [
            pl.col("open.amount").cast(pl.Float64),
            pl.col("high.amount").cast(pl.Float64),
            pl.col("low.amount").cast(pl.Float64),
            pl.col("close.amount").cast(pl.Float64),
        ]
    )
    _dates = _df_plot["date"].to_list()

    # ゴールデンクロスとデッドクロスのデータを分離
    _golden = signals.filter(pl.col("signal") == "ゴールデンクロス")
    _dead = signals.filter(pl.col("signal") == "デッドクロス")

    _signal_data = [
        go.Candlestick(
            yaxis="y1",
            x=_dates,
            open=_df_plot["open.amount"],
            high=_df_plot["high.amount"],
            low=_df_plot["low.amount"],
            close=_df_plot["close.amount"],
            increasing_line_color="red",
            decreasing_line_color="green",
            name=f"{_company_name}の株価",
        ),
        go.Scatter(
            yaxis="y1",
            x=_dates,
            y=_df_plot["ma5"],
            name="SMA5",
            line={"color": "royalblue", "width": 1.2},
        ),
        go.Scatter(
            yaxis="y1",
            x=_dates,
            y=_df_plot["ma25"],
            name="SMA25",
            line={"color": "lightseagreen", "width": 1.2},
        ),
        # ゴールデンクロスのマーカー
        go.Scatter(
            yaxis="y1",
            x=_golden["date"].to_list(),
            y=_golden["price"].cast(pl.Float64).to_list(),
            mode="markers",
            name="ゴールデンクロス",
            marker={
                "symbol": "triangle-up",
                "size": 15,
                "color": "lime",
                "line": {"color": "darkgreen", "width": 2},
            },
        ),
        # デッドクロスのマーカー
        go.Scatter(
            yaxis="y1",
            x=_dead["date"].to_list(),
            y=_dead["price"].cast(pl.Float64).to_list(),
            mode="markers",
            name="デッドクロス",
            marker={
                "symbol": "triangle-down",
                "size": 15,
                "color": "red",
                "line": {"color": "darkred", "width": 2},
            },
        ),
    ]

    _signal_layout = {
        "height": 560,
        "width": 1028,
        "title": {
            "text": f"{_company_name}の株価（シグナル付き）",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24, "weight": "bold"},
        },
        "xaxis": {
            "rangeslider": {"visible": False},
            "title": {"text": "日付"},
        },
        "yaxis1": {
            "domain": [0.05, 1.0],
            "title": "価格(JPY)",
            "side": "left",
            "tickformat": ",",
        },
        "legend": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
    }

    signal_fig = go.Figure(data=_signal_data, layout=go.Layout(_signal_layout))

    # 月ごとにラベルを表示
    _month_indices = []
    _month_labels = []
    _prev_month = None
    for _i, _d in enumerate(_dates):
        if _prev_month != _d.month:
            _month_indices.append(_dates[_i])
            _month_labels.append(_d.strftime("%Y-%m"))
            _prev_month = _d.month

    signal_fig.update_layout(
        {
            "xaxis": {
                "showgrid": False,
                "tickmode": "array",
                "tickvals": _month_indices,
                "ticktext": _month_labels,
                "tickangle": -45,
            }
        }
    )
    signal_fig


if __name__ == "__main__":
    app.run()
