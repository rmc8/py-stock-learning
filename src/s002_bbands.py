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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ボリンジャーバンドと時間軸

    ## 時間軸とボリンジャーバンド

    **異なる時間軸でのボリンジャーバンド適用**：
    - **日足**: 短期〜中期トレンド（数日〜数ヶ月）
    - **週足**: 中期トレンド（数週間〜数ヶ月）
    - **月足**: 長期トレンド（数ヶ月〜数年）
    - **分足**: リアルタイム取引（デイトレード）← ストリーミング処理で対応

    このノートでは、まず週足・月足でチャートを確認し、その後日足でバッチ処理とストリーミング処理を実装します。
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
def _(stock_code, yf):
    # 週足
    ticker = yf.Ticker(stock_code.value)
    info = ticker.info
    wkly = ticker.history(period="1y", interval="1wk")
    wkly  # 54 rows
    return info, ticker, wkly


@app.cell
def _(ticker):
    # 月足
    moly = ticker.history(period="1y", interval="1mo")
    moly  # 13rows
    return (moly,)


@app.cell
def _(go, info, moly, pl, stock_code, wkly):
    company_name = info.get("shortName", stock_code.value)

    def get_layout(label):
        return {
            "height": 560,
            "width": 1028,
            "title": {
                "text": f"{company_name}の株価({label})",
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

    def to_float64(df):
        return df.with_columns(
            [
                pl.col("open.amount").cast(pl.Float64),
                pl.col("high.amount").cast(pl.Float64),
                pl.col("low.amount").cast(pl.Float64),
                pl.col("close.amount").cast(pl.Float64),
            ]
        )

    def get_plot_data(df, dates):
        return [
            go.Candlestick(
                yaxis="y1",
                x=dates.to_list(),
                open=df["open.amount"],
                high=df["high.amount"],
                low=df["low.amount"],
                close=df["close.amount"],
                increasing_line_color="red",
                decreasing_line_color="green",
                name=f"{company_name}の株価",
            )
        ]

    wkly_layout = get_layout(label="週足")
    moly_layout = get_layout(label="月足")
    wkly_plot = to_float64(wkly)
    moly_plot = to_float64(moly)
    wkly_dates = wkly_plot["date"]
    moly_dates = moly_plot["date"]
    wkly_data = get_plot_data(wkly_plot, wkly_dates)
    moly_data = get_plot_data(moly_plot, moly_dates)
    return moly_data, moly_layout, wkly_data, wkly_layout


@app.cell
def _(go, wkly_data, wkly_layout):
    wkly_fig = go.Figure(data=wkly_data, layout=go.Layout(wkly_layout))
    wkly_fig
    return


@app.cell
def _(go, moly_data, moly_layout):
    moly_fig = go.Figure(data=moly_data, layout=go.Layout(moly_layout))
    moly_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ボリンジャーバンド
    """)
    return


@app.cell
def _(ticker):
    # 日足データを2年分取得（ボリンジャーバンド用）
    data = ticker.history(period="2y", interval="1d")
    data
    return (data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ボリンジャーバンド（日足データ）

    価格の変動範囲を統計的に表す指標。移動平均線±標準偏差でバンドを描画します。

    **構成**: ミドルバンド（SMA） ± 標準偏差×N

    | パラメータ | 値 | 説明 |
    |-----------|---|------|
    | 期間 | 20 | 20日間の移動平均と標準偏差 |
    | 偏差σ1 | 1.0 | 標準偏差の1倍 |
    | 偏差σ2 | 2.0 | 標準偏差の2倍（一般的） |

    **シグナル**: バンド幅拡大→ボラティリティ増加、価格がバンドに接触→買われすぎ/売られすぎ
    """)
    return


@app.cell
def _(data, ka, pl):
    import numpy as np

    # 終値をnumpy配列に変換
    close = data["close.amount"].to_numpy().astype("float64")

    # 偏差1.0のボリンジャーバンド
    bb_upper_1, bb_middle_1, bb_lower_1, _, _, _, _ = ka.bbands(
        close, period=20, dev_up=1.0, dev_down=1.0
    )

    # 偏差2.0のボリンジャーバンド
    bb_upper_2, bb_middle_2, bb_lower_2, _, _, _, _ = ka.bbands(
        close, period=20, dev_up=2.0, dev_down=2.0
    )

    # DataFrameに列を追加
    data_with_bb = data.with_columns(
        [
            pl.Series("bbands_upper_1", bb_upper_1),
            pl.Series("bbands_middle_1", bb_middle_1),
            pl.Series("bbands_lower_1", bb_lower_1),
            pl.Series("bbands_upper_2", bb_upper_2),
            pl.Series("bbands_middle_2", bb_middle_2),
            pl.Series("bbands_lower_2", bb_lower_2),
        ]
    )

    data_with_bb
    return close, data_with_bb


@app.cell
def _(data_with_bb, go, info, pl, stock_code):
    _company_name = info.get("shortName", stock_code.value)

    # Float64に変換
    _df_bb_plot = data_with_bb.with_columns(
        [
            pl.col("open.amount").cast(pl.Float64),
            pl.col("high.amount").cast(pl.Float64),
            pl.col("low.amount").cast(pl.Float64),
            pl.col("close.amount").cast(pl.Float64),
        ]
    )
    _dates_bb = _df_bb_plot["date"].to_list()

    _bb_data = [
        go.Candlestick(
            yaxis="y1",
            x=_dates_bb,
            open=_df_bb_plot["open.amount"],
            high=_df_bb_plot["high.amount"],
            low=_df_bb_plot["low.amount"],
            close=_df_bb_plot["close.amount"],
            increasing_line_color="red",
            decreasing_line_color="green",
            name=f"{_company_name}の株価",
        ),
        # ミドルバンド
        go.Scatter(
            yaxis="y1",
            x=_dates_bb,
            y=_df_bb_plot["bbands_middle_1"],
            name="ミドルバンド (SMA20)",
            line={"color": "blue", "width": 1.5},
        ),
        # 偏差1.0のバンド
        go.Scatter(
            yaxis="y1",
            x=_dates_bb,
            y=_df_bb_plot["bbands_upper_1"],
            name="σ1 上限",
            line={"color": "lightcoral", "width": 1.2, "dash": "dot"},
        ),
        go.Scatter(
            yaxis="y1",
            x=_dates_bb,
            y=_df_bb_plot["bbands_lower_1"],
            name="σ1 下限",
            line={"color": "lightcoral", "width": 1.2, "dash": "dot"},
        ),
        # 偏差2.0のバンド
        go.Scatter(
            yaxis="y1",
            x=_dates_bb,
            y=_df_bb_plot["bbands_upper_2"],
            name="σ2 上限",
            line={"color": "orange", "width": 1.5},
        ),
        go.Scatter(
            yaxis="y1",
            x=_dates_bb,
            y=_df_bb_plot["bbands_lower_2"],
            name="σ2 下限",
            line={"color": "orange", "width": 1.5},
        ),
    ]

    _bb_layout = {
        "height": 560,
        "width": 1028,
        "title": {
            "text": f"{_company_name}の株価（ボリンジャーバンド）",
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

    bb_fig = go.Figure(data=_bb_data, layout=go.Layout(_bb_layout))
    bb_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ストリーミング処理（リアルタイムデータ対応）

    **バッチ処理**（`ka.bbands()`）は過去データ全体を一括計算。
    **ストリーミング処理**（`ka.bbands_inc()` + ジェネレーター）はデータを1行ずつ処理し、
    リアルタイム更新（分足データなど）に対応します。

    ジェネレーターで前回の計算結果（SMA、合計、二乗合計）を保持し、
    新しいデータポイントごとに`ka.bbands_inc()`でインクリメンタル計算を実行します。
    """)
    return


@app.cell
def _(ka):
    def bbands_streaming(prices, period=20, dev_up=2.0, dev_down=2.0):
        """
        ジェネレーターを使ったボリンジャーバンドのストリーミング計算

        Args:
            prices: 価格のイテラブル（リスト、numpy配列など）
            period: ボリンジャーバンドの期間
            dev_up: 上方偏差倍数
            dev_down: 下方偏差倍数

        Yields:
            (upper, middle, lower, index): 各データポイントのボリンジャーバンド値
        """
        # 状態変数
        sma = None
        sum_val = 0.0
        sum_sq = 0.0
        buffer = []  # スライディングウィンドウ

        for idx, price in enumerate(prices):
            if len(buffer) < period:
                # ウォームアップ期間：期間分のデータが揃うまで
                buffer.append(price)
                sum_val += price
                sum_sq += price**2

                if len(buffer) == period:
                    # 初回のSMA計算
                    sma = sum_val / period

                yield (None, None, None, idx)
            else:
                # インクリメンタル計算
                old_price = buffer[0]
                upper, middle, lower, sma, sum_val, sum_sq = ka.bbands_inc(
                    price=price,
                    prev_sma=sma,
                    prev_sum=sum_val,
                    prev_sum_sq=sum_sq,
                    old_price=old_price,
                    period=period,
                    dev_up=dev_up,
                    dev_down=dev_down,
                )

                # バッファ更新
                buffer.append(price)
                buffer.pop(0)

                yield (upper, middle, lower, idx)

    return (bbands_streaming,)


@app.cell
def _(bbands_streaming, close, pl):
    # ジェネレーターでストリーミング処理を実行
    stream_results = list(bbands_streaming(close, period=20, dev_up=2.0, dev_down=2.0))

    # 結果をDataFrameに変換
    stream_upper = [r[0] for r in stream_results]
    stream_middle = [r[1] for r in stream_results]
    stream_lower = [r[2] for r in stream_results]

    stream_df = pl.DataFrame(
        {
            "index": list(range(len(stream_results))),
            "stream_upper": stream_upper,
            "stream_middle": stream_middle,
            "stream_lower": stream_lower,
        }
    )

    stream_df
    return (stream_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### ストリーミング処理の途中経過

    最初の50行のストリーミング処理結果を表示します。
    最初の20行（ウォームアップ期間）は`None`、その後インクリメンタル計算が開始されます。
    """)
    return


@app.cell
def _(stream_df):
    # 最初の50行を表示
    stream_df.head(50)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### バッチ計算 vs ストリーミング処理の比較

    ジェネレーターによるストリーミング処理とバッチ計算の結果を比較します。
    両者は数学的に同一なので、差分はほぼゼロ（浮動小数点誤差のみ）になるはずです。
    """)
    return


@app.cell
def _(data_with_bb, pl, stream_df):
    # バッチ計算結果とストリーミング結果を結合
    comparison_full = pl.DataFrame(
        {
            "index": stream_df["index"],
            "batch_upper": data_with_bb["bbands_upper_2"],
            "stream_upper": stream_df["stream_upper"],
            "batch_middle": data_with_bb["bbands_middle_2"],
            "stream_middle": stream_df["stream_middle"],
            "batch_lower": data_with_bb["bbands_lower_2"],
            "stream_lower": stream_df["stream_lower"],
        }
    ).with_columns(
        [
            # 差分計算（Noneを除外）
            pl.when(pl.col("stream_upper").is_not_null())
            .then((pl.col("batch_upper") - pl.col("stream_upper")).abs())
            .otherwise(None)
            .alias("diff_upper"),
            pl.when(pl.col("stream_middle").is_not_null())
            .then((pl.col("batch_middle") - pl.col("stream_middle")).abs())
            .otherwise(None)
            .alias("diff_middle"),
            pl.when(pl.col("stream_lower").is_not_null())
            .then((pl.col("batch_lower") - pl.col("stream_lower")).abs())
            .otherwise(None)
            .alias("diff_lower"),
        ]
    )

    # 統計サマリ
    comparison_summary = pl.DataFrame(
        {
            "指標": ["上限バンド", "ミドルバンド", "下限バンド"],
            "最大差分": [
                comparison_full["diff_upper"].max(),
                comparison_full["diff_middle"].max(),
                comparison_full["diff_lower"].max(),
            ],
            "平均差分": [
                comparison_full["diff_upper"].mean(),
                comparison_full["diff_middle"].mean(),
                comparison_full["diff_lower"].mean(),
            ],
        }
    )

    comparison_summary
    return (comparison_full,)


@app.cell
def _(comparison_full):
    # 最後の20行を表示（計算が安定している部分）
    comparison_full.tail(20)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ジェネレーターによる自動ストリーミング可視化

    ジェネレーター計算の結果を**自動アニメーション**でチャート表示します。

    ### 実装方法

    `mo.ui.refresh`（タイマー）と`mo.state`（状態管理）を組み合わせることで、
    データが徐々に追加されていく様子を**自動的に可視化**します。

    - **自動モード**: タイマーで0.1秒ごとにデータ行数が自動的に増加
    - **手動モード**: スライダーで任意の位置を確認可能

    ### 操作方法

    1. 自動アニメーションが開始され、チャートが徐々に描画される
    2. 手動スライダーで任意の時点を確認可能
    3. ストリーミング処理で「データが1行ずつ追加されていく」様子を視覚的に理解できる
    """)
    return


@app.cell
def _(mo, stream_df):
    # データ行数の最大値
    max_rows = len(stream_df)

    # 状態管理: 現在表示している行数（allow_self_loops=Trueで自己ループ可能）
    get_current_row, set_current_row = mo.state(20, allow_self_loops=True)

    # タイマー: 0.1秒ごとに発火
    timer = mo.ui.refresh(default_interval="0.1s")
    return get_current_row, max_rows, set_current_row, timer


@app.cell
def _(get_current_row, max_rows, set_current_row, timer):
    # タイマーを参照することで、このセルが0.1秒ごとに再実行される
    timer

    # 現在の行数を取得
    current = get_current_row()

    # まだ最大に達していなければ、行数を1増やす
    if current < max_rows:
        set_current_row(current + 1)
    return


@app.cell
def _(get_current_row, max_rows, mo, set_current_row):
    # 手動で行数を調整するスライダー
    manual_slider = mo.ui.slider(
        start=20,
        stop=max_rows,
        value=get_current_row(),
        step=1,
        label=f"表示するデータ行数（手動調整）",
        on_change=set_current_row,  # スライダー変更時に状態を更新
    )

    mo.md(f"""
    ### 自動/手動切り替え

    {manual_slider}

    現在の表示行数: **{get_current_row()}** / {max_rows}

    > **ヒント**: 自動アニメーションは常に実行中。スライダーを動かして任意の位置を確認できます。
    """)
    return


@app.cell
def _(data, get_current_row, go, info, pl, stock_code, stream_df):
    # 状態から現在の行数を取得
    _stream_rows = get_current_row()
    _stream_data_subset = stream_df.head(_stream_rows)
    _original_data_subset = data.head(_stream_rows)

    _company_name_stream = info.get("shortName", stock_code.value)

    # Float64に変換
    _df_stream_plot = _original_data_subset.with_columns(
        [
            pl.col("open.amount").cast(pl.Float64),
            pl.col("high.amount").cast(pl.Float64),
            pl.col("low.amount").cast(pl.Float64),
            pl.col("close.amount").cast(pl.Float64),
        ]
    )
    _dates_stream = _df_stream_plot["date"].to_list()

    _stream_chart_data = [
        go.Candlestick(
            yaxis="y1",
            x=_dates_stream,
            open=_df_stream_plot["open.amount"],
            high=_df_stream_plot["high.amount"],
            low=_df_stream_plot["low.amount"],
            close=_df_stream_plot["close.amount"],
            increasing_line_color="red",
            decreasing_line_color="green",
            name=f"{_company_name_stream}の株価",
        ),
        # ミドルバンド
        go.Scatter(
            yaxis="y1",
            x=_dates_stream,
            y=_stream_data_subset["stream_middle"],
            name="ミドルバンド (SMA20)",
            line={"color": "blue", "width": 1.5},
        ),
        # 偏差2.0のバンド（ストリーミング計算結果）
        go.Scatter(
            yaxis="y1",
            x=_dates_stream,
            y=_stream_data_subset["stream_upper"],
            name="σ2 上限（ストリーミング）",
            line={"color": "orange", "width": 1.5},
        ),
        go.Scatter(
            yaxis="y1",
            x=_dates_stream,
            y=_stream_data_subset["stream_lower"],
            name="σ2 下限（ストリーミング）",
            line={"color": "orange", "width": 1.5},
        ),
    ]

    _stream_chart_layout = {
        "height": 560,
        "width": 1028,
        "title": {
            "text": f"{_company_name_stream}の株価（ストリーミング処理：{_stream_rows}行）",
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

    stream_chart_fig = go.Figure(
        data=_stream_chart_data, layout=go.Layout(_stream_chart_layout)
    )
    stream_chart_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### バッチ vs ストリーミング 検証結果

    比較テーブルから、バッチ計算とストリーミング処理の結果がほぼ一致することを確認できます（差分は浮動小数点誤差のみ）。

    **ストリーミング処理の利点**：
    - メモリ効率（ウィンドウのみ保持）
    - リアルタイム対応（分足データなど）
    - 無限ストリーム対応
    """)
    return


if __name__ == "__main__":
    app.run()
