import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import datetime as dt
    import warnings

    import marimo as mo
    import plotly.graph_objs as go
    import polars as pl
    import yfinance_pl as yf

    warnings.simplefilter("ignore")
    return go, mo, pl, yf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 一目均衡表（Ichimoku Cloud）を作る

    一目均衡表は、1936年に日本の細田悟一氏によって開発されたテクニカル指標です。
    「一目で相場の均衡状態がわかる」ことから名付けられました。

    ### 構成要素（5本の線）

    1. **転換線（Conversion Line / 転換線）**: 短期的な相場の方向性を示す（9日間）
    2. **基準線（Base Line / 基準線）**: 中期的な相場の方向性を示す（26日間）
    3. **先行スパン1（Leading Span A / 先行スパン1）**: 転換線と基準線の中間を26日先行させた線
    4. **先行スパン2（Leading Span B / 先行スパン2）**: 長期的な相場の方向性を26日先行させた線（52日間）
    5. **遅行スパン（Lagging Span / 遅行スパン）**: 現在の終値を26日遅行させた線

    **雲（Kumo / Cloud）**: 先行スパン1と先行スパン2の間の領域
    - 価格が雲の上 → 上昇トレンド
    - 価格が雲の中 → もみ合い相場
    - 価格が雲の下 → 下降トレンド

    ---

    以下、各線を個別に計算しながら学習します。
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
    ticker = yf.Ticker(stock_code.value)
    info = ticker.info
    hist = ticker.history(period="1y")
    hist.head(5)
    return hist, ticker


@app.cell
def _(hist, mo, pl):
    mo.md(r"""
    ### 1. 転換線（Conversion Line / 転換線）

    **計算式**: `(過去9日間の最高値 + 過去9日間の最安値) ÷ 2`

    短期的な相場の方向性を示す指標です。9日間という短い期間で計算されるため、
    価格変動に敏感に反応します。

    **ポイント**:
    - 転換線が基準線を上抜ける → 買いシグナル（好転）
    - 転換線が基準線を下抜ける → 売りシグナル（逆転）

    **実装のポイント**:
    - yfinance_plから取得したデータはDecimal型
    - Polarsの`rolling_max`/`rolling_min`はDecimal型未対応
    - 事前に`.cast(pl.Float64)`で型変換が必要

    ```python
    high = hist["high.amount"].cast(pl.Float64)
    low = hist["low.amount"].cast(pl.Float64)
    conversion_line = (high.rolling_max(9) + low.rolling_min(9)) / 2
    ```
    """)

    # 転換線: 過去9日間の (Max + Min) / 2
    high = hist["high.amount"].cast(pl.Float64)
    low = hist["low.amount"].cast(pl.Float64)
    conversion_line = (high.rolling_max(9) + low.rolling_min(9)) / 2
    conversion_line
    return (conversion_line,)


@app.cell
def _(hist, mo, pl):
    mo.md(r"""
    ### 2. 基準線（Base Line / 基準線）

    **計算式**: `(過去26日間の最高値 + 過去26日間の最安値) ÷ 2`

    中期的な相場の方向性を示す指標です。26日間は約1ヶ月の営業日に相当し、
    転換線よりも安定した動きを示します。

    **ポイント**:
    - 基準線が上向き → 中期的な上昇トレンド
    - 基準線が下向き → 中期的な下降トレンド
    - 基準線が横ばい → もみ合い相場

    **26日という数字の意味**:
    一目均衡表が開発された1936年当時、日本の取引所は月に26日営業していたため、
    「1ヶ月」を表す数字として26が使われています。

    ```python
    high = hist["high.amount"].cast(pl.Float64)
    low = hist["low.amount"].cast(pl.Float64)
    base_line = (high.rolling_max(26) + low.rolling_min(26)) / 2
    ```
    """)

    # 基準線: 過去26日間の (Max + Min) / 2
    _high = hist["high.amount"].cast(pl.Float64)
    _low = hist["low.amount"].cast(pl.Float64)
    base_line = (_high.rolling_max(26) + _low.rolling_min(26)) / 2
    base_line
    return (base_line,)


@app.cell
def _(base_line, conversion_line, mo):
    mo.md(r"""
    ### 3. 先行スパン1（Leading Span A / 先行スパン甲）

    **計算式**: `(転換線 + 基準線) ÷ 2` を **26日未来** にシフト

    転換線と基準線の中間値を26日先行させた線です。
    この線は「現在の短期〜中期のトレンド」を未来に投影したものと解釈できます。

    **ポイント**:
    - 先行スパン2と合わせて「雲（Kumo）」を形成
    - 雲の上限または下限として機能
    - 価格のサポート・レジスタンスラインとして機能

    **実装のポイント**:
    - Polarsの`.shift(26)`は正の数で「未来にシフト」
    - シフトした分（先頭26個）は自動的に`null`になる
    - これにより、チャート上で26日分先行して表示される

    ```python
    leading_span1 = ((conversion_line + base_line) / 2).shift(26)
    ```
    """)

    # 先行スパン1: (転換線 + 基準線) / 2 を26日未来にずらす
    leading_span1 = ((conversion_line + base_line) / 2).shift(26)
    leading_span1
    return (leading_span1,)


@app.cell
def _(hist, mo, pl):
    mo.md(r"""
    ### 4. 先行スパン2（Leading Span B / 先行スパン乙）

    **計算式**: `(過去52日間の最高値 + 過去52日間の最安値) ÷ 2` を **26日未来** にシフト

    長期的な相場の方向性を26日先行させた線です。
    52日間は約2ヶ月の営業日に相当し、より長期的なトレンドを示します。

    **ポイント**:
    - 先行スパン1と合わせて「雲（Kumo / Cloud）」を形成
    - 雲の厚さ = トレンドの強さ
      - 雲が厚い → 強いサポート/レジスタンス
      - 雲が薄い → 弱いサポート/レジスタンス
    - 雲の色（先行スパン1と2の上下関係）
      - 先行スパン1 > 先行スパン2 → 上昇雲（緑色で表示されることが多い）
      - 先行スパン1 < 先行スパン2 → 下降雲（赤色で表示されることが多い）

    **52日という数字の意味**:
    26日の2倍で、約2ヶ月の営業日を表します。

    ```python
    high = hist["high.amount"].cast(pl.Float64)
    low = hist["low.amount"].cast(pl.Float64)
    leading_span2 = ((high.rolling_max(52) + low.rolling_min(52)) / 2).shift(26)
    ```
    """)

    # 先行スパン2: 過去52日間の (Max + Min) / 2 を26日未来にずらす
    _high2 = hist["high.amount"].cast(pl.Float64)
    _low2 = hist["low.amount"].cast(pl.Float64)
    leading_span2 = ((_high2.rolling_max(52) + _low2.rolling_min(52)) / 2).shift(26)
    leading_span2
    return (leading_span2,)


@app.cell
def _(hist, mo, pl):
    mo.md(r"""
    ### 5. 遅行スパン（Lagging Span / Chikou Span / 遅行線）

    **計算式**: 今日の終値を **26日過去** にシフト

    現在の終値を26日前に遡って表示した線です。
    現在の価格水準を過去の価格と比較することで、相場の勢いを判断します。

    **ポイント**:
    - 遅行スパンが過去のローソク足を上抜ける → 強い買いシグナル
    - 遅行スパンが過去のローソク足を下抜ける → 強い売りシグナル
    - 遅行スパンがローソク足に絡む → もみ合い相場

    **実装のポイント**:
    - Polarsの`.shift(-26)`は負の数で「過去にシフト」
    - シフトした分（末尾26個）は自動的に`null`になる
    - これにより、チャート上で26日分遅行して表示される

    **使い方のコツ**:
    遅行スパンは「現在の価格が26日前と比べてどうか」を示すため、
    上昇トレンド時は遅行スパンが過去のローソク足の上方に位置し、
    下降トレンド時は下方に位置します。

    ```python
    close = hist["close.amount"].cast(pl.Float64)
    lagging_span = close.shift(-26)
    ```
    """)

    # 遅行スパン: 今日の終値を26日過去にずらす
    _close = hist["close.amount"].cast(pl.Float64)
    lagging_span = _close.shift(-26)
    lagging_span
    return (lagging_span,)


@app.cell
def _(go, hist, mo, pl, stock_code, ticker):
    mo.md(r"""
    ---

    ## 一目均衡表のチャート表示

    上記で学習した各線の計算を、`get_ichimoku_values()`関数でまとめて取得できます。

    ```python
    from libs.ichimoku import get_ichimoku_values
    values = get_ichimoku_values(hist)
    ```

    この関数は5つの線をすべて計算して辞書形式で返します。

    ### チャートの見方

    **三役好転（さんやくこうてん）**: 最強の買いシグナル
    1. 転換線が基準線を上抜ける
    2. 遅行スパンがローソク足を上抜ける
    3. 価格が雲を上抜ける

    **三役逆転（さんやくぎゃくてん）**: 最強の売りシグナル
    1. 転換線が基準線を下抜ける
    2. 遅行スパンがローソク足を下抜ける
    3. 価格が雲を下抜ける

    **雲の使い方**:
    - 雲は将来のサポート・レジスタンスを示す
    - 価格が雲の上 → 上昇トレンド継続の可能性が高い
    - 価格が雲の下 → 下降トレンド継続の可能性が高い
    - 価格が雲を突破 → トレンド転換の可能性
    """)

    import numpy as np

    from libs.ichimoku import IchimokuValues, get_ichimoku_values

    def create_cloud_segments(dates, span1, span2):
        """
        Split Ichimoku cloud into colored segments based on bullish/bearish crossovers.

        Args:
            dates: List of date strings
            span1: Polars Series or numpy array of leading_span1 values
            span2: Polars Series or numpy array of leading_span2 values

        Returns:
            List of go.Scatter traces for colored cloud segments
        """
        # Convert to numpy arrays if needed
        if hasattr(span1, "to_numpy"):
            span1 = span1.to_numpy()
        if hasattr(span2, "to_numpy"):
            span2 = span2.to_numpy()

        # Calculate bullish condition (span1 > span2)
        # Handle NaN values by treating them as False
        is_bullish = np.nan_to_num(span1 > span2, nan=False)

        # Find crossover points where bullish condition changes
        crossovers = np.where(np.diff(is_bullish.astype(int)) != 0)[0] + 1

        # Create segment boundaries (start at 0, include all crossovers, end at len)
        boundaries = np.concatenate([[0], crossovers, [len(dates)]])

        traces = []

        # For each segment between boundaries
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]

            # Extract segment data
            segment_dates = dates[start_idx:end_idx]
            segment_span1 = span1[start_idx:end_idx]
            segment_span2 = span2[start_idx:end_idx]

            # Skip if all values are NaN
            if np.all(np.isnan(segment_span1)) or np.all(np.isnan(segment_span2)):
                continue

            # Determine segment color
            segment_is_bullish = is_bullish[start_idx]
            fillcolor = (
                "rgba(135, 206, 250, 0.3)"
                if segment_is_bullish
                else "rgba(255, 165, 0, 0.3)"
            )

            # Create trace pair for this segment
            # First trace: span1 (no fill)
            traces.append(
                go.Scatter(
                    x=segment_dates,
                    y=segment_span1,
                    mode="lines",
                    line={"width": 0.5, "color": "rgba(200,200,200,0.5)"},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            # Second trace: span2 (fill to previous = span1)
            traces.append(
                go.Scatter(
                    x=segment_dates,
                    y=segment_span2,
                    mode="lines",
                    line={"width": 0.5, "color": "rgba(200,200,200,0.5)"},
                    fill="tonexty",
                    fillcolor=fillcolor,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        return traces

    def get_ichimoku_fig(df: pl.DataFrame, values: IchimokuValues, name: str):
        # 日付を"YYYY-MM-DD"形式の文字列に変換（カテゴリ軸のラベルが綺麗になる）
        dates = df["date"].dt.strftime("%Y-%m-%d").to_list()
        layout = {
            "height": 700,
            "title": {"text": name, "x": 0.5},
            "xaxis": {
                "rangeslider": {"visible": False},
                "type": "category",
                "nticks": 12,
                "tickmode": "auto",
                "showgrid": False,
            },
            "yaxis1": {
                "domain": [0.05, 1.0],
                "title": "価格(JPY)",
                "side": "left",
                "tickformat": ",",
            },
            "yaxis2": {"domain": [0.0, 0.05]},
        }
        data = [
            go.Candlestick(
                yaxis="y1",
                x=dates,
                open=df["open.amount"],
                high=df["high.amount"],
                low=df["low.amount"],
                close=df["close.amount"],
                increasing_line_color="red",
                decreasing_line_color="green",
                name=name,
            ),
            # 一目均衡表の各線を表示する
            go.Scatter(
                x=dates,
                y=values["base_line"],
                name="基準線",
                mode="lines",
                line={"color": "green", "width": 1},
            ),
            go.Scatter(
                x=dates,
                y=values["conversion_line"],
                name="転換線",
                mode="lines",
                line={"color": "darkviolet", "width": 1},
            ),
            go.Scatter(
                x=dates,
                y=values["leading_span1"],
                name="先行スパン1",
                mode="lines",
                line={"color": "gainsboro", "width": 1},
            ),
            go.Scatter(
                x=dates,
                y=values["leading_span2"],
                name="先行スパン2",
                mode="lines",
                line={"color": "gainsboro", "width": 1},
            ),
            go.Scatter(
                x=dates,
                y=values["lagging_span"],
                name="遅行スパン",
                mode="lines",
                line={"color": "cornflowerblue", "width": 1},
            ),
        ]

        # 雲の塗りつぶし（陽転・陰転で色分け）
        cloud_traces = create_cloud_segments(
            dates=dates, span1=values["leading_span1"], span2=values["leading_span2"]
        )
        data.extend(cloud_traces)
        return go.Figure(data=data, layout=go.Layout(layout))

    values = get_ichimoku_values(hist)
    company_name = ticker.info.get("shortName", stock_code.value)
    fig = get_ichimoku_fig(df=hist, values=values, name=company_name)
    fig
    return


if __name__ == "__main__":
    app.run()
