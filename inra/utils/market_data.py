import yfinance as yf


def load_company_snapshot(ticker: str) -> dict:
    info = yf.Ticker(ticker).get_info()

    dividend_yield = info.get("dividendYield")

    if dividend_yield is not None:
        dividend_yield *= 100

    return {
        "Ticker": ticker,
        "Name": info.get("longName") or info.get("shortName") or ticker,
        "Kurs": info.get("currentPrice") or info.get("regularMarketPrice"),
        "Währung": info.get("currency"),
        "Dividendenrendite": dividend_yield,
        "KGV": info.get("trailingPE"),
        "Forward KGV": info.get("forwardPE"),
    }