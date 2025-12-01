import polars as pl
from typing import TypedDict


class IchimokuValues(TypedDict):
    conversion_line: pl.Series
    base_line: pl.Series
    leading_span1: pl.Series
    leading_span2: pl.Series
    lagging_span: pl.Series


def get_ichimoku_values(df: pl.DataFrame) -> IchimokuValues:
    # Decimal型はrolling操作がサポートされていないため、先にFloat64に変換
    high = df["high.amount"].cast(pl.Float64)
    low = df["low.amount"].cast(pl.Float64)
    close = df["close.amount"].cast(pl.Float64)

    # 転換線: 過去9日間の (Max + Min) / 2
    conversion_line = (high.rolling_max(9) + low.rolling_min(9)) / 2

    # 基準線: 過去26日間の (Max + Min) / 2
    base_line = (high.rolling_max(26) + low.rolling_min(26)) / 2

    # 先行スパン1: (転換線 + 基準線) / 2 を26日未来にずらす
    # Polarsのshiftはデフォルトで空いた部分をnullで埋めます
    leading_span1 = ((conversion_line + base_line) / 2).shift(26)

    # 先行スパン2: 過去52日間の (Max + Min) / 2 を26日未来にずらす
    leading_span2 = ((high.rolling_max(52) + low.rolling_min(52)) / 2).shift(26)

    # 遅行スパン: 今日の終値を26日過去にずらす
    lagging_span = close.shift(-26)

    return {
        "conversion_line": conversion_line,
        "base_line": base_line,
        "leading_span1": leading_span1,
        "leading_span2": leading_span2,
        "lagging_span": lagging_span,
    }
