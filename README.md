# py-stock-learning

marimoを使った株価分析の学習プロジェクト。テクニカル指標を用いた株価チャートの可視化と売買シグナルの検出を実践します。

## セットアップ

```bash
# 依存関係のインストール
uv sync
```

## 使い方

```bash
# ノートブックを編集モードで起動
uv run marimo edit src/s001_sma.py

# ノートブックを閲覧モードで起動
uv run marimo run src/s001_sma.py
```

## ノートブック一覧

| ファイル | 内容 |
|---------|------|
| `src/s001_sma.py` | 単純移動平均線（SMA）による株価分析。ゴールデンクロス・デッドクロスの検出 |

## 主要ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| [marimo](https://marimo.io/) | リアクティブノートブック環境 |
| [yfinance-pl](https://github.com/rmc8/yfinance_pl) | Yahoo Financeから株価データを取得（Polars形式） |
| [kand](https://github.com/kand-ta/kand) | テクニカル指標の計算（SMA, EMAなど） |
| [polars](https://pola.rs/) | 高速なDataFrameライブラリ |
| [plotly](https://plotly.com/python/) | インタラクティブなチャート作成 |

## 動作環境

- Python 3.13以上
- uv（パッケージマネージャ）
