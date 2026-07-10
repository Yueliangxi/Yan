#!/usr/bin/env python3
"""
Yan Coin 股票模拟器
根据 Bitcoin.csv 的成交量驱动回购（减少流通股本），并生成股价与成交量数据。
"""

import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ── 发行参数 ──────────────────────────────────────────────
INITIAL_ISSUANCE = 10_000_000       # 初始发行量 10M
INITIAL_PRICE = 1.1                 # 初始发行价 1.1 HKD
BUYBACK_PRICE = 1.0                 # 回购价 1.0 HKD
ISSUANCE_THRESHOLD = 0.05           # 流通股本低于 5% 时触发新发行
VOLATILITY_SCALE = 0.15             # 股价波动幅度 = BTC 波动的 15%
SHARES_PER_BTC = 0.2                # 每成交 1 BTC 回购 0.2 股
PRICE_CEILING = 1.2                 # 股价上限
MEAN_REVERSION = 0.02               # 每日向 1.05 HKD 均值回归力度
TARGET_PRICE = 1.05                 # 目标均价

BASE_DIR = Path(__file__).parent
BITCOIN_CSV = BASE_DIR / "Bitcoin.csv"
OUTPUT_CSV = BASE_DIR / "Yan_stock.csv"
DOCS_DIR = BASE_DIR / "docs"
DOCS_CSV = DOCS_DIR / "Yan_stock.csv"


@dataclass
class BitcoinDay:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    change_pct: float


def parse_number(s: str) -> float:
    """解析带逗号、K/M 后缀的数字字符串。"""
    s = s.strip().replace(",", "").replace('"', "")
    if not s:
        return 0.0
    multiplier = 1.0
    if s.endswith("K"):
        multiplier = 1_000
        s = s[:-1]
    elif s.endswith("M"):
        multiplier = 1_000_000
        s = s[:-1]
    elif s.endswith("B"):
        multiplier = 1_000_000_000
        s = s[:-1]
    return float(s) * multiplier


def parse_change_pct(s: str) -> float:
    """解析涨跌幅字符串，如 '4.96%' -> 0.0496"""
    s = s.strip().replace("%", "").replace('"', "")
    if not s:
        return 0.0
    return float(s) / 100.0


def parse_date(s: str) -> datetime:
    s = s.strip().replace('"', "")
    return datetime.strptime(s, "%Y-%m-%d")


def load_bitcoin_data(path: Path) -> list[BitcoinDay]:
    rows: list[BitcoinDay] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                BitcoinDay(
                    date=parse_date(row["日期"]),
                    open=parse_number(row["开盘"]),
                    high=parse_number(row["高"]),
                    low=parse_number(row["低"]),
                    close=parse_number(row["收盘"]),
                    volume=parse_number(row["交易量"]),
                    change_pct=parse_change_pct(row["涨跌幅"]),
                )
            )
    rows.sort(key=lambda r: r.date)
    return rows


def new_issuance(current_outstanding: float, date: datetime) -> float:
    """
  新发行逻辑占位函数。
    当流通股本接近耗尽时调用，请在此实现你的发行策略。
    默认行为：重置为初始发行量。

    Args:
        current_outstanding: 触发时的剩余流通股本
        date: 触发日期

    Returns:
        新增发行的股数
    """
    # TODO: 在此实现你的新发行逻辑
    new_shares = INITIAL_ISSUANCE - current_outstanding
    print(f"  [新发行] {date.strftime('%Y-%m-%d')}: "
          f"剩余 {current_outstanding:,.0f} 股 → 增发 {new_shares:,.0f} 股")
    return new_shares


def simulate_stock(btc_days: list[BitcoinDay]) -> list[dict]:
    outstanding = float(INITIAL_ISSUANCE)
    prev_close = INITIAL_PRICE
    results: list[dict] = []

    for day in btc_days:
        # 流通股本低于阈值时先触发新发行
        if outstanding < INITIAL_ISSUANCE * ISSUANCE_THRESHOLD:
            new_shares = new_issuance(outstanding, day.date)
            outstanding += new_shares

        # 根据 BTC 成交量计算当日回购股数
        buyback_shares = day.volume * SHARES_PER_BTC
        buyback_shares = min(buyback_shares, outstanding)
        outstanding -= buyback_shares

        # 用 BTC 日涨跌幅（而非绝对价格）推导本股 OHLC，避免长期复利漂移
        c = prev_close * (1 + day.change_pct * VOLATILITY_SCALE)
        c += (TARGET_PRICE - prev_close) * MEAN_REVERSION
        c = max(BUYBACK_PRICE, min(PRICE_CEILING, round(c, 4)))

        intraday_range = (day.high - day.low) / day.close if day.close > 0 else 0
        spread = intraday_range * VOLATILITY_SCALE * 0.5
        o = max(BUYBACK_PRICE, round(c / (1 + day.change_pct * VOLATILITY_SCALE), 4))
        h = min(PRICE_CEILING, round(max(o, c) * (1 + spread), 4))
        l = max(BUYBACK_PRICE, round(min(o, c) * (1 - spread), 4))

        change = (c - prev_close) / prev_close if prev_close > 0 else 0.0
        prev_close = c

        results.append(
            {
                "日期": day.date.strftime("%Y-%m-%d"),
                "开盘": o,
                "收盘": c,
                "高": h,
                "低": l,
                "成交量": int(buyback_shares),
                "涨跌幅": change,
                "流通股本": int(outstanding),
            }
        )

    return results


def save_csv(rows: list[dict], path: Path) -> None:
    fieldnames = ["日期", "开盘", "收盘", "高", "低", "成交量", "涨跌幅", "流通股本"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "涨跌幅": f"{row['涨跌幅'] * 100:.2f}%",
                }
            )


def main() -> None:
    print("加载 Bitcoin 数据...")
    btc_days = load_bitcoin_data(BITCOIN_CSV)
    print(f"  共 {len(btc_days)} 个交易日 "
          f"({btc_days[0].date.date()} ~ {btc_days[-1].date.date()})")

    print("模拟 Yan Coin 股价...")
    rows = simulate_stock(btc_days)

    print(f"保存 CSV → {OUTPUT_CSV}")
    save_csv(rows, OUTPUT_CSV)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUTPUT_CSV, DOCS_CSV)
    print(f"复制 CSV → {DOCS_CSV}（供 docs/index.html 读取）")

    last = rows[-1]
    print(f"\n最新数据 ({last['日期']}):")
    print(f"  收盘价: {last['收盘']} HKD")
    print(f"  成交量: {last['成交量']:,} 股")
    print(f"  流通股本: {last['流通股本']:,} 股")


if __name__ == "__main__":
    main()
