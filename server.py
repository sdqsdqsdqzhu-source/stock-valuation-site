from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import time
import urllib.parse
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import date, datetime, timedelta


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
PORT = int(os.environ.get("STOCK_SITE_PORT", "8765"))
REDDIT_SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "StockMarket",
    "options",
    "SecurityAnalysis",
    "ValueInvesting",
    "pennystocks",
]


CIK_BY_TICKER = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    "INTC": "0000050863",
    "AMD": "0000002488",
    "META": "0001326801",
    "AMZN": "0001018724",
    "GOOG": "0001652044",
    "GOOGL": "0001652044",
    "JPM": "0000019617",
    "BAC": "0000070858",
    "XOM": "0000034088",
    "CVX": "0000093410",
    "WMT": "0000104169",
    "COST": "0000909832",
    "DIS": "0001744489",
    "NFLX": "0001065280",
    "QCOM": "0000804328",
    "MU": "0000723125",
    "SNDK": "0001000180",
    "SOFI": "0001818874",
}

LOGO_DOMAINS = {
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "NVDA": "nvidia.com",
    "INTC": "intel.com",
    "AMD": "amd.com",
    "MU": "micron.com",
    "SNDK": "sandisk.com",
    "TSLA": "tesla.com",
    "META": "meta.com",
    "AMZN": "amazon.com",
    "GOOG": "abc.xyz",
    "GOOGL": "abc.xyz",
    "JPM": "jpmorganchase.com",
    "XOM": "exxonmobil.com",
    "WMT": "walmart.com",
    "SOFI": "sofi.com",
}

OFFICIAL_EARNINGS = {
    "SOFI": {
        "source": "SoFi Investor Relations",
        "source_url": "https://investors.sofi.com/news/news-details/2026/SoFi-Reports-First-Quarter-2026-with-Record-Net-Revenue-of-1-1-Billion-Record-Member-and-Product-Growth-Net-Income-of-167-Million/default.aspx",
        "latest_report": {
            "form": "Earnings Release",
            "period_end": "2026-03-31",
            "filed": "2026-04-29",
            "fiscal_period": "Q1",
            "fiscal_year": "2026",
        },
        "actuals": {
            "revenue": 1_100_368_000,
            "net_income": 166_731_000,
            "eps": 0.12,
        },
        "guidance": [
            {
                "name": "Revenue & EPS Outlook",
                "status": "官网IR已接入 / company IR connected",
                "context": "Q2 2026：管理层预计 adjusted net revenue 增长约 30%；FY2026：adjusted net revenue 约 $4.655B，隐含约 30% 年增长；adjusted EPS 约 $0.60 / Q2 2026 adjusted net revenue growth about 30%; FY2026 adjusted net revenue about $4.655B, implying about 30% growth; adjusted EPS about $0.60.",
                "yoy": 0.30,
                "qoq": None,
                "secondary_yoy": None,
                "secondary_qoq": None,
            },
            {
                "name": "Margin Guidance",
                "status": "官网IR已接入 / company IR connected",
                "context": "Q2 2026：adjusted EBITDA margin 约 30%，adjusted net income margin 约 12%-13%；FY2026：adjusted EBITDA 约 $1.6B，EBITDA margin 约 34%，adjusted net income 约 $825M，margin 约 18% / Q2 adjusted EBITDA margin about 30% and adjusted net income margin about 12%-13%; FY adjusted EBITDA about $1.6B, EBITDA margin about 34%, adjusted net income about $825M, margin about 18%.",
                "yoy": None,
                "qoq": None,
            },
            {
                "name": "Capex Guidance",
                "status": "官网IR未明确给出 / not explicitly guided in company IR",
                "context": "这份 Q1 2026 新闻稿没有给出明确 capex 指引；金融科技公司更应跟踪技术投入、信贷资产增长和资金成本 / The Q1 2026 release does not provide explicit capex guidance; for a fintech, track technology investment, loan book growth, and funding cost.",
                "yoy": None,
                "qoq": None,
            },
            {
                "name": "Buybacks & Dividends",
                "status": "官网IR未明确给出 / not explicitly guided in company IR",
                "context": "本次新闻稿未给出明确回购或分红计划；应继续跟踪 10-Q、董事会授权公告和股本变化 / The release does not give a clear buyback or dividend plan; continue tracking 10-Q filings, board authorizations, and share-count change.",
                "yoy": None,
                "qoq": None,
            },
        ],
    },
}

TICKER_ALIASES = {
    "INTEL": "INTC",
    "英特尔": "INTC",
    "因特尔": "INTC",
    "GOOGLE": "GOOG",
    "GOOGL": "GOOGL",
    "谷歌": "GOOG",
    "ALPHABET": "GOOG",
    "苹果": "AAPL",
    "APPLE": "AAPL",
    "微软": "MSFT",
    "MICROSOFT": "MSFT",
    "英伟达": "NVDA",
    "NVIDIA": "NVDA",
    "特斯拉": "TSLA",
    "TESLA": "TSLA",
    "亚马逊": "AMZN",
    "AMAZON": "AMZN",
    "脸书": "META",
    "META": "META",
    "美光": "MU",
    "MICRON": "MU",
    "高通": "QCOM",
    "QUALCOMM": "QCOM",
    "富途": "FUTU",
    "FUTU": "FUTU",
    "SOFI": "SOFI",
    "SOFI TECHNOLOGIES": "SOFI",
}


PROFILES = {
    "AAPL": {
        "sector": "Consumer Technology",
        "industry": "Devices / Services",
        "traits": ["mega_cap", "quality", "buyback", "china_exposure", "consumer"],
        "growth": 0.07,
        "attention": 82,
        "risk": ["China supply chain", "regulatory app store pressure"],
    },
    "MSFT": {
        "sector": "Software / Cloud",
        "industry": "Cloud, AI, Productivity",
        "traits": ["mega_cap", "quality", "ai", "recurring_revenue", "rate_sensitive"],
        "growth": 0.12,
        "attention": 78,
        "risk": ["AI capex discipline", "antitrust scrutiny"],
    },
    "NVDA": {
        "sector": "Semiconductors",
        "industry": "AI Accelerators",
        "traits": ["mega_cap", "cyclical", "ai", "export_control", "high_growth"],
        "growth": 0.24,
        "attention": 94,
        "risk": ["China export controls", "AI capex cycle", "customer concentration"],
    },
    "INTC": {
        "sector": "Semiconductors",
        "industry": "IDM / Foundry",
        "traits": ["cyclical", "heavy_asset", "policy_sensitive", "turnaround", "geopolitical"],
        "growth": 0.04,
        "attention": 76,
        "risk": ["foundry execution", "heavy capex", "margin pressure", "policy headline risk"],
    },
    "AMD": {
        "sector": "Semiconductors",
        "industry": "CPUs / GPUs",
        "traits": ["cyclical", "ai", "high_growth", "rate_sensitive"],
        "growth": 0.18,
        "attention": 84,
        "risk": ["AI share uncertainty", "PC/server cycle"],
    },
    "MU": {
        "sector": "Semiconductors",
        "industry": "Memory / DRAM / NAND",
        "traits": ["cyclical", "ai", "commodity_sensitive", "high_attention", "rate_sensitive"],
        "growth": 0.20,
        "attention": 92,
        "risk": ["memory pricing cycle", "capex discipline", "AI HBM expectations"],
    },
    "SNDK": {
        "sector": "Semiconductors",
        "industry": "NAND / Storage",
        "traits": ["cyclical", "commodity_sensitive", "high_attention", "turnaround"],
        "growth": 0.16,
        "attention": 88,
        "risk": ["NAND pricing cycle", "post-spin financial visibility", "retail momentum reversal"],
    },
    "SOFI": {
        "sector": "Fintech / Consumer Finance",
        "industry": "Digital banking / Lending",
        "traits": ["high_growth", "rate_sensitive", "turnaround", "consumer", "policy_sensitive"],
        "growth": 0.30,
        "attention": 86,
        "risk": ["credit cycle", "funding cost", "regulatory scrutiny", "private-credit sentiment"],
    },
    "TSLA": {
        "sector": "Autos / Energy",
        "industry": "EVs, autonomy, storage",
        "traits": ["cyclical", "policy_sensitive", "meme_sensitive", "high_growth", "china_exposure"],
        "growth": 0.15,
        "attention": 96,
        "risk": ["margin pressure", "EV demand cycle", "management headline risk"],
    },
    "JPM": {
        "sector": "Financials",
        "industry": "Banking",
        "traits": ["financial", "rate_sensitive", "defensive_quality"],
        "growth": 0.05,
        "attention": 55,
        "risk": ["credit cycle", "yield curve", "capital rules"],
    },
    "XOM": {
        "sector": "Energy",
        "industry": "Integrated Oil & Gas",
        "traits": ["commodity_sensitive", "cyclical", "cash_return"],
        "growth": 0.03,
        "attention": 58,
        "risk": ["oil price", "windfall taxes", "energy transition"],
    },
    "WMT": {
        "sector": "Consumer Defensive",
        "industry": "Retail",
        "traits": ["defensive", "scale", "tariff_sensitive", "low_margin"],
        "growth": 0.04,
        "attention": 50,
        "risk": ["wage pressure", "tariffs", "consumer slowdown"],
    },
}


SECTOR_DEFAULTS = {
    "Semiconductors": {
        "target_pe": 24,
        "target_forward_pe": 22,
        "target_ps": 6.0,
        "target_pb": 3.8,
        "target_pfcf": 26,
        "target_ev_ebitda": 15,
        "method_weights": {"forward_pe": 0.25, "ev_ebitda": 0.25, "dcf": 0.2, "ps": 0.15, "peg": 0.15},
    },
    "Software / Cloud": {
        "target_pe": 32,
        "target_forward_pe": 29,
        "target_ps": 9.0,
        "target_pb": 8.0,
        "target_pfcf": 32,
        "target_ev_ebitda": 22,
        "method_weights": {"dcf": 0.3, "pfcf": 0.25, "forward_pe": 0.2, "ps": 0.15, "peg": 0.1},
    },
    "Financials": {
        "target_pe": 12,
        "target_forward_pe": 11,
        "target_ps": 3.0,
        "target_pb": 1.7,
        "target_pfcf": 10,
        "target_ev_ebitda": 0,
        "method_weights": {"pb": 0.45, "forward_pe": 0.25, "pe": 0.15, "dcf": 0.15},
    },
    "Energy": {
        "target_pe": 12,
        "target_forward_pe": 11,
        "target_ps": 1.4,
        "target_pb": 2.0,
        "target_pfcf": 12,
        "target_ev_ebitda": 6.5,
        "method_weights": {"pfcf": 0.3, "ev_ebitda": 0.3, "forward_pe": 0.2, "dcf": 0.2},
    },
    "Consumer Defensive": {
        "target_pe": 22,
        "target_forward_pe": 20,
        "target_ps": 0.9,
        "target_pb": 4.5,
        "target_pfcf": 23,
        "target_ev_ebitda": 13,
        "method_weights": {"forward_pe": 0.3, "pfcf": 0.25, "dcf": 0.25, "ev_ebitda": 0.1, "pb": 0.1},
    },
    "default": {
        "target_pe": 20,
        "target_forward_pe": 18,
        "target_ps": 3.0,
        "target_pb": 3.0,
        "target_pfcf": 20,
        "target_ev_ebitda": 11,
        "method_weights": {"forward_pe": 0.25, "dcf": 0.25, "pfcf": 0.2, "ev_ebitda": 0.15, "peg": 0.15},
    },
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip() in {"", "N/A", "--", "NaN"}:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except Exception:
        return default


def ticker_seed(ticker: str) -> random.Random:
    seed = sum((idx + 1) * ord(ch) for idx, ch in enumerate(ticker.upper()))
    return random.Random(seed)


def normalize_ticker(raw: str) -> tuple[str, str]:
    original = (raw or "INTC").strip()
    alias_key = re.sub(r"\s+", " ", original.upper())
    value = TICKER_ALIASES.get(original, TICKER_ALIASES.get(alias_key, alias_key))
    if "." in value:
        market, ticker = value.split(".", 1)
        ticker = TICKER_ALIASES.get(ticker, ticker)
        return ticker, f"{market}.{ticker}"
    if value.isdigit() and len(value) <= 5:
        return value.zfill(5), f"HK.{value.zfill(5)}"
    return value, f"US.{value}"


def get_profile(ticker: str) -> dict:
    if ticker in PROFILES:
        return dict(PROFILES[ticker])
    rnd = ticker_seed(ticker)
    sectors = ["Semiconductors", "Software / Cloud", "Consumer Defensive", "Energy", "Industrials"]
    sector = sectors[rnd.randrange(len(sectors))]
    traits = {
        "Semiconductors": ["cyclical", "rate_sensitive", "tariff_sensitive"],
        "Software / Cloud": ["asset_light", "rate_sensitive", "recurring_revenue"],
        "Consumer Defensive": ["defensive", "tariff_sensitive", "low_margin"],
        "Energy": ["commodity_sensitive", "cyclical"],
        "Industrials": ["cyclical", "heavy_asset", "fiscal_spending_sensitive"],
    }[sector]
    return {
        "sector": sector,
        "industry": "Auto-classified peer group",
        "traits": traits,
        "growth": 0.04 + rnd.random() * 0.12,
        "attention": 35 + rnd.random() * 35,
        "risk": ["limited configured company profile", "use live filings before trading"],
    }


def get_futu_snapshot(code: str) -> tuple[dict, list[str]]:
    notes = []
    try:
        from futu import OpenQuoteContext, RET_OK

        host = os.environ.get("FUTU_OPEND_HOST", "127.0.0.1")
        port = int(os.environ.get("FUTU_OPEND_PORT", "11111"))
        ctx = OpenQuoteContext(host=host, port=port)
        try:
            ret, data = ctx.get_market_snapshot([code])
            if ret != RET_OK or data is None or len(data) == 0:
                notes.append(f"Futu OpenD returned no snapshot for {code}.")
                return {}, notes
            row = data.iloc[0].to_dict()
            return {
                "code": str(row.get("code", code)),
                "name": str(row.get("name", "")),
                "price": safe_float(row.get("last_price")),
                "prev_close_price": safe_float(row.get("prev_close_price")),
                "market_cap": safe_float(row.get("total_market_val")),
                "pe": safe_float(row.get("pe_ratio")),
                "pe_ttm": safe_float(row.get("pe_ttm_ratio")),
                "pb": safe_float(row.get("pb_ratio")),
                "ey_ratio": safe_float(row.get("ey_ratio")),
                "eps": safe_float(row.get("earning_per_share")),
                "book_per_share": safe_float(row.get("net_asset_per_share")),
                "volume": safe_float(row.get("volume")),
                "turnover_rate": safe_float(row.get("turnover_rate")),
                "volume_ratio": safe_float(row.get("volume_ratio")),
                "bid_ask_ratio": safe_float(row.get("bid_ask_ratio")),
                "net_profit_snapshot": safe_float(row.get("net_profit")),
                "outstanding_shares": safe_float(row.get("outstanding_shares")),
                "source": "Futu OpenD",
            }, ["Futu OpenD snapshot connected."]
        finally:
            ctx.close()
    except Exception as exc:
        notes.append(f"Futu OpenD unavailable: {exc.__class__.__name__}.")
        return {}, notes


def yahoo_symbol(ticker: str) -> str:
    return ticker.split(".")[-1].replace("-", "-").upper()


def yahoo_chart(ticker: str, range_: str = "5d", interval: str = "1d") -> dict:
    params = urllib.parse.urlencode({"range": range_, "interval": interval})
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol(ticker)}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    result = ((data.get("chart") or {}).get("result") or [])
    return result[0] if result else {}


def yahoo_quote_points(chart: dict) -> list[dict]:
    timestamps = chart.get("timestamp") or []
    quote = (((chart.get("indicators") or {}).get("quote") or [{}])[0]) or {}
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    points = []
    for idx, ts in enumerate(timestamps):
        close = safe_float(closes[idx] if idx < len(closes) else None)
        if close <= 0:
            continue
        points.append({
            "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
            "close": close,
            "volume": safe_float(volumes[idx] if idx < len(volumes) else None),
        })
    return points


def get_yahoo_snapshot(ticker: str) -> tuple[dict, list[str]]:
    try:
        chart = yahoo_chart(ticker, "5d", "1d")
        meta = chart.get("meta") or {}
        points = yahoo_quote_points(chart)
        price = safe_float(meta.get("regularMarketPrice")) or (points[-1]["close"] if points else 0)
        if price <= 0:
            return {}, [f"Yahoo Finance chart returned no usable price for {ticker}."]
        prev_close = points[-2]["close"] if len(points) >= 2 else safe_float(meta.get("chartPreviousClose"))
        volume = safe_float(meta.get("regularMarketVolume")) or (points[-1]["volume"] if points else 0)
        return {
            "code": f"US.{yahoo_symbol(ticker)}",
            "name": meta.get("longName") or meta.get("shortName") or ticker,
            "price": price,
            "prev_close_price": prev_close,
            "market_cap": 0,
            "pe": 0,
            "pe_ttm": 0,
            "pb": 0,
            "ey_ratio": 0,
            "eps": 0,
            "book_per_share": 0,
            "volume": volume,
            "turnover_rate": 0,
            "volume_ratio": 0,
            "bid_ask_ratio": 0,
            "day_high": safe_float(meta.get("regularMarketDayHigh")),
            "day_low": safe_float(meta.get("regularMarketDayLow")),
            "fifty_two_week_high": safe_float(meta.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": safe_float(meta.get("fiftyTwoWeekLow")),
            "regular_market_time": meta.get("regularMarketTime"),
            "source": "Yahoo Finance chart",
        }, ["Yahoo Finance chart snapshot connected."]
    except Exception as exc:
        return {}, [f"Yahoo Finance chart snapshot unavailable: {exc.__class__.__name__}."]


def get_futu_price_context(code: str, current_price: float, prev_close_price: float = 0) -> tuple[dict, list[str]]:
    notes = []
    try:
        from futu import AuType, KLType, OpenQuoteContext, RET_OK

        host = os.environ.get("FUTU_OPEND_HOST", "127.0.0.1")
        port = int(os.environ.get("FUTU_OPEND_PORT", "11111"))
        ctx = OpenQuoteContext(host=host, port=port)
        try:
            end = date.today()
            start = end - timedelta(days=130)
            ret, data, _ = ctx.request_history_kline(
                code,
                start=start.isoformat(),
                end=end.isoformat(),
                ktype=KLType.K_DAY,
                autype=AuType.QFQ,
                max_count=200,
            )
            if ret != RET_OK or data is None or len(data) == 0:
                return fallback_price_context(code, current_price, prev_close_price), [f"Futu history unavailable for {code}."]
            rows = data.to_dict("records")
            closes = [safe_float(row.get("close")) for row in rows if safe_float(row.get("close")) > 0]
            volumes = [safe_float(row.get("volume")) for row in rows if safe_float(row.get("volume")) > 0]
            if not closes:
                return fallback_price_context(code, current_price, prev_close_price), [f"Futu history returned no closes for {code}."]
            price = current_price or closes[-1]

            def ref(days: int) -> float:
                idx = max(0, len(closes) - 1 - days)
                return closes[idx]

            avg_5 = sum(volumes[-5:]) / min(len(volumes), 5) if volumes else 0
            avg_20 = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0
            avg_60 = sum(volumes[-60:]) / min(len(volumes), 60) if volumes else 0
            return {
                "previous_close": ref(1),
                "week_ago": ref(5),
                "month_ago": ref(21),
                "quarter_ago": ref(63),
                "latest_close": closes[-1],
                "day_change": pct_change(closes[-1], ref(1)),
                "week_change": pct_change(closes[-1], ref(5)),
                "month_change": pct_change(closes[-1], ref(21)),
                "quarter_change": pct_change(closes[-1], ref(63)),
                "avg_volume_5d": avg_5,
                "avg_volume_20d": avg_20,
                "avg_volume_60d": avg_60,
                "volume_ratio": (volumes[-1] / avg_20) if volumes and avg_20 else 0,
                "volume_trend": (avg_5 / avg_20) if avg_5 and avg_20 else 0,
                "history": [{"date": row.get("time_key", "")[:10], "close": safe_float(row.get("close")), "volume": safe_float(row.get("volume"))} for row in rows[-90:]],
                "source": "Futu historical K-line",
            }, ["Futu historical K-line connected."]
        finally:
            ctx.close()
    except Exception as exc:
        fallback = fallback_price_context(code, current_price, prev_close_price)
        return fallback, [f"Futu historical K-line unavailable: {exc.__class__.__name__}."]


def get_yahoo_price_context(ticker: str, current_price: float, prev_close_price: float = 0) -> tuple[dict, list[str]]:
    try:
        chart = yahoo_chart(ticker, "3mo", "1d")
        points = yahoo_quote_points(chart)
        if not points:
            return {}, [f"Yahoo Finance chart history returned no closes for {ticker}."]
        closes = [point["close"] for point in points]
        volumes = [point["volume"] for point in points]
        price = current_price or closes[-1]

        def ref(days: int) -> float:
            idx = max(0, len(closes) - 1 - days)
            return closes[idx]

        prev = prev_close_price if prev_close_price > 0 else (closes[-2] if len(closes) >= 2 else ref(1))
        avg_5 = sum(volumes[-5:]) / min(len(volumes), 5) if volumes else 0
        avg_20 = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0
        avg_60 = sum(volumes[-60:]) / min(len(volumes), 60) if volumes else 0
        return {
            "previous_close": prev,
            "week_ago": ref(5),
            "month_ago": ref(21),
            "quarter_ago": ref(63),
            "latest_close": price,
            "day_change": pct_change(price, prev),
            "week_change": pct_change(price, ref(5)),
            "month_change": pct_change(price, ref(21)),
            "quarter_change": pct_change(price, ref(63)),
            "avg_volume_5d": avg_5,
            "avg_volume_20d": avg_20,
            "avg_volume_60d": avg_60,
            "volume_ratio": (volumes[-1] / avg_20) if avg_20 else 0,
            "volume_trend": (avg_5 / avg_20) if avg_20 else 0,
            "history": points[-90:],
            "source": "Yahoo Finance chart",
        }, ["Yahoo Finance chart history connected."]
    except Exception as exc:
        return {}, [f"Yahoo Finance chart history unavailable: {exc.__class__.__name__}."]


def pct_change(current: float, previous: float) -> float | None:
    if not previous:
        return None
    return current / previous - 1


def fallback_price_context(code: str, current_price: float, prev_close_price: float = 0) -> dict:
    ticker = code.split(".")[-1]
    rnd = ticker_seed(ticker)
    def back(days: int) -> float:
        drift = (rnd.random() - 0.48) * math.sqrt(days) * 0.045
        return max(0.01, current_price / (1 + drift))
    prev = prev_close_price if prev_close_price > 0 else back(1)
    week = back(5)
    month = back(21)
    quarter = back(63)
    avg_20 = 2_000_000 + rnd.random() * 25_000_000
    ratio = 0.6 + rnd.random() * 2.2
    return {
        "previous_close": prev,
        "week_ago": week,
        "month_ago": month,
        "quarter_ago": quarter,
        "latest_close": current_price,
        "day_change": pct_change(current_price, prev),
        "week_change": pct_change(current_price, week),
        "month_change": pct_change(current_price, month),
        "quarter_change": pct_change(current_price, quarter),
        "avg_volume_5d": avg_20 * ratio,
        "avg_volume_20d": avg_20,
        "avg_volume_60d": avg_20 * (0.8 + rnd.random() * 0.5),
        "volume_ratio": ratio,
        "volume_trend": ratio,
        "history": [],
        "source": "model fallback",
    }


def sec_request(url: str) -> dict:
    user_agent = os.environ.get("SEC_USER_AGENT", "David Stock Valuation Site david@example.com")
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=6) as response:
        return json.loads(response.read().decode("utf-8"))


def yahoo_quarterly_request(ticker: str) -> dict:
    types = [
        "quarterlyTotalRevenue",
        "quarterlyGrossProfit",
        "quarterlyNetIncome",
        "quarterlyDilutedEPS",
        "quarterlyOperatingIncome",
        "quarterlyOperatingCashFlow",
        "quarterlyCapitalExpenditure",
        "quarterlyTotalAssets",
        "quarterlyTotalLiabilitiesNetMinorityInterest",
        "quarterlyStockholdersEquity",
        "quarterlyCashAndCashEquivalents",
    ]
    params = urllib.parse.urlencode({
        "lang": "en-US",
        "region": "US",
        "symbol": ticker,
        "padTimeSeries": "true",
        "type": ",".join(types),
        "merge": "false",
        "period1": "0",
        "period2": str(int(time.time()) + 86400),
        "corsDomain": "finance.yahoo.com",
    })
    url = f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{ticker}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def enrich_with_yahoo_quarterly(ticker: str, fin: dict) -> list[str]:
    mapping = {
        "quarterlyTotalRevenue": "revenue",
        "quarterlyGrossProfit": "gross_profit",
        "quarterlyNetIncome": "net_income",
        "quarterlyDilutedEPS": "eps",
        "quarterlyOperatingIncome": "operating_income",
        "quarterlyOperatingCashFlow": "operating_cash_flow",
        "quarterlyCapitalExpenditure": "capex",
        "quarterlyTotalAssets": "assets",
        "quarterlyTotalLiabilitiesNetMinorityInterest": "liabilities",
        "quarterlyStockholdersEquity": "equity",
        "quarterlyCashAndCashEquivalents": "cash",
    }
    try:
        data = yahoo_quarterly_request(ticker)
        results = data.get("timeseries", {}).get("result", [])
        found = 0
        for block in results:
            for yahoo_key, local_key in mapping.items():
                rows = block.get(yahoo_key)
                if not isinstance(rows, list):
                    continue
                series = []
                for row in rows:
                    value = safe_float(row.get("reportedValue", {}).get("raw"), None)
                    if value is None:
                        continue
                    series.append({
                        "date": row.get("asOfDate") or "",
                        "filed": row.get("asOfDate") or "",
                        "fy": None,
                        "fp": row.get("periodType", "3M"),
                        "frame": row.get("asOfDate") or "",
                        "value": value,
                        "form": "Yahoo Finance",
                        "tag": yahoo_key,
                    })
                series = sorted(series, key=lambda x: x.get("date") or "")[-16:]
                if len(series) >= max(8, len(fin.get("trends", {}).get(local_key, []))):
                    fin.setdefault("trends", {})[local_key] = series
                    found += 1
        latest = fin.get("trends", {})
        for key in ("revenue", "gross_profit", "net_income", "eps", "operating_income", "operating_cash_flow", "assets", "liabilities", "equity", "cash"):
            rows = latest.get(key) or []
            if rows:
                fin[key] = safe_float(rows[-1].get("value"))
        capex_rows = latest.get("capex") or []
        if capex_rows:
            fin["capex"] = abs(safe_float(capex_rows[-1].get("value")))
        fin["free_cash_flow"] = safe_float(fin.get("operating_cash_flow")) - abs(safe_float(fin.get("capex")))
        fin["changes"] = {key: series_change(value) for key, value in fin.get("trends", {}).items()}
        return [f"Yahoo Finance quarterly fundamentals connected for {found} fields."] if found else ["Yahoo Finance quarterly fundamentals returned no usable fields."]
    except Exception as exc:
        return [f"Yahoo Finance quarterly fundamentals unavailable: {exc.__class__.__name__}."]


def fact_units(facts: dict, tag: str) -> list[dict]:
    for taxonomy in ("us-gaap", "ifrs-full"):
        item = facts.get("facts", {}).get(taxonomy, {}).get(tag)
        if not item:
            continue
        units = item.get("units", {})
        for unit_name in ("USD", "USD/shares", "shares", "pure"):
            if unit_name in units:
                return units[unit_name]
    return []


def latest_fact(facts: dict, tags: list[str], forms=("10-K", "10-Q", "20-F", "40-F")) -> float:
    rows = []
    for tag in tags:
        for row in fact_units(facts, tag):
            if row.get("form") in forms and row.get("val") is not None:
                rows.append(row)
    rows.sort(key=lambda x: (x.get("filed", ""), x.get("end", "")), reverse=True)
    return safe_float(rows[0].get("val")) if rows else 0.0


def latest_fact_row(facts: dict, tags: list[str], forms=("10-K", "10-Q", "20-F", "40-F")) -> dict:
    rows = []
    for tag in tags:
        for row in fact_units(facts, tag):
            if row.get("form") in forms and row.get("val") is not None:
                item = dict(row)
                item["tag"] = tag
                rows.append(item)
    rows.sort(key=lambda x: (x.get("filed", ""), x.get("end", "")), reverse=True)
    return rows[0] if rows else {}


def period_series(facts: dict, tags: list[str], limit: int = 16) -> list[dict]:
    rows = []
    annual_rows = []
    for tag in tags:
        for row in fact_units(facts, tag):
            frame = str(row.get("frame", ""))
            form = row.get("form")
            val = safe_float(row.get("val"), None)
            if val is None or form not in {"10-Q", "10-K", "20-F", "40-F"}:
                continue
            if row.get("fp") == "FY" and form in {"10-K", "20-F", "40-F"}:
                item = dict(row)
                item["tag"] = tag
                annual_rows.append(item)
            if "Q" not in frame or frame.endswith("I"):
                continue
            rows.append({
                "date": row.get("end") or row.get("filed"),
                "filed": row.get("filed"),
                "fy": row.get("fy"),
                "fp": row.get("fp"),
                "frame": frame,
                "value": val,
                "form": form,
                "tag": tag,
            })
    existing_frames = {row["frame"] for row in rows}
    for annual in annual_rows:
        fy = annual.get("fy")
        tag = annual.get("tag")
        if fy is None:
            continue
        q_rows = [row for row in rows if row.get("fy") == fy and row.get("tag") == tag and row.get("fp") in {"Q1", "Q2", "Q3"}]
        q4_frame = f"CY{fy}Q4"
        if len(q_rows) >= 3 and q4_frame not in existing_frames:
            q4_value = safe_float(annual.get("val")) - sum(safe_float(row.get("value")) for row in q_rows[:3])
            rows.append({
                "date": annual.get("end") or annual.get("filed"),
                "filed": annual.get("filed"),
                "fy": fy,
                "fp": "Q4",
                "frame": q4_frame,
                "value": q4_value,
                "form": annual.get("form"),
                "tag": tag,
            })
    by_frame = {}
    for row in rows:
        key = row["frame"] or f"{row['fy']}-{row['fp']}"
        current = by_frame.get(key)
        if not current or row.get("filed", "") > current.get("filed", ""):
            by_frame[key] = row
    series = sorted(by_frame.values(), key=lambda x: x.get("date") or "")[-limit:]
    return series


def instant_series(facts: dict, tags: list[str], limit: int = 16) -> list[dict]:
    rows = []
    for tag in tags:
        for row in fact_units(facts, tag):
            frame = str(row.get("frame", ""))
            form = row.get("form")
            val = safe_float(row.get("val"), None)
            if val is None or form not in {"10-Q", "10-K", "20-F", "40-F"}:
                continue
            if "Q" not in frame:
                continue
            rows.append({
                "date": row.get("end") or row.get("filed"),
                "filed": row.get("filed"),
                "fy": row.get("fy"),
                "fp": row.get("fp"),
                "frame": frame,
                "value": val,
                "form": form,
                "tag": tag,
            })
    by_frame = {}
    for row in rows:
        key = row["frame"] or f"{row['fy']}-{row['fp']}"
        current = by_frame.get(key)
        if not current or row.get("filed", "") > current.get("filed", ""):
            by_frame[key] = row
    return sorted(by_frame.values(), key=lambda x: x.get("date") or "")[-limit:]


def subtract_series(left: list[dict], right: list[dict], tag: str, limit: int = 16) -> list[dict]:
    right_by_date = {row.get("date"): row for row in right if row.get("date")}
    output = []
    for row in left:
        match = right_by_date.get(row.get("date"))
        if not match:
            continue
        output.append({
            "date": row.get("date"),
            "filed": row.get("filed") or match.get("filed"),
            "fy": row.get("fy"),
            "fp": row.get("fp"),
            "frame": row.get("frame"),
            "value": safe_float(row.get("value")) - abs(safe_float(match.get("value"))),
            "form": row.get("form"),
            "tag": tag,
        })
    return output[-limit:]


def series_change(series: list[dict]) -> dict:
    if not series:
        return {"qoq": None, "yoy": None}
    latest = safe_float(series[-1].get("value"))
    prev = safe_float(series[-2].get("value")) if len(series) >= 2 else 0
    year_ago = safe_float(series[-5].get("value")) if len(series) >= 5 else 0
    return {
        "qoq": ((latest / prev) - 1) if prev else None,
        "yoy": ((latest / year_ago) - 1) if year_ago else None,
    }


def annual_growth(facts: dict, tags: list[str]) -> float:
    rows = []
    for tag in tags:
        for row in fact_units(facts, tag):
            if row.get("form") in {"10-K", "20-F", "40-F"} and row.get("fp") == "FY":
                rows.append(row)
    rows.sort(key=lambda x: (x.get("fy", 0), x.get("filed", "")), reverse=True)
    clean = [safe_float(r.get("val")) for r in rows if safe_float(r.get("val")) > 0]
    if len(clean) < 2:
        return 0.0
    return clamp((clean[0] / clean[1]) - 1, -0.8, 1.5)


def get_sec_financials(ticker: str) -> tuple[dict, list[str]]:
    cik = CIK_BY_TICKER.get(ticker)
    if not cik:
        return {}, ["SEC CIK not configured for this ticker yet."]
    try:
        facts = sec_request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        revenue_tags = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"]
        net_income_tags = ["NetIncomeLoss", "ProfitLoss"]
        ocf_tags = ["NetCashProvidedByUsedInOperatingActivities"]
        capex_tags = ["PaymentsToAcquirePropertyPlantAndEquipment"]
        cost_revenue_tags = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization"]
        cash_tags = ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "CashCashEquivalentsAndShortTermInvestments"]
        debt_current_tags = ["ShortTermBorrowings", "LongTermDebtAndFinanceLeaseObligationsCurrent", "LongTermDebtCurrent", "CurrentPortionOfLongTermDebt"]
        debt_long_tags = ["LongTermDebtAndFinanceLeaseObligationsNoncurrent", "LongTermDebtNoncurrent", "LongTermDebt"]
        interest_tags = ["InterestExpenseNonOperating", "InterestExpense"]
        pretax_tags = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxes", "IncomeBeforeIncomeTaxes"]
        tax_tags = ["IncomeTaxExpenseBenefit"]
        filing_row = latest_fact_row(facts, revenue_tags + net_income_tags)
        revenue = latest_fact(facts, revenue_tags)
        net_income = latest_fact(facts, net_income_tags)
        ocf = latest_fact(facts, ocf_tags)
        capex = abs(latest_fact(facts, capex_tags))
        assets = latest_fact(facts, ["Assets"])
        liabilities = latest_fact(facts, ["Liabilities"])
        equity = latest_fact(facts, ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"])
        shares = latest_fact(facts, ["WeightedAverageNumberOfDilutedSharesOutstanding"], forms=("10-K", "10-Q"))
        eps = latest_fact(facts, ["EarningsPerShareDiluted"], forms=("10-K", "10-Q"))
        operating_income = latest_fact(facts, ["OperatingIncomeLoss"])
        gross_profit = latest_fact(facts, ["GrossProfit"])
        if not gross_profit and revenue:
            cost_revenue = latest_fact(facts, cost_revenue_tags)
            gross_profit = revenue - abs(cost_revenue) if cost_revenue else 0
        cash = latest_fact(facts, cash_tags)
        debt_current = latest_fact(facts, debt_current_tags)
        debt_long = latest_fact(facts, debt_long_tags)
        total_debt = debt_current + debt_long
        if total_debt <= 0:
            total_debt = latest_fact(facts, ["DebtCurrent", "LongTermDebtAndFinanceLeaseObligations"])
        interest_expense = abs(latest_fact(facts, interest_tags))
        pretax_income = latest_fact(facts, pretax_tags)
        tax_provision = latest_fact(facts, tax_tags)
        revenue_trend = period_series(facts, revenue_tags)
        gross_trend = period_series(facts, ["GrossProfit"])
        if not gross_trend:
            cost_trend = period_series(facts, cost_revenue_tags)
            gross_trend = subtract_series(revenue_trend, cost_trend, "RevenueLessCostOfRevenue")
        trends = {
            "revenue": revenue_trend,
            "gross_profit": gross_trend,
            "net_income": period_series(facts, net_income_tags),
            "eps": period_series(facts, ["EarningsPerShareDiluted", "EarningsPerShareBasic"]),
            "operating_income": period_series(facts, ["OperatingIncomeLoss"]),
            "operating_cash_flow": period_series(facts, ocf_tags),
            "capex": period_series(facts, capex_tags),
            "shares": period_series(facts, ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"]),
            "assets": instant_series(facts, ["Assets"]),
            "liabilities": instant_series(facts, ["Liabilities"]),
            "equity": instant_series(facts, ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
            "cash": instant_series(facts, cash_tags),
        }
        changes = {key: series_change(value) for key, value in trends.items()}
        return {
            "revenue": revenue,
            "revenue_growth": annual_growth(facts, revenue_tags),
            "net_income": net_income,
            "operating_income": operating_income,
            "gross_profit": gross_profit,
            "operating_cash_flow": ocf,
            "capex": capex,
            "free_cash_flow": ocf - capex,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "shares": shares,
            "eps": eps,
            "cash": cash,
            "total_debt": total_debt,
            "interest_expense": interest_expense,
            "pretax_income": pretax_income,
            "tax_provision": tax_provision,
            "latest_report": {
                "form": filing_row.get("form", "N/A"),
                "period_end": filing_row.get("end", "N/A"),
                "filed": filing_row.get("filed", "N/A"),
                "fiscal_period": filing_row.get("fp", "N/A"),
                "fiscal_year": filing_row.get("fy", "N/A"),
            },
            "trends": trends,
            "changes": changes,
            "guidance": build_guidance_watchlist(ticker, changes),
            "source": "SEC EDGAR companyfacts",
        }, ["SEC companyfacts connected."]
    except Exception as exc:
        return {}, [f"SEC companyfacts unavailable: {exc.__class__.__name__}."]


def fallback_snapshot(ticker: str, profile: dict) -> dict:
    rnd = ticker_seed(ticker)
    price = round(20 + rnd.random() * 280, 2)
    market_cap = (2 + rnd.random() * 850) * 1_000_000_000
    eps = max(0.35, price / (14 + rnd.random() * 28))
    return {
        "code": f"US.{ticker}",
        "name": ticker,
        "price": price,
        "market_cap": market_cap,
        "prev_close_price": price * (0.99 + rnd.random() * 0.02),
        "pe": price / eps,
        "pe_ttm": price / eps,
        "pb": 1.2 + rnd.random() * 9,
        "ey_ratio": eps / price * 100,
        "eps": eps,
        "book_per_share": price / (1.2 + rnd.random() * 9),
        "volume": 800_000 + rnd.random() * 45_000_000,
        "turnover_rate": 0.4 + rnd.random() * 4,
        "volume_ratio": 0.7 + rnd.random() * 2.4,
        "bid_ask_ratio": -40 + rnd.random() * 80,
        "source": "deterministic fallback",
    }


def fallback_financials(ticker: str, snapshot: dict, profile: dict) -> dict:
    rnd = ticker_seed(ticker)
    market_cap = max(snapshot.get("market_cap", 0), 1_000_000_000)
    price = max(snapshot.get("price", 0), 1)
    shares = market_cap / price
    revenue_multiple = 2.0 + rnd.random() * 7.5
    revenue = market_cap / revenue_multiple
    net_margin = 0.07 + rnd.random() * 0.23
    if "low_margin" in profile["traits"]:
        net_margin = 0.025 + rnd.random() * 0.05
    if "turnaround" in profile["traits"]:
        net_margin = 0.0 + rnd.random() * 0.08
    net_income = revenue * net_margin
    ocf = net_income * (0.9 + rnd.random() * 0.7)
    capex_ratio = 0.04 + rnd.random() * 0.07
    if "heavy_asset" in profile["traits"]:
        capex_ratio = 0.12 + rnd.random() * 0.16
    capex = revenue * capex_ratio
    assets = market_cap * (0.8 + rnd.random() * 1.8)
    liabilities = assets * (0.25 + rnd.random() * 0.45)
    equity = assets - liabilities
    return {
        "revenue": revenue,
        "revenue_growth": profile["growth"] * (0.7 + rnd.random() * 0.8),
        "net_income": net_income,
        "operating_income": net_income * 1.25,
        "gross_profit": revenue * (0.28 + rnd.random() * 0.38),
        "operating_cash_flow": ocf,
        "capex": capex,
        "free_cash_flow": ocf - capex,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "shares": shares,
        "eps": snapshot.get("eps") or (net_income / shares),
        "cash": assets * (0.06 + rnd.random() * 0.16),
        "total_debt": liabilities * (0.25 + rnd.random() * 0.45),
        "interest_expense": liabilities * (0.012 + rnd.random() * 0.025),
        "pretax_income": net_income / 0.82 if net_income > 0 else net_income,
        "tax_provision": max(net_income / 0.82 - net_income, 0),
        "latest_report": {
            "form": "N/A",
            "period_end": "N/A",
            "filed": "N/A",
            "fiscal_period": "N/A",
            "fiscal_year": "N/A",
        },
        "trends": fallback_trends(revenue, net_income, ocf, capex, profile["growth"]),
        "changes": {},
        "guidance": build_guidance_watchlist(ticker, {}),
        "source": "model fallback",
    }


def enrich_snapshot_with_financials(snapshot: dict, fin: dict) -> list[str]:
    notes = []
    price = safe_float(snapshot.get("price"))
    shares = safe_float(fin.get("shares")) or safe_float(snapshot.get("outstanding_shares"))
    eps_points = fin.get("trends", {}).get("eps", []) or []
    eps_ttm = sum(safe_float(row.get("value")) for row in eps_points[-4:]) if len(eps_points) >= 4 else 0
    if eps_ttm:
        fin["eps_ttm"] = eps_ttm
    eps = safe_float(snapshot.get("eps")) or eps_ttm or safe_float(fin.get("eps"))
    equity = safe_float(fin.get("equity"))
    market_cap = safe_float(snapshot.get("market_cap"))
    if price > 0 and shares > 0 and market_cap <= 0:
        snapshot["market_cap"] = price * shares
        notes.append("Market cap estimated from live price and SEC diluted shares.")
    if eps and safe_float(snapshot.get("eps")) <= 0:
        snapshot["eps"] = eps
        snapshot["pe"] = price / eps if price and eps else 0
        snapshot["pe_ttm"] = snapshot["pe"]
        snapshot["ey_ratio"] = eps / price * 100 if price else 0
        notes.append("PE/EPS filled from SEC TTM EPS and live price." if eps_ttm else "PE/EPS filled from SEC latest EPS and live price.")
    if equity > 0 and shares > 0:
        book_per_share = equity / shares
        if book_per_share > 0 and safe_float(snapshot.get("book_per_share")) <= 0:
            snapshot["book_per_share"] = book_per_share
            snapshot["pb"] = price / book_per_share if price else 0
            notes.append("P/B filled from SEC equity and diluted shares.")
    if notes and "Yahoo Finance chart" in str(snapshot.get("source", "")):
        snapshot["source"] = "Yahoo Finance chart + SEC filings"
    return notes


def fallback_trends(revenue: float, net_income: float, ocf: float, capex: float, growth: float) -> dict:
    today = date.today()
    points = []
    for idx in range(12, 0, -1):
        period_date = today - timedelta(days=idx * 91)
        scale = (1 + growth / 4) ** (12 - idx)
        points.append({"date": period_date.isoformat(), "value": revenue / 4 * scale, "form": "model"})
    return {
        "revenue": points,
        "net_income": [{**p, "value": p["value"] * (net_income / max(revenue, 1))} for p in points],
        "eps": [{**p, "value": (net_income / max(revenue, 1)) * 0.25} for p in points],
        "operating_income": [{**p, "value": p["value"] * (net_income * 1.25 / max(revenue, 1))} for p in points],
        "gross_profit": [{**p, "value": p["value"] * 0.45} for p in points],
        "operating_cash_flow": [{**p, "value": p["value"] * (ocf / max(revenue, 1))} for p in points],
        "capex": [{**p, "value": p["value"] * (capex / max(revenue, 1))} for p in points],
        "shares": [{**p, "value": 1_000_000_000} for p in points],
        "assets": [{**p, "value": p["value"] * 2.0} for p in points],
        "liabilities": [{**p, "value": p["value"] * 1.6} for p in points],
        "equity": [{**p, "value": p["value"] * 0.4} for p in points],
        "cash": [{**p, "value": p["value"] * 0.2} for p in points],
    }


def build_guidance_watchlist(ticker: str, changes: dict) -> list[dict]:
    revenue_change = changes.get("revenue", {}) if changes else {}
    net_income_change = changes.get("net_income", {}) if changes else {}
    gross_change = changes.get("gross_profit", {}) if changes else {}
    capex_change = changes.get("capex", {}) if changes else {}
    return [
        {
            "name": "Revenue & EPS Outlook",
            "status": "需要业绩新闻稿/电话会 / needs earnings release / transcript",
            "context": "SEC XBRL 没有统一的未来营收/EPS 指引字段；这里先展示最新实际营收和净利润的 YoY/QoQ / SEC XBRL has no standard forward revenue/EPS guidance field; showing actual revenue and net income YoY/QoQ first.",
            "yoy": revenue_change.get("yoy"),
            "qoq": revenue_change.get("qoq"),
            "secondary_yoy": net_income_change.get("yoy"),
            "secondary_qoq": net_income_change.get("qoq"),
        },
        {
            "name": "Margin Guidance",
            "status": "需要业绩新闻稿/电话会 / needs earnings release / transcript",
            "context": "毛利率展望通常出现在 earnings call 或 IR deck；当前用毛利额趋势作为代理 / Margin outlook usually appears in earnings calls or IR decks; gross profit trend is used as a proxy for now.",
            "yoy": gross_change.get("yoy"),
            "qoq": gross_change.get("qoq"),
        },
        {
            "name": "Capex Guidance",
            "status": "需要业绩新闻稿/电话会 / needs earnings release / transcript",
            "context": "Capex 计划通常是管理层口径；当前展示实际资本开支的 YoY/QoQ / Capex plans are usually management guidance; actual capex YoY/QoQ is shown for now.",
            "yoy": capex_change.get("yoy"),
            "qoq": capex_change.get("qoq"),
        },
        {
            "name": "Buybacks & Dividends",
            "status": "需要解析10-Q/10-K现金流 / needs 10-Q/10-K cash-flow parsing",
            "context": "下一步可从回购、分红、股本变化和董事会授权公告中提取 / Next step is extracting buybacks, dividends, share-count change, and board authorizations.",
            "yoy": None,
            "qoq": None,
        },
    ]


def apply_official_earnings_overlay(ticker: str, fin: dict) -> list[str]:
    official = OFFICIAL_EARNINGS.get(ticker)
    if not official:
        return []
    current_report = fin.get("latest_report", {})
    official_report = dict(official.get("latest_report", {}))
    if official_report.get("period_end", "") >= current_report.get("period_end", ""):
        official_report["source"] = official["source"]
        official_report["source_url"] = official["source_url"]
        official_report["sec_filed"] = current_report.get("filed", "")
        fin["latest_report"] = official_report
    for key, value in official.get("actuals", {}).items():
        fin[key] = value
        rows = fin.get("trends", {}).get(key) or []
        if rows:
            rows[-1]["value"] = value
            rows[-1]["date"] = official_report.get("period_end", rows[-1].get("date"))
            rows[-1]["filed"] = official_report.get("filed", rows[-1].get("filed"))
            rows[-1]["form"] = official_report.get("form", rows[-1].get("form"))
            rows[-1]["tag"] = f"{official['source']} actual"
    if "revenue" in official.get("actuals", {}) and "net_income" in official.get("actuals", {}):
        fin["source"] = f"{fin.get('source', 'financial data')} + {official['source']} latest release overlay"
        fin["changes"] = {key: series_change(value) for key, value in fin.get("trends", {}).items()}
    merged = []
    for item in official.get("guidance", []):
        enriched = dict(item)
        enriched["source"] = official["source"]
        enriched["source_url"] = official["source_url"]
        merged.append(enriched)
    if merged:
        fin["guidance"] = merged
    return [f"{ticker} official IR earnings release connected: {official['source_url']}"]


def format_size(market_cap: float) -> str:
    if market_cap >= 200_000_000_000:
        return "Mega cap"
    if market_cap >= 10_000_000_000:
        return "Large cap"
    if market_cap >= 2_000_000_000:
        return "Mid cap"
    return "Small cap"


def baseline_macro(note: str) -> tuple[dict, list[str]]:
    return {
            "regime": "Manual baseline: mildly restrictive",
            "fed_policy": "Restrictive / data-dependent",
            "discount_rate": 0.102,
            "equity_risk_premium": 0.047,
            "yield_curve": "Unknown live curve",
            "liquidity": "Neutral to tight",
            "tariff_regime": "Section 301 / export-control sensitive names need extra haircut",
            "source": "local baseline",
        }, [note]


def macro_regime() -> tuple[dict, list[str]]:
    fred_key = os.environ.get("FRED_API_KEY")
    if not fred_key:
        return baseline_macro("FRED_API_KEY not set; macro regime uses a local baseline.")
    try:
        def fred_latest(series_id: str) -> float:
            params = urllib.parse.urlencode({
                "series_id": series_id,
                "api_key": fred_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            })
            req = urllib.request.Request(f"https://api.stlouisfed.org/fred/series/observations?{params}")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            return safe_float(data["observations"][0]["value"])

        ten_y = fred_latest("DGS10")
        two_y = fred_latest("DGS2")
        fed_funds = fred_latest("FEDFUNDS")
        curve = ten_y - two_y
        restrictive = fed_funds > 3.5 or ten_y > 4
        return {
            "regime": "Live FRED: restrictive" if restrictive else "Live FRED: neutral/easy",
            "fed_policy": f"Fed funds {fed_funds:.2f}%",
            "discount_rate": clamp(0.06 + ten_y / 100 + 0.025, 0.075, 0.14),
            "equity_risk_premium": 0.047,
            "yield_curve": f"10Y {ten_y:.2f}% / 2Y {two_y:.2f}% / spread {curve:.2f}%",
            "liquidity": "Tight" if restrictive else "Neutral",
            "tariff_regime": "Monitor USTR tariff and export-control headlines",
            "source": "FRED API",
        }, ["FRED macro data connected."]
    except Exception as exc:
        return baseline_macro(f"FRED unavailable: {exc.__class__.__name__}; macro regime uses a local baseline.")


def score_financials(fin: dict) -> dict:
    revenue = max(fin["revenue"], 1)
    net_margin = fin["net_income"] / revenue
    gross_margin = fin["gross_profit"] / revenue if fin["gross_profit"] else 0.0
    fcf_margin = fin["free_cash_flow"] / revenue
    debt_to_assets = fin["liabilities"] / max(fin["assets"], 1)
    roe = fin["net_income"] / max(fin["equity"], 1)
    fcf_conversion = fin["free_cash_flow"] / max(abs(fin["net_income"]), 1)

    quality = 50
    quality += clamp(fin["revenue_growth"] * 130, -25, 25)
    quality += clamp(net_margin * 90, -20, 22)
    quality += clamp(fcf_margin * 120, -20, 25)
    quality += clamp((0.55 - debt_to_assets) * 45, -18, 18)
    quality += clamp((fcf_conversion - 0.8) * 18, -12, 12)

    return {
        "score": round(clamp(quality, 0, 100)),
        "revenue_growth": fin["revenue_growth"],
        "gross_margin": gross_margin,
        "net_margin": net_margin,
        "fcf_margin": fcf_margin,
        "debt_to_assets": debt_to_assets,
        "roe": roe,
        "fcf_conversion": fcf_conversion,
    }


def valuation_methods(ticker: str, snapshot: dict, fin: dict, profile: dict, macro: dict, metrics: dict) -> tuple[list[dict], dict]:
    sector_model = SECTOR_DEFAULTS.get(profile["sector"], SECTOR_DEFAULTS["default"])
    price = max(snapshot["price"], 0.01)
    shares = max(fin["shares"] or snapshot.get("outstanding_shares") or snapshot["market_cap"] / price, 1)
    raw_eps = fin.get("eps_ttm") or fin.get("eps") or snapshot.get("eps")
    eps = safe_float(raw_eps)
    if eps <= 0 and fin["net_income"] > 0:
        eps = fin["net_income"] / shares
    revenue_per_share = fin["revenue"] / shares
    fcf_per_share = fin["free_cash_flow"] / shares
    book_per_share = fin["equity"] / shares if fin["equity"] > 0 else snapshot.get("book_per_share", 0)
    expected_growth = clamp((profile["growth"] * 0.6) + (metrics["revenue_growth"] * 0.4), -0.05, 0.35)
    forward_eps = eps * (1 + expected_growth)
    ebitda = max(fin["operating_income"] + abs(fin["capex"]) * 0.55, 0)
    net_debt = max(fin["liabilities"] - max(fin["operating_cash_flow"], 0), 0)
    enterprise_value = snapshot.get("market_cap", price * shares) + net_debt
    current_pe = price / eps if eps else 0
    current_forward_pe = price / forward_eps if forward_eps else 0
    current_ps = snapshot.get("market_cap", price * shares) / fin["revenue"] if fin["revenue"] else 0
    current_pb = price / book_per_share if book_per_share else 0
    current_pfcf = price / fcf_per_share if fcf_per_share else 0
    current_ev_ebitda = enterprise_value / ebitda if ebitda else 0

    methods = []

    def add(
        key: str,
        name: str,
        fair_value: float,
        why: str,
        confidence: str,
        invalid_reason: str = "",
        include_negative: bool = True,
        metric_label: str = "",
        metric_value: float | None = None,
        target_label: str = "",
        target_value: float | None = None,
    ):
        has_value = fair_value != 0 and math.isfinite(fair_value)
        applicable = has_value if include_negative else fair_value > 0 and math.isfinite(fair_value)
        upside = (fair_value / price - 1) * 100 if applicable else None
        low_value = min(fair_value * 0.88, fair_value * 1.12) if applicable else None
        high_value = max(fair_value * 0.88, fair_value * 1.12) if applicable else None
        negative_note = " 负估值意味着该方法下股权价值被现金流、亏损或净债务拖到 0 以下，风险很高 / Negative fair value means cash flow, losses, or net debt push equity value below zero; risk is high." if applicable and fair_value < 0 else ""
        methods.append({
            "key": key,
            "name": name,
            "fair_value": round(fair_value, 2) if applicable else None,
            "low": round(low_value, 2) if applicable else None,
            "high": round(high_value, 2) if applicable else None,
            "upside": round(upside, 1) if upside is not None else None,
            "valuation_label": valuation_label(upside) if upside is not None else "不适用 / Not applicable",
            "why": why + negative_note,
            "confidence": "Risk" if applicable and fair_value < 0 else confidence if applicable else "N/A",
            "weight": sector_model["method_weights"].get(key, 0.05) if applicable else 0,
            "display_weight": sector_model["method_weights"].get(key, 0.05),
            "applicable": applicable,
            "invalid_reason": invalid_reason if not applicable else "",
            "is_negative": applicable and fair_value < 0,
            "metric_label": metric_label,
            "metric_value": round(metric_value, 2) if metric_value is not None and math.isfinite(metric_value) else None,
            "target_label": target_label,
            "target_value": round(target_value, 2) if target_value is not None and math.isfinite(target_value) else None,
        })

    add("pe", "Trailing PE", eps * sector_model["target_pe"], "适合已有稳定盈利的公司，用过去盈利做 sanity check / Best for companies with stable earnings; uses trailing profit as a sanity check.", "Medium", "EPS 为 0，Trailing PE 不能给出有效估值 / EPS is zero, so trailing PE cannot anchor valuation.", metric_label="Current PE", metric_value=current_pe, target_label="Target PE", target_value=sector_model["target_pe"])
    add("forward_pe", "Forward PE", forward_eps * sector_model["target_forward_pe"], "核心机构视角，反映未来 12 个月盈利预期；需配合预期上修/下修 / Institutional lens for next-12-month earnings; must be judged with estimate revisions.", "High", "Forward EPS 为 0 或缺失，Forward PE 暂不适用 / Forward EPS is zero or missing, so Forward PE is not applicable.", metric_label="Current Forward PE", metric_value=current_forward_pe, target_label="Target Forward PE", target_value=sector_model["target_forward_pe"])
    fair_peg_pe = clamp(max(expected_growth, 0.02) * 100 * 1.15, 10, 48)
    peg_ratio = current_forward_pe / (expected_growth * 100) if current_forward_pe and expected_growth else 0
    add("peg", "PEG Ratio", forward_eps * fair_peg_pe, f"PEG 是 Forward PE / EPS 增速的比值；当前 PEG Ratio 约 {peg_ratio:.2f} / PEG equals Forward PE divided by EPS growth; current PEG is about {peg_ratio:.2f}.", "Medium", "Forward EPS 或增长率为 0，PEG Ratio 不适用 / Forward EPS or growth is zero, so PEG is not applicable.", metric_label="Current PEG", metric_value=peg_ratio, target_label="Fair PEG", target_value=1.15)
    add("ps", "Price / Sales", revenue_per_share * sector_model["target_ps"], "适合高成长或利润暂时被投入压低的公司，但低毛利业务要打折 / Useful for high-growth companies or firms investing through margins; low-margin businesses need a haircut.", "Medium", metric_label="Current P/S", metric_value=current_ps, target_label="Target P/S", target_value=sector_model["target_ps"])
    add("pb", "Price / Book", book_per_share * sector_model["target_pb"], "金融、保险、重资产公司更有用；轻资产科技股只作参考 / More useful for financials, insurers, and asset-heavy companies; only a reference for asset-light tech.", "Medium", metric_label="Current P/B", metric_value=current_pb, target_label="Target P/B", target_value=sector_model["target_pb"])
    add("pfcf", "Price / FCF", fcf_per_share * sector_model["target_pfcf"], "现金流是估值的硬地板，适合成熟优质公司 / Cash flow is the hard floor of valuation; useful for mature quality companies.", "High" if fcf_per_share > 0 else "Low", "自由现金流为 0，P/FCF 不能作为估值锚 / Free cash flow is zero, so P/FCF cannot anchor valuation.", metric_label="Current P/FCF", metric_value=current_pfcf, target_label="Target P/FCF", target_value=sector_model["target_pfcf"])
    equity_value = ebitda * sector_model["target_ev_ebitda"] - net_debt if sector_model["target_ev_ebitda"] > 0 else 0
    add("ev_ebitda", "EV / EBITDA", equity_value / shares, "适合周期、工业、能源、半导体等资本密集行业 / Fits cyclical, industrial, energy, semiconductor, and capital-intensive industries.", "High", "EBITDA 为 0，EV/EBITDA 暂不适用 / EBITDA is zero, so EV/EBITDA is not applicable.", metric_label="Current EV/EBITDA", metric_value=current_ev_ebitda, target_label="Target EV/EBITDA", target_value=sector_model["target_ev_ebitda"])

    dcf_value = dcf_per_share(
        fcf_per_share=fcf_per_share,
        growth=expected_growth,
        discount_rate=macro["discount_rate"] + risk_discount(profile, metrics),
        terminal_growth=0.025,
    )
    add("dcf", "DCF", dcf_value, "理论最完整，但对折现率和终值敏感；用于给估值区间定锚 / The most complete theory, but sensitive to discount rate and terminal value; useful as a valuation anchor.", "Medium", "折现假设无效，DCF 暂不适用 / Discount assumptions are invalid, so DCF is not applicable.", metric_label="Discount rate", metric_value=macro["discount_rate"] + risk_discount(profile, metrics), target_label="Terminal growth", target_value=0.025)

    usable = [m for m in methods if m["applicable"] and not m["is_negative"] and m["weight"] > 0]
    weight_sum = sum(m["weight"] for m in usable)
    weighted = sum(m["fair_value"] * m["weight"] for m in usable) / weight_sum if weight_sum else price
    low = sum(m["low"] * m["weight"] for m in usable) / weight_sum if weight_sum else price * 0.9
    high = sum(m["high"] * m["weight"] for m in usable) / weight_sum if weight_sum else price * 1.1
    valuation_score = clamp(50 + (weighted / price - 1) * 80, 0, 100)
    return methods, {
        "current_price": round(price, 2),
        "fair_value": round(weighted, 2),
        "range_low": round(low, 2),
        "range_high": round(high, 2),
        "upside": round((weighted / price - 1) * 100, 1),
        "score": round(valuation_score),
        "expected_growth": expected_growth,
        "forward_eps": forward_eps,
        "forward_pe": price / forward_eps if forward_eps > 0 else 0,
        "peg_ratio": peg_ratio,
    }


def valuation_label(upside: float) -> str:
    if upside is None:
        return "不适用 / Not applicable"
    if upside >= 0:
        return f"当前股价低估 {upside:.1f}% / current price is undervalued by {upside:.1f}%"
    return f"当前股价高估 {abs(upside):.1f}% / current price is overvalued by {abs(upside):.1f}%"


def risk_discount(profile: dict, metrics: dict) -> float:
    extra = 0.0
    traits = set(profile["traits"])
    if "turnaround" in traits:
        extra += 0.018
    if "meme_sensitive" in traits:
        extra += 0.012
    if "geopolitical" in traits or "export_control" in traits:
        extra += 0.01
    if metrics["fcf_margin"] < 0:
        extra += 0.015
    if metrics["debt_to_assets"] > 0.65:
        extra += 0.012
    return extra


def dcf_per_share(fcf_per_share: float, growth: float, discount_rate: float, terminal_growth: float) -> float:
    if discount_rate <= terminal_growth:
        return 0
    growth = clamp(growth, -0.03, 0.22)
    value = 0.0
    fcf = fcf_per_share
    for year in range(1, 6):
        fcf *= 1 + growth
        value += fcf / ((1 + discount_rate) ** year)
    terminal = fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    value += terminal / ((1 + discount_rate) ** 5)
    return value


def estimate_beta(profile: dict, snapshot: dict) -> float:
    traits = set(profile.get("traits", []))
    beta = 1.0
    if "high_growth" in traits or "ai" in traits:
        beta += 0.25
    if "cyclical" in traits or "commodity_sensitive" in traits:
        beta += 0.18
    if "defensive" in traits:
        beta -= 0.22
    if "turnaround" in traits or "meme_sensitive" in traits:
        beta += 0.22
    if snapshot.get("market_cap", 0) < 10_000_000_000:
        beta += 0.12
    return round(clamp(beta, 0.55, 2.35), 2)


def calculate_dcf_model(inputs: dict) -> dict:
    fcf = safe_float(inputs.get("base_fcf_b"))
    revenue = safe_float(inputs.get("revenue_b"))
    fcf_margin = safe_float(inputs.get("fcf_margin"))
    if fcf == 0 and revenue and fcf_margin:
        fcf = revenue * fcf_margin
    shares = max(safe_float(inputs.get("shares_b")), 0.0001)
    cash = safe_float(inputs.get("cash_b"))
    debt = safe_float(inputs.get("debt_b"))
    discount = safe_float(inputs.get("discount_rate"))
    terminal_growth = safe_float(inputs.get("terminal_growth"))
    growth_1 = safe_float(inputs.get("growth_stage_1"))
    growth_2 = safe_float(inputs.get("growth_stage_2"))
    years_1 = int(clamp(safe_float(inputs.get("years_stage_1"), 5), 1, 10))
    years_2 = int(clamp(safe_float(inputs.get("years_stage_2"), 5), 0, 10))
    current_price = safe_float(inputs.get("current_price"))

    projections = []
    pv_sum = 0.0
    current_fcf = fcf
    for year in range(1, years_1 + years_2 + 1):
        growth = growth_1 if year <= years_1 else growth_2
        current_fcf *= 1 + growth
        pv = current_fcf / ((1 + discount) ** year) if discount > -0.99 else 0
        pv_sum += pv
        projections.append({"year": year, "growth": growth, "fcf_b": current_fcf, "pv_b": pv})

    if discount <= terminal_growth:
        terminal_value = None
        terminal_pv = None
        enterprise_value = pv_sum
        warning = "折现率必须高于永续增长率，否则 Gordon Growth 终值会失真。"
    else:
        terminal_value = current_fcf * (1 + terminal_growth) / (discount - terminal_growth)
        terminal_pv = terminal_value / ((1 + discount) ** max(len(projections), 1))
        enterprise_value = pv_sum + terminal_pv
        warning = ""

    equity_value = enterprise_value + cash - debt
    fair_price = equity_value / shares
    margin = (fair_price / current_price - 1) if current_price else None
    return {
        "enterprise_value_b": round(enterprise_value, 3),
        "equity_value_b": round(equity_value, 3),
        "fair_price": round(fair_price, 2),
        "margin_of_safety": round(margin, 4) if margin is not None else None,
        "terminal_value_b": round(terminal_value, 3) if terminal_value is not None else None,
        "terminal_pv_b": round(terminal_pv, 3) if terminal_pv is not None else None,
        "pv_stage_b": round(pv_sum, 3),
        "projections": [{**row, "growth": round(row["growth"], 4), "fcf_b": round(row["fcf_b"], 3), "pv_b": round(row["pv_b"], 3)} for row in projections],
        "warning": warning,
    }


def build_dcf_lab(ticker: str, snapshot: dict, fin: dict, profile: dict, macro: dict, metrics: dict) -> dict:
    def trailing_sum(metric: str) -> float:
        points = fin.get("trends", {}).get(metric, []) or []
        values = [safe_float(row.get("value")) for row in points[-4:]]
        return sum(values) if len(values) >= 4 else 0.0

    price = max(snapshot.get("price", 0), 0)
    market_cap_b = (snapshot.get("market_cap", 0) or price * max(fin.get("shares", 0), 0)) / 1_000_000_000
    shares_b = max(fin.get("shares") or snapshot.get("outstanding_shares") or (snapshot.get("market_cap", 0) / max(price, 0.01)), 0) / 1_000_000_000
    revenue_ttm = trailing_sum("revenue") or fin.get("revenue", 0)
    ocf_ttm = trailing_sum("operating_cash_flow")
    capex_ttm = abs(trailing_sum("capex"))
    fcf_ttm = ocf_ttm - capex_ttm if ocf_ttm else fin.get("free_cash_flow", 0)
    revenue_b = revenue_ttm / 1_000_000_000
    fcf_b = fcf_ttm / 1_000_000_000
    cash_b = fin.get("cash", 0) / 1_000_000_000
    liabilities_b = fin.get("liabilities", 0) / 1_000_000_000
    debt_b = (fin.get("total_debt", 0) or fin.get("liabilities", 0) * 0.35) / 1_000_000_000
    interest_b = fin.get("interest_expense", 0) / 1_000_000_000
    pretax_b = fin.get("pretax_income", 0) / 1_000_000_000
    tax_b = fin.get("tax_provision", 0) / 1_000_000_000
    risk_free = clamp((macro.get("discount_rate", 0.102) - 0.085), 0.025, 0.06)
    market_return = 0.10
    beta = estimate_beta(profile, snapshot)
    cost_of_debt = clamp(interest_b / debt_b if debt_b > 0 else risk_free + 0.018, 0.015, 0.12)
    tax_rate = clamp(tax_b / pretax_b if pretax_b > 0 else 0.21, 0.0, 0.32)
    debt_weight = debt_b / max(market_cap_b + debt_b, 0.0001)
    equity_weight = 1 - debt_weight
    cost_of_equity = risk_free + beta * (market_return - risk_free)
    wacc = debt_weight * cost_of_debt * (1 - tax_rate) + equity_weight * cost_of_equity
    growth_stage_1 = clamp(max(profile.get("growth", 0.06), metrics.get("revenue_growth", 0) * 0.35 + profile.get("growth", 0.06) * 0.65), -0.05, 0.35)
    growth_stage_2 = clamp(growth_stage_1 * 0.35, -0.02, 0.10)
    terminal_growth = 0.025
    discount_rate = clamp(max(wacc, macro.get("discount_rate", 0.1)) + risk_discount(profile, metrics) * 0.5, 0.06, 0.18)
    inputs = {
        "ticker": ticker,
        "current_price": round(price, 2),
        "market_cap_b": round(market_cap_b, 3),
        "shares_b": round(shares_b, 3),
        "revenue_b": round(revenue_b, 3),
        "base_fcf_b": round(fcf_b, 3),
        "fcf_margin": round(fcf_ttm / revenue_ttm if revenue_ttm else metrics.get("fcf_margin", 0), 4),
        "cash_b": round(cash_b, 3),
        "debt_b": round(debt_b, 3),
        "liabilities_b": round(liabilities_b, 3),
        "interest_expense_b": round(interest_b, 3),
        "pretax_income_b": round(pretax_b, 3),
        "tax_provision_b": round(tax_b, 3),
        "beta": beta,
        "risk_free_rate": round(risk_free, 4),
        "market_return": market_return,
        "cost_of_debt": round(cost_of_debt, 4),
        "cost_of_equity": round(cost_of_equity, 4),
        "tax_rate": round(tax_rate, 4),
        "debt_weight": round(debt_weight, 4),
        "equity_weight": round(equity_weight, 4),
        "wacc": round(wacc, 4),
        "discount_rate": round(discount_rate, 4),
        "growth_stage_1": round(growth_stage_1, 4),
        "years_stage_1": 5,
        "growth_stage_2": round(growth_stage_2, 4),
        "years_stage_2": 5,
        "terminal_growth": terminal_growth,
    }
    result = calculate_dcf_model(inputs)
    sensitivity = []
    for discount_shift in (-0.01, 0, 0.01):
        row = []
        for growth_shift in (-0.005, 0, 0.005):
            scenario = dict(inputs)
            scenario["discount_rate"] = max(inputs["discount_rate"] + discount_shift, 0.001)
            scenario["terminal_growth"] = max(inputs["terminal_growth"] + growth_shift, -0.02)
            row.append(calculate_dcf_model(scenario)["fair_price"])
        sensitivity.append({"discount_rate": round(inputs["discount_rate"] + discount_shift, 4), "values": row})
    return {
        "source": "Excel-inspired DCF v2 + SEC/Futu/FRED auto-fill",
        "units": "Billion USD unless noted",
        "inputs": inputs,
        "result": result,
        "sensitivity": sensitivity,
        "notes": [
            "新版 Excel 的 10 年两阶段 FCF 预测被保留，并加入 WACC 自动计算 / The new Excel-style 10-year two-stage FCF forecast is preserved with automatic WACC.",
            "Revenue、OCF、Capex 和 FCF 优先使用最近 4 个季度合计，避免把单季 FCF 当成年化基础 / Revenue, OCF, Capex, and FCF prefer TTM sums to avoid treating one quarter as annual FCF.",
            "WACC 默认用 CAPM：Cost of Equity = Risk-free + Beta * Market Premium；Cost of Debt = Interest Expense / Debt / Default WACC uses CAPM and interest expense over debt.",
            "Beta 暂用股票画像估算，页面可手动改；后续可接 Yahoo/GuruFocus 精确 beta / Beta is estimated from the stock profile for now and can be manually edited; Yahoo or GuruFocus beta can be connected later.",
        ],
    }


def fmt_money_short(value: float) -> str:
    value = safe_float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000_000:
        return f"{sign}${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    return f"{sign}${value:.2f}"


def fmt_pct_short(value: float | None, signed: bool = False) -> str:
    if value is None:
        return "N/A"
    number = safe_float(value, None)
    if number is None:
        return "N/A"
    prefix = "+" if signed and number >= 0 else ""
    return f"{prefix}{number * 100:.1f}%"


def metric_series(fin: dict, metric: str, limit: int = 8) -> list[dict]:
    return (fin.get("trends", {}).get(metric, []) or [])[-limit:]


def values_only(points: list[dict]) -> list[float]:
    return [safe_float(row.get("value")) for row in points]


def margin_series(fin: dict, numerator: str, denominator: str = "revenue", limit: int = 8) -> list[dict]:
    numer = metric_series(fin, numerator, limit)
    denom = metric_series(fin, denominator, limit)
    length = min(len(numer), len(denom))
    output = []
    for n_row, d_row in zip(numer[-length:], denom[-length:]):
        base = safe_float(d_row.get("value"))
        output.append({
            "date": n_row.get("date") or d_row.get("date"),
            "value": safe_float(n_row.get("value")) / base if base else 0,
        })
    return output


def fcf_series(fin: dict, limit: int = 8) -> list[dict]:
    ocf = metric_series(fin, "operating_cash_flow", limit)
    capex = metric_series(fin, "capex", limit)
    length = min(len(ocf), len(capex))
    output = []
    for ocf_row, capex_row in zip(ocf[-length:], capex[-length:]):
        output.append({
            "date": ocf_row.get("date") or capex_row.get("date"),
            "value": safe_float(ocf_row.get("value")) - abs(safe_float(capex_row.get("value"))),
        })
    return output


def pct_delta(latest: float, base: float) -> float | None:
    if not base:
        return None
    return latest / base - 1


def latest_prev_first(values: list[float]) -> tuple[float, float, float]:
    latest = values[-1] if values else 0
    prev = values[-2] if len(values) >= 2 else latest
    first = values[0] if values else latest
    return latest, prev, first


def display_trend(points: list[dict], kind: str = "money") -> list[dict]:
    output = []
    for row in points[-8:]:
        value = safe_float(row.get("value"))
        if kind == "pct":
            display = fmt_pct_short(value)
        elif kind == "number":
            display = f"{value:.2f}"
        elif kind == "shares":
            display = f"{value / 1_000_000_000:.2f}B"
        else:
            display = fmt_money_short(value)
        output.append({"date": row.get("date") or "", "value": round(value, 6), "display": display})
    return output


def history_change(points: list[dict]) -> tuple[float | None, float | None]:
    values = values_only(points)
    if not values:
        return None, None
    latest = values[-1]
    prev = values[-2] if len(values) >= 2 else 0
    year_ago = values[-5] if len(values) >= 5 else 0
    return pct_delta(latest, prev), pct_delta(latest, year_ago)


def derived_ratio_series(fin: dict, numerator: str, denominator: str, multiplier: float = 1.0, limit: int = 12) -> list[dict]:
    numer = metric_series(fin, numerator, limit)
    denom = metric_series(fin, denominator, limit)
    length = min(len(numer), len(denom))
    output = []
    for n_row, d_row in zip(numer[-length:], denom[-length:]):
        base = safe_float(d_row.get("value"))
        output.append({
            "date": n_row.get("date") or d_row.get("date"),
            "value": (safe_float(n_row.get("value")) * multiplier / base) if base else 0,
        })
    return output


def build_financial_metric_history(fin: dict, metrics: dict) -> list[dict]:
    fcf_points = fcf_series(fin, 12)
    fcf_margin_points = []
    revenue_points = metric_series(fin, "revenue", 12)
    length = min(len(fcf_points), len(revenue_points))
    for fcf_row, rev_row in zip(fcf_points[-length:], revenue_points[-length:]):
        rev = safe_float(rev_row.get("value"))
        fcf_margin_points.append({"date": fcf_row.get("date"), "value": safe_float(fcf_row.get("value")) / rev if rev else 0})

    cards = [
        {
            "key": "revenue",
            "name": "营收 / Revenue",
            "display": fmt_money_short(fin.get("revenue")),
            "points": display_trend(revenue_points),
            "why": "代表需求规模和商业天花板 / Shows demand scale and business ceiling.",
        },
        {
            "key": "gross_margin",
            "name": "毛利率 / Gross margin",
            "display": fmt_pct_short(metrics.get("gross_margin")),
            "points": display_trend(derived_ratio_series(fin, "gross_profit", "revenue"), "pct"),
            "why": "代表定价权、产品竞争力和产能利用率 / Shows pricing power, competitiveness, and utilization.",
        },
        {
            "key": "net_income",
            "name": "净利润 / Net income",
            "display": fmt_money_short(fin.get("net_income")),
            "points": display_trend(metric_series(fin, "net_income", 12)),
            "why": "代表最终盈利结果，亏损股修复时尤其关键 / Shows bottom-line profitability, especially important for turnaround stocks.",
        },
        {
            "key": "net_margin",
            "name": "净利率 / Net margin",
            "display": fmt_pct_short(metrics.get("net_margin")),
            "points": display_trend(derived_ratio_series(fin, "net_income", "revenue"), "pct"),
            "why": "代表收入最终能沉淀成利润的能力 / Shows how much revenue turns into profit.",
        },
        {
            "key": "eps",
            "name": "每股收益 / EPS",
            "display": f"{safe_float(fin.get('eps')):.2f}",
            "points": display_trend(metric_series(fin, "eps", 12), "number"),
            "why": "连接公司利润和单股价值，也是 PE/Forward PE 的核心输入 / Links company profit to per-share value and drives PE/Forward PE.",
        },
        {
            "key": "fcf_margin",
            "name": "自由现金流率 / FCF margin",
            "display": fmt_pct_short(metrics.get("fcf_margin")),
            "points": display_trend(fcf_margin_points, "pct"),
            "why": "代表利润质量和真实现金创造能力 / Shows earnings quality and real cash generation.",
        },
        {
            "key": "debt_to_assets",
            "name": "负债/资产 / Debt / Assets",
            "display": fmt_pct_short(metrics.get("debt_to_assets")),
            "points": display_trend(derived_ratio_series(fin, "liabilities", "assets"), "pct"),
            "why": "代表资产负债安全和抗周期能力 / Shows balance-sheet safety and cycle resilience.",
        },
        {
            "key": "roe",
            "name": "ROE / Return on Equity",
            "display": fmt_pct_short(metrics.get("roe")),
            "points": display_trend(derived_ratio_series(fin, "net_income", "equity", 4.0), "pct"),
            "why": "季度净利润年化后除以权益，代表股东资本回报效率 / Annualized quarterly net income over equity shows shareholder capital efficiency.",
        },
    ]
    for card in cards:
        if card["key"] in {"gross_margin", "net_margin", "fcf_margin", "debt_to_assets", "roe"}:
            values = values_only(card["points"])
            latest = values[-1] if values else 0
            prev = values[-2] if len(values) >= 2 else 0
            year_ago = values[-5] if len(values) >= 5 else 0
            qoq = latest - prev if len(values) >= 2 else None
            yoy = latest - year_ago if len(values) >= 5 else None
            card["change_type"] = "pp"
        else:
            qoq, yoy = history_change(card["points"])
            card["change_type"] = "pct"
        card["qoq"] = qoq
        card["yoy"] = yoy
        card["points"] = card["points"][-12:]
    return cards


def build_turnaround_model(ticker: str, snapshot: dict, fin: dict, profile: dict, metrics: dict) -> dict:
    revenue = metric_series(fin, "revenue")
    revenue_values = values_only(revenue)
    gross_margin = margin_series(fin, "gross_profit")
    gross_values = values_only(gross_margin)
    operating_margin = margin_series(fin, "operating_income" if metric_series(fin, "operating_income") else "net_income")
    operating_values = values_only(operating_margin)
    fcf_points = fcf_series(fin)
    fcf_values = values_only(fcf_points)
    fcf_margin_points = []
    for fcf_row, rev_row in zip(fcf_points[-len(revenue):], revenue[-len(fcf_points):]):
        rev = safe_float(rev_row.get("value"))
        fcf_margin_points.append({"date": fcf_row.get("date"), "value": safe_float(fcf_row.get("value")) / rev if rev else 0})
    fcf_margin_values = values_only(fcf_margin_points)
    shares = metric_series(fin, "shares")
    share_values = values_only(shares)

    latest_rev, prev_rev, first_rev = latest_prev_first(revenue_values)
    rev_qoq = pct_delta(latest_rev, prev_rev)
    rev_yoy = pct_delta(latest_rev, revenue_values[-5]) if len(revenue_values) >= 5 else None
    prev_rev_qoq = pct_delta(prev_rev, revenue_values[-3]) if len(revenue_values) >= 3 else None
    rev_accel = (rev_qoq or 0) - (prev_rev_qoq or 0)
    rev_score = clamp(52 + (rev_qoq or 0) * 150 + (rev_yoy or 0) * 60 + rev_accel * 180, 0, 100)

    latest_gm, prev_gm, first_gm = latest_prev_first(gross_values)
    gm_score = clamp(45 + latest_gm * 65 + (latest_gm - first_gm) * 260 + (latest_gm - prev_gm) * 160, 0, 100)

    latest_om, prev_om, first_om = latest_prev_first(operating_values)
    om_score = clamp(45 + latest_om * 140 + (latest_om - first_om) * 320 + (12 if latest_om > 0 else 0), 0, 100)

    latest_fcf, prev_fcf, first_fcf = latest_prev_first(fcf_values)
    latest_fcf_margin, _, first_fcf_margin = latest_prev_first(fcf_margin_values)
    fcf_score = clamp(45 + latest_fcf_margin * 130 + (latest_fcf_margin - first_fcf_margin) * 340 + (15 if latest_fcf > 0 else 0), 0, 100)

    cash = safe_float(fin.get("cash"))
    debt = safe_float(fin.get("total_debt"))
    assets = safe_float(fin.get("assets"))
    quarterly_burn = abs(latest_fcf) if latest_fcf < 0 else 0
    runway_quarters = cash / quarterly_burn if quarterly_burn else 12
    debt_to_assets = debt / assets if assets else metrics.get("debt_to_assets", 0)
    runway_score = clamp((min(runway_quarters, 12) / 8) * 80 + (20 if latest_fcf >= 0 else 0) - debt_to_assets * 25, 0, 100)

    share_latest, _, share_first = latest_prev_first(share_values)
    dilution = pct_delta(share_latest, share_first) if share_first and len(share_values) >= 2 else 0
    leverage_score = clamp(82 - max(dilution or 0, 0) * 360 - debt_to_assets * 55 + (8 if cash > debt else 0), 0, 100)

    rev_changes = []
    for idx in range(1, len(revenue_values)):
        change = pct_delta(revenue_values[idx], revenue_values[idx - 1])
        if change is not None:
            rev_changes.append(change)
    volatility = (max(rev_changes) - min(rev_changes)) if rev_changes else 0.15
    quality_score = clamp(48 + latest_gm * 55 + latest_fcf_margin * 90 - volatility * 75 + (8 if latest_rev > first_rev else 0), 0, 100)

    guidance_items = fin.get("guidance", []) or []
    guidance_score = clamp(48 + (8 if guidance_items else 0) + (10 if rev_qoq and rev_qoq > 0 else 0) + (10 if latest_om > first_om else 0) + (8 if latest_fcf_margin > first_fcf_margin else 0), 0, 100)

    def raw_item(label: str, value: str) -> dict:
        return {"label": label, "value": value}

    dimensions = [
        {
            "key": "revenue_reacceleration",
            "name": "营收重新加速 / Revenue re-acceleration",
            "weight": 0.15,
            "score": round(rev_score),
            "raw": [
                raw_item("最新季度营收 / Latest revenue", fmt_money_short(latest_rev)),
                raw_item("环比 / QoQ", fmt_pct_short(rev_qoq, True)),
                raw_item("同比 / YoY", fmt_pct_short(rev_yoy, True)),
            ],
            "trend": display_trend(revenue),
            "explanation": f"营收环比 {fmt_pct_short(rev_qoq, True)}，同比 {fmt_pct_short(rev_yoy, True)}；如果增长从负转正或环比继续抬升，说明需求端可能已经拐头 / Revenue QoQ is {fmt_pct_short(rev_qoq, True)} and YoY is {fmt_pct_short(rev_yoy, True)}; improving growth suggests demand may be turning.",
        },
        {
            "key": "gross_margin_recovery",
            "name": "毛利率修复 / Gross margin recovery",
            "weight": 0.15,
            "score": round(gm_score),
            "raw": [
                raw_item("最新毛利率 / Latest gross margin", fmt_pct_short(latest_gm)),
                raw_item("较首期变化 / Change vs first", fmt_pct_short(latest_gm - first_gm, True)),
                raw_item("环比变化 / QoQ margin change", fmt_pct_short(latest_gm - prev_gm, True)),
            ],
            "trend": display_trend(gross_margin, "pct"),
            "explanation": f"毛利率从 {fmt_pct_short(first_gm)} 到 {fmt_pct_short(latest_gm)}；毛利率改善通常代表降价压力缓解、产能利用率提高或产品结构变好 / Gross margin moved from {fmt_pct_short(first_gm)} to {fmt_pct_short(latest_gm)}, a useful signal for pricing, utilization, or mix recovery.",
        },
        {
            "key": "operating_loss_narrowing",
            "name": "经营亏损收窄 / Operating loss narrowing",
            "weight": 0.15,
            "score": round(om_score),
            "raw": [
                raw_item("最新经营利润率 / Latest operating margin", fmt_pct_short(latest_om)),
                raw_item("较首期变化 / Change vs first", fmt_pct_short(latest_om - first_om, True)),
                raw_item("是否转正 / Positive now", "是 / Yes" if latest_om > 0 else "否 / No"),
            ],
            "trend": display_trend(operating_margin, "pct"),
            "explanation": f"经营利润率从 {fmt_pct_short(first_om)} 到 {fmt_pct_short(latest_om)}；亏损收窄说明收入增长开始穿透固定成本，是真正修复的核心信号 / Operating margin moved from {fmt_pct_short(first_om)} to {fmt_pct_short(latest_om)}; narrowing losses show revenue is starting to cover fixed costs.",
        },
        {
            "key": "fcf_burn_compression",
            "name": "自由现金流烧钱收缩 / FCF burn compression",
            "weight": 0.15,
            "score": round(fcf_score),
            "raw": [
                raw_item("最新季度FCF / Latest quarterly FCF", fmt_money_short(latest_fcf)),
                raw_item("最新FCF率 / Latest FCF margin", fmt_pct_short(latest_fcf_margin)),
                raw_item("FCF率变化 / FCF margin change", fmt_pct_short(latest_fcf_margin - first_fcf_margin, True)),
            ],
            "trend": display_trend(fcf_points),
            "explanation": f"FCF 率从 {fmt_pct_short(first_fcf_margin)} 到 {fmt_pct_short(latest_fcf_margin)}；烧钱速度下降会延长生存时间，也降低再融资压力 / FCF margin moved from {fmt_pct_short(first_fcf_margin)} to {fmt_pct_short(latest_fcf_margin)}; lower cash burn extends runway and reduces financing pressure.",
        },
        {
            "key": "balance_sheet_runway",
            "name": "资产负债表续航 / Balance-sheet runway",
            "weight": 0.15,
            "score": round(runway_score),
            "raw": [
                raw_item("现金 / Cash", fmt_money_short(cash)),
                raw_item("季度烧钱 / Quarterly burn", fmt_money_short(quarterly_burn)),
                raw_item("估算续航 / Estimated runway", f"{runway_quarters:.1f}Q"),
            ],
            "trend": display_trend(metric_series(fin, "liabilities") or fcf_points),
            "explanation": f"按最新季度烧钱估算现金续航约 {runway_quarters:.1f} 个季度，债务/资产约 {fmt_pct_short(debt_to_assets)}；续航越长，修复等待时间越充裕 / Cash runway is about {runway_quarters:.1f} quarters and debt/assets is {fmt_pct_short(debt_to_assets)}; more runway gives the turnaround more time.",
        },
        {
            "key": "dilution_leverage_risk",
            "name": "稀释与杠杆风险 / Dilution & leverage risk",
            "weight": 0.10,
            "score": round(leverage_score),
            "raw": [
                raw_item("股数变化 / Share count change", fmt_pct_short(dilution, True)),
                raw_item("总债务 / Total debt", fmt_money_short(debt)),
                raw_item("债务/资产 / Debt/assets", fmt_pct_short(debt_to_assets)),
            ],
            "trend": display_trend(shares, "shares") if shares else display_trend(metric_series(fin, "liabilities") or fcf_points),
            "explanation": f"股数变化约 {fmt_pct_short(dilution, True)}，债务/资产约 {fmt_pct_short(debt_to_assets)}；修复股最怕持续融资稀释或债务压力吞掉股东回报 / Share count changed about {fmt_pct_short(dilution, True)} and debt/assets is {fmt_pct_short(debt_to_assets)}; dilution and leverage can absorb the recovery upside.",
        },
        {
            "key": "revenue_quality",
            "name": "收入质量 / Revenue quality",
            "weight": 0.10,
            "score": round(quality_score),
            "raw": [
                raw_item("毛利率 / Gross margin", fmt_pct_short(latest_gm)),
                raw_item("FCF率 / FCF margin", fmt_pct_short(latest_fcf_margin)),
                raw_item("收入波动区间 / Revenue volatility band", fmt_pct_short(volatility)),
            ],
            "trend": display_trend(fcf_margin_points, "pct"),
            "explanation": f"收入质量用毛利率、FCF率和营收波动共同判断；高增长但现金转换差，修复可信度会打折 / Revenue quality blends gross margin, FCF margin, and revenue volatility; growth with weak cash conversion deserves a lower score.",
        },
        {
            "key": "guidance_credibility",
            "name": "指引可信度 / Guidance credibility",
            "weight": 0.05,
            "score": round(guidance_score),
            "raw": [
                raw_item("最新财报 / Latest filing", fin.get("latest_report", {}).get("filed", "N/A")),
                raw_item("营收环比 / Revenue QoQ", fmt_pct_short(rev_qoq, True)),
                raw_item("利润率变化 / Margin change", fmt_pct_short(latest_om - first_om, True)),
            ],
            "trend": display_trend(revenue[-4:]),
            "explanation": "暂用实际财报趋势代理管理层兑现能力；后续接入 earnings call、Yahoo/Seeking Alpha 指引历史后，可以改成“指引 vs 实际”的命中率 / Actual filing trends are used as a proxy for delivery; once guidance history is connected, this can become guidance-vs-actual hit rate.",
        },
    ]
    overall = round(sum(item["score"] * item["weight"] for item in dimensions))
    label = (
        "高质量修复 / High-quality turnaround" if overall >= 75 else
        "早期修复但仍有风险 / Early recovery with risk" if overall >= 60 else
        "观察型修复 / Watchlist recovery" if overall >= 45 else
        "价值陷阱或财务困境风险 / Value trap or distress risk"
    )
    return {
        "score": overall,
        "label": label,
        "why_it_matters": "负PE或负FCF股票不能只看当前利润，要看需求、毛利、经营亏损、烧钱速度、续航和稀释是否连续改善 / For negative PE or negative FCF stocks, judge whether demand, margins, losses, cash burn, runway, and dilution are improving together.",
        "dimensions": dimensions,
    }


def attention_model(ticker: str, snapshot: dict, profile: dict, price_context: dict, x_social: dict | None = None, reddit_social: dict | None = None) -> dict:
    turnover = snapshot.get("turnover_rate", 0)
    volume = snapshot.get("volume", 0)
    base = profile.get("attention", 45)
    volume_ratio = snapshot.get("volume_ratio") or price_context.get("volume_ratio", 0)
    volume_trend = price_context.get("volume_trend", 0)
    momentum = max(
        abs(price_context.get("day_change") or 0),
        abs(price_context.get("week_change") or 0),
        abs(price_context.get("month_change") or 0),
    )
    liquidity = clamp(math.log10(max(volume, 1)) * 7 + turnover * 6, 0, 100)
    volume_heat = clamp(volume_ratio * 32 + volume_trend * 22, 0, 100)
    momentum_heat = clamp(momentum * 260, 0, 100)
    social = clamp(base, 0, 100)
    velocity = clamp(0.35 * volume_heat + 0.30 * momentum_heat + 0.20 * liquidity + 0.15 * social, 0, 100)
    x_score = x_social.get("score") if x_social and x_social.get("connected") else None
    reddit_score = reddit_social.get("score") if reddit_social and reddit_social.get("connected") else None
    social_component = max([value for value in (social, x_score, reddit_score) if value is not None])
    score = round(clamp(0.17 * social + 0.21 * liquidity + 0.25 * volume_heat + 0.17 * velocity + 0.20 * social_component, 0, 100))
    signals = [
        {"name": "Liquidity", "value": round(liquidity), "detail": "成交量、换手率和流动性基础分 / Volume, turnover, and liquidity base score."},
        {"name": "Volume ratio", "value": round(volume_heat), "detail": f"量比 / Volume ratio {volume_ratio:.2f}x；5日/20日成交量趋势 / 5D vs 20D volume trend {volume_trend:.2f}x。"},
        {"name": "Order imbalance", "value": round(clamp((snapshot.get("bid_ask_ratio", 0) + 100) / 2, 0, 100)), "detail": f"Futu 委比 / bid-ask imbalance {snapshot.get('bid_ask_ratio', 0):.1f}%。"},
        {"name": "Price/volume velocity", "value": round(velocity), "detail": "结合价格波动、量比、换手率和基础关注度 / Combines price move, volume ratio, turnover, and baseline attention."},
        {"name": "Social/news baseline", "value": round(social), "detail": "未覆盖平台仍用题材基线；Reddit 公开搜索会覆盖这部分 / Uncovered platforms use theme baseline; Reddit public search can override part of it."},
    ]
    if reddit_social and reddit_social.get("connected"):
        signals.insert(0, {
            "name": "Reddit public search",
            "value": reddit_social["score"],
            "detail": f"最近 7 天抓到 {reddit_social['posts']} 篇帖子、{reddit_social['comments']} 条评论，帖子分数约 {reddit_social['upvotes']} / Found {reddit_social['posts']} posts, {reddit_social['comments']} comments, and about {reddit_social['upvotes']} post score in the last 7 days.",
        })
    if x_social and x_social.get("connected"):
        signals.insert(0, {
            "name": "X recent search",
            "value": x_social["score"],
            "detail": f"最近 7 天抓到 {x_social['mentions']} 条相关帖，互动量约 {x_social['engagement']} / Found {x_social['mentions']} relevant posts and about {x_social['engagement']} engagement in the last 7 days.",
        })
    return {
        "score": score,
        "level": "Very high" if score >= 80 else "High" if score >= 65 else "Moderate" if score >= 45 else "Low",
        "signals": signals,
        "x_social": x_social or {},
        "reddit_social": reddit_social or {},
        "connectors": [
            {"name": "买卖盘 / Order book", "status": "planned", "needs": "Futu 订阅买卖盘用于委比/买卖盘失衡 / Futu order book subscription for bid-ask imbalance"},
            {"name": "Reddit", "status": "connected" if reddit_social and reddit_social.get("connected") else "public limited", "needs": "当前用公开JSON搜索；限流后可加OAuth / Public JSON search now; OAuth can be added if Reddit rate-limits"},
            {"name": "X", "status": "connected" if x_social and x_social.get("connected") else "needs key", "needs": "X_BEARER_TOKEN 用于 cashtag/recent search / Bearer token in X_BEARER_TOKEN for cashtag search"},
            {"name": "Google Trends", "status": "limited", "needs": "需要 Google Trends API alpha 权限 / Google Trends API alpha access"},
            {"name": "新闻情绪 / News sentiment", "status": "needs key", "needs": "需要新闻API监控情绪和负面新闻 / News provider API for sentiment and negative-news flags"},
        ],
    }


def fetch_x_attention(ticker: str) -> tuple[dict, list[str]]:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token:
        return {
            "connected": False,
            "score": None,
            "mentions": None,
            "engagement": None,
            "query": f"${ticker} OR {ticker} stock",
        }, ["X_BEARER_TOKEN not set; X social search is disabled."]
    query = f'("${ticker}" OR "${ticker} stock" OR "${ticker} earnings" OR "${ticker} shares" OR "${ticker} price" OR "${ticker} guidance" OR "${ticker} revenue" OR "${ticker} EPS" OR "${ticker} stock market" OR "${ticker} investing" OR "${ticker} trading" OR "${ticker} options" OR "${ticker} bullish" OR "${ticker} bearish" OR "${ticker} AI" OR "${ticker} chip" OR "${ticker} semiconductor" OR "${ticker} memory" OR "${ticker} cloud" OR "${ticker} tariff" OR "${ticker} China" OR "${ticker} Fed" OR "${ticker} rate" OR "${ticker} macro" OR "${ticker} lawsuit" OR "${ticker} SEC" OR "${ticker} insider" OR "${ticker} buyback" OR "${ticker} dividend" OR "${ticker} capex" OR "${ticker} margin" OR "${ticker} valuation" OR "${ticker} PE" OR "${ticker} PEG" OR "${ticker} DCF" OR "${ticker} analyst" OR "${ticker} upgrade" OR "${ticker} downgrade" OR "${ticker} target price" OR "${ticker} call" OR "${ticker} put" OR "${ticker} WallStreetBets" OR "${ticker} WSB" OR "${ticker} reddit" OR "${ticker} short squeeze" OR "${ticker} volume" OR "${ticker} breakout" OR "${ticker} momentum" OR "${ticker} news" OR "${ticker} results" OR "${ticker} quarter" OR "${ticker} Q1" OR "${ticker} Q2" OR "${ticker} Q3" OR "${ticker} Q4" OR "${ticker} FY" OR "${ticker} FCF" OR "${ticker} EBITDA" OR "${ticker} sales" OR "${ticker} demand" OR "${ticker} supply" OR "${ticker} inventory" OR "${ticker} cycle" OR "${ticker} recession" OR "${ticker} inflation" OR "${ticker} rates" OR "${ticker} hedge fund" OR "${ticker} 13F" OR "${ticker} CEO" OR "${ticker} CFO") lang:en -is:retweet'
    compact_query = f'(${ticker} OR "{ticker} stock" OR "{ticker} earnings" OR "{ticker} shares" OR "{ticker} options" OR "{ticker} news") lang:en -is:retweet'
    params = urllib.parse.urlencode({
        "query": compact_query,
        "max_results": 100,
        "tweet.fields": "created_at,public_metrics,lang",
    })
    url = f"https://api.x.com/2/tweets/search/recent?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "stock-valuation-site/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        tweets = data.get("data", []) or []
        engagement = 0
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {}) or {}
            engagement += safe_float(metrics.get("like_count")) + safe_float(metrics.get("retweet_count")) * 2 + safe_float(metrics.get("reply_count")) * 1.5 + safe_float(metrics.get("quote_count")) * 1.5
        mentions = len(tweets)
        score = clamp(mentions * 0.75 + math.log10(max(engagement, 1)) * 18, 0, 100)
        return {
            "connected": True,
            "score": round(score),
            "mentions": mentions,
            "engagement": round(engagement),
            "query": compact_query,
        }, ["X recent search connected."]
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")[:500]
        except Exception:
            detail = ""
        return {
            "connected": False,
            "score": None,
            "mentions": None,
            "engagement": None,
            "query": compact_query,
            "error": f"HTTP {exc.code}",
            "detail": detail,
        }, [f"X recent search unavailable: HTTP {exc.code}. {detail[:180]}"]
    except Exception as exc:
        return {
            "connected": False,
            "score": None,
            "mentions": None,
            "engagement": None,
            "query": compact_query,
            "error": exc.__class__.__name__,
        }, [f"X recent search unavailable: {exc.__class__.__name__}."]


def fetch_reddit_attention(ticker: str) -> tuple[dict, list[str]]:
    pattern = re.compile(rf"(?<![A-Z0-9])\$?{re.escape(ticker.upper())}(?![A-Z0-9])")
    posts = []
    errors = []
    successful_requests = 0
    browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

    def fetch_with_curl(url: str) -> dict | None:
        try:
            result = subprocess.run(
                [
                    "curl.exe",
                    "-L",
                    "-sS",
                    "-A",
                    browser_user_agent,
                    "-H",
                    "Accept: application/json,text/plain,*/*",
                    "--max-time",
                    "15",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None
            return json.loads(result.stdout)
        except Exception:
            return None

    for subreddit in REDDIT_SUBREDDITS:
        params = urllib.parse.urlencode({
            "q": ticker,
            "restrict_sr": 1,
            "sort": "new",
            "t": "week",
            "limit": 25,
        })
        url = f"https://www.reddit.com/r/{subreddit}/search.json?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": browser_user_agent,
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=7) as response:
                payload = json.loads(response.read().decode("utf-8"))
            successful_requests += 1
        except urllib.error.HTTPError as exc:
            payload = fetch_with_curl(url)
            if payload is None:
                errors.append(f"r/{subreddit} HTTP {exc.code}")
                continue
            successful_requests += 1
        except Exception as exc:
            payload = fetch_with_curl(url)
            if payload is None:
                errors.append(f"r/{subreddit} {exc.__class__.__name__}")
                continue
            successful_requests += 1

        for child in payload.get("data", {}).get("children", []) or []:
            item = child.get("data", {}) or {}
            title = str(item.get("title") or "")
            text = str(item.get("selftext") or "")
            haystack = f"{title}\n{text}".upper()
            if not pattern.search(haystack):
                continue
            created = safe_float(item.get("created_utc"))
            posts.append({
                "subreddit": item.get("subreddit_name_prefixed") or f"r/{subreddit}",
                "title": title[:180],
                "url": f"https://www.reddit.com{item.get('permalink', '')}",
                "score": round(safe_float(item.get("score"))),
                "comments": round(safe_float(item.get("num_comments"))),
                "upvote_ratio": safe_float(item.get("upvote_ratio")),
                "created_utc": created,
                "created": time.strftime("%Y-%m-%d", time.gmtime(created)) if created else "",
            })

    if successful_requests == 0:
        return {
            "connected": False,
            "score": None,
            "posts": None,
            "comments": None,
            "upvotes": None,
            "top_posts": [],
            "error": "; ".join(errors[:4]),
        }, [f"Reddit public search unavailable: {'; '.join(errors[:4]) or 'unknown error'}."]

    total_comments = sum(item["comments"] for item in posts)
    total_score = sum(max(item["score"], 0) for item in posts)
    avg_upvote_ratio = sum(item["upvote_ratio"] for item in posts) / len(posts) if posts else 0
    active_subreddits = len({item["subreddit"] for item in posts})
    heat = clamp(
        min(len(posts), 80) / 80 * 42
        + min(math.log10(total_comments + 1), 4) / 4 * 24
        + min(math.log10(total_score + 1), 4) / 4 * 20
        + min(active_subreddits, 8) / 8 * 10
        + avg_upvote_ratio * 4,
        0,
        100,
    )
    today = date.today()
    daily = []
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        key = day.isoformat()
        day_posts = [item for item in posts if item.get("created") == key]
        daily.append({
            "date": key,
            "posts": len(day_posts),
            "comments": sum(item["comments"] for item in day_posts),
            "upvotes": sum(max(item["score"], 0) for item in day_posts),
        })
    top_posts = sorted(posts, key=lambda item: item["score"] + item["comments"] * 2, reverse=True)[:5]

    return {
        "connected": True,
        "score": round(heat),
        "posts": len(posts),
        "comments": total_comments,
        "upvotes": total_score,
        "avg_upvote_ratio": avg_upvote_ratio,
        "daily": daily,
        "active_subreddits": active_subreddits,
        "top_posts": top_posts,
        "searched_subreddits": REDDIT_SUBREDDITS,
        "errors": errors[:4],
    }, [f"Reddit public search connected across {successful_requests}/{len(REDDIT_SUBREDDITS)} subreddits."]


def risk_model(snapshot: dict, fin: dict, metrics: dict, profile: dict, valuation: dict) -> dict:
    flags = []
    def add(severity: str, title: str, detail: str):
        flags.append({"severity": severity, "title": title, "detail": detail})

    if metrics["fcf_margin"] < 0:
        add("high", "自由现金流为负 / Free cash flow is negative", "现金流为负时，DCF 和 P/FCF 可信度下降，需关注融资和稀释风险 / When FCF is negative, DCF and P/FCF are less reliable; watch financing and dilution risk.")
    if metrics["debt_to_assets"] > 0.7:
        add("high", "资产负债杠杆偏高 / Balance sheet leverage is high", "负债占资产比例较高，利率上行或信用收缩时估值折扣应提高 / High liabilities-to-assets means valuation haircut should rise when rates or credit tighten.")
    if valuation["forward_pe"] > 45:
        add("medium", "Forward PE 需要强执行 / Forward PE requires strong execution", "Forward PE 偏高，必须依赖持续增长、预期上修和市场热度维持倍数 / High Forward PE needs growth, estimate revisions, and attention to sustain the multiple.")
    if "turnaround" in profile["traits"]:
        add("medium", "转型执行风险 / Turnaround execution risk", "转型/扭亏公司不能只看低 PE，需要看毛利率、capex、现金流和管理层执行 / For turnarounds, low PE is not enough; watch gross margin, capex, cash flow, and execution.")
    if "export_control" in profile["traits"] or "geopolitical" in profile["traits"]:
        add("medium", "地缘/出口管制暴露 / Geopolitical/export-control exposure", "地缘和出口管制会影响收入可见度、供应链和估值倍数 / Geopolitics and export controls can affect revenue visibility, supply chains, and valuation multiples.")
    if "tariff_sensitive" in profile["traits"] or "china_exposure" in profile["traits"]:
        add("medium", "关税和中国敞口 / Tariff and China exposure", "关税、供应链迁移和中美政策变化可能压缩毛利率 / Tariffs, supply-chain shifts, and US-China policy can compress margins.")
    for item in profile.get("risk", []):
        add("watch", f"{item.title()} / profile risk", "来自公司画像的预设风险标签，接入新闻/filing 后会升级为实时监控 / Preset profile risk tag; later upgraded with live news and filing monitoring.")
    if not flags:
        add("watch", "暂无重大模型红旗 / No major model red flags", "第一版模型未发现明显红旗，但仍需接入新闻、insider 和 13F 数据确认 / This first model sees no major red flag, but news, insider, and 13F data should confirm it.")

    penalty = sum({"high": 18, "medium": 10, "watch": 4}.get(f["severity"], 4) for f in flags)
    return {"score": round(clamp(100 - penalty, 0, 100)), "flags": flags[:8]}


def macro_exposure(profile: dict, macro: dict) -> dict:
    traits = set(profile["traits"])
    exposures = [
        {"name": "Rate sensitivity", "value": 85 if "rate_sensitive" in traits or "high_growth" in traits else 45},
        {"name": "Tariff sensitivity", "value": 80 if "tariff_sensitive" in traits or "china_exposure" in traits else 35},
        {"name": "Policy/fiscal catalyst", "value": 88 if "policy_sensitive" in traits or "fiscal_spending_sensitive" in traits else 40},
        {"name": "Geopolitical exposure", "value": 85 if "geopolitical" in traits or "export_control" in traits else 38},
        {"name": "Commodity sensitivity", "value": 86 if "commodity_sensitive" in traits else 25},
    ]
    wind = 50
    if "policy_sensitive" in traits:
        wind += 15
    if "rate_sensitive" in traits and "restrictive" in macro["regime"].lower():
        wind -= 10
    if "tariff_sensitive" in traits or "export_control" in traits:
        wind -= 8
    if "defensive" in traits:
        wind += 6
    return {
        "score": round(clamp(wind, 0, 100)),
        "regime": macro,
        "exposures": exposures,
        "interpretation": "顺风 / Tailwind" if wind >= 65 else "逆风 / Headwind" if wind <= 42 else "中性偏观察 / Neutral-watch",
    }


def build_summary(fin_score: dict, valuation: dict, attention: dict, risk: dict, macro: dict) -> dict:
    score = (
        fin_score["score"] * 0.25
        + valuation["score"] * 0.20
        + clamp(50 + valuation["expected_growth"] * 160, 0, 100) * 0.15
        + attention["score"] * 0.15
        + risk["score"] * 0.10
        + macro["score"] * 0.15
    )
    if score >= 75:
        label = "High quality / favorable setup"
    elif score >= 60:
        label = "Constructive, but watch the flags"
    elif score >= 45:
        label = "Mixed setup"
    else:
        label = "High-risk or unattractive setup"
    return {"score": round(score), "label": label}


def external_links(ticker: str, profile: dict) -> list[dict]:
    query = urllib.parse.quote(ticker)
    return [
        {"name": "Yahoo Finance", "url": f"https://finance.yahoo.com/quote/{query}/analysis", "use": "分析师预期、盈利趋势、估值摘要 / analyst estimates, earnings trend, valuation summary；公开接口常有 crumb 限制 / public endpoints often have crumb limits."},
        {"name": "Seeking Alpha", "url": f"https://seekingalpha.com/symbol/{query}/earnings/transcripts", "use": "电话会纪要和管理层指引 / earnings call transcripts and management guidance；部分内容需要订阅 / some content requires subscription."},
        {"name": "GuruFocus", "url": f"https://www.gurufocus.com/stock/{query}/summary", "use": "历史估值、质量评分、guru/insider 持仓 / historical valuation, quality scores, guru and insider ownership；通常需要套餐 / often paid."},
        {"name": "Investing.com", "url": f"https://www.investing.com/search/?q={query}", "use": "新闻、技术面、日历和市场数据 / news, technicals, calendar, and market data."},
        {"name": "公司IR / Company IR", "url": f"https://www.google.com/search?q={urllib.parse.quote(ticker + ' investor relations earnings presentation guidance')}", "use": "最权威来源：公司官网IR、业绩新闻稿、10-Q/10-K、演示材料 / most authoritative source: company IR, earnings releases, 10-Q/10-K, presentations."},
    ]


def analyze(raw_ticker: str) -> dict:
    ticker, code = normalize_ticker(raw_ticker)
    profile = get_profile(ticker)
    notes = []
    snapshot, futu_notes = get_futu_snapshot(code)
    notes.extend(futu_notes)
    if not snapshot or snapshot.get("price", 0) <= 0:
        yahoo_snapshot, yahoo_notes = get_yahoo_snapshot(ticker)
        notes.extend(yahoo_notes)
        if yahoo_snapshot and yahoo_snapshot.get("price", 0) > 0:
            snapshot = yahoo_snapshot
        else:
            snapshot = fallback_snapshot(ticker, profile)
            notes.append("Using deterministic snapshot fallback.")
    price_context, price_notes = get_futu_price_context(snapshot.get("code", code), snapshot.get("price", 0), snapshot.get("prev_close_price", 0))
    notes.extend(price_notes)
    if price_context.get("source") == "model fallback":
        yahoo_context, yahoo_context_notes = get_yahoo_price_context(ticker, snapshot.get("price", 0), snapshot.get("prev_close_price", 0))
        notes.extend(yahoo_context_notes)
        if yahoo_context:
            price_context = yahoo_context

    sec_fin, sec_notes = get_sec_financials(ticker)
    notes.extend(sec_notes)
    if not sec_fin or sec_fin.get("revenue", 0) <= 0:
        sec_fin = fallback_financials(ticker, snapshot, profile)
        notes.append("Using model fallback financials.")
    elif snapshot.get("eps", 0) > 0 and sec_fin.get("eps", 0) <= 0:
        sec_fin["eps"] = snapshot["eps"]
    notes.extend(enrich_with_yahoo_quarterly(ticker, sec_fin))
    notes.extend(apply_official_earnings_overlay(ticker, sec_fin))
    notes.extend(enrich_snapshot_with_financials(snapshot, sec_fin))

    macro, macro_notes = macro_regime()
    notes.extend(macro_notes)
    metrics = score_financials(sec_fin)
    sec_fin["metric_history"] = build_financial_metric_history(sec_fin, metrics)
    methods, valuation = valuation_methods(ticker, snapshot, sec_fin, profile, macro, metrics)
    dcf_lab = build_dcf_lab(ticker, snapshot, sec_fin, profile, macro, metrics)
    turnaround = build_turnaround_model(ticker, snapshot, sec_fin, profile, metrics)
    x_social, x_notes = fetch_x_attention(ticker)
    notes.extend(x_notes)
    reddit_social, reddit_notes = fetch_reddit_attention(ticker)
    notes.extend(reddit_notes)
    attention = attention_model(ticker, snapshot, profile, price_context, x_social, reddit_social)
    risks = risk_model(snapshot, sec_fin, metrics, profile, valuation)
    macro_view = macro_exposure(profile, macro)
    summary = build_summary(metrics, valuation, attention, risks, macro_view)

    return {
        "ticker": ticker,
        "code": snapshot.get("code", code),
        "name": snapshot.get("name") or ticker,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "profile": {
            "sector": profile["sector"],
            "industry": profile["industry"],
            "traits": profile["traits"],
            "size": format_size(snapshot.get("market_cap", 0)),
            "logo_url": f"https://images.financialmodelingprep.com/symbol/{ticker}.png",
            "logo_fallback_url": f"https://logo.clearbit.com/{LOGO_DOMAINS.get(ticker, ticker.lower() + '.com')}",
        },
        "snapshot": snapshot,
        "price_context": price_context,
        "financials": sec_fin,
        "metrics": metrics,
        "valuation": valuation,
        "dcf_lab": dcf_lab,
        "turnaround": turnaround,
        "methods": sorted(methods, key=lambda x: x["weight"], reverse=True),
        "attention": attention,
        "risk": risks,
        "macro": macro_view,
        "summary": summary,
        "external_links": external_links(ticker, profile),
        "data_notes": notes,
    }


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = urllib.parse.urlparse(path).path
        if clean == "/":
            clean = "/index.html"
        return str(PUBLIC / clean.lstrip("/"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/analyze":
            params = urllib.parse.parse_qs(parsed.query)
            ticker = params.get("ticker", ["INTC"])[0]
            try:
                payload = analyze(ticker)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return
        return super().do_GET()


if __name__ == "__main__":
    os.chdir(PUBLIC)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Stock valuation site running at http://127.0.0.1:{PORT}")
    server.serve_forever()
