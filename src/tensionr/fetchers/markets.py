"""Market data via one batched yfinance download."""

import logging
import warnings
from typing import Any

from tensionr.config import TICKERS

logger = logging.getLogger(__name__)


def fetch_market_data() -> list[dict[str, Any]]:
    logger.info("fetching market data...")
    market_intel: list[dict[str, Any]] = []
    try:
        import yfinance as yf

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data = yf.download(
                list(TICKERS.values()),
                period="5d",
                group_by="ticker",
                progress=False,
                threads=True,
            )
        if data is None or data.empty:
            logger.warning("yfinance returned no data")
            return []

        for name, symbol in TICKERS.items():
            try:
                closes = data[symbol]["Close"].dropna()
            except KeyError:
                logger.warning("ticker %s missing from batch download", symbol)
                continue
            if len(closes) < 2:
                continue
            prev = float(closes.iloc[-2])
            curr = float(closes.iloc[-1])
            change = ((curr - prev) / prev) * 100
            market_intel.append(
                {"symbol": name, "price": round(curr, 2), "change": round(change, 2)}
            )
    except Exception as e:
        logger.warning("market data degraded: %s", e)
    return market_intel
