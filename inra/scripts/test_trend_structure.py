import yfinance as yf

from inra.modules.trend_structure import (
    analyze_trend_structure,
    calculate_long_term_trend_score,
)


TEST_TICKERS = [
    "MSFT",
    "SONY",
    "MCO",
    "BASFY",
    "BFSA.F",
    "NESN.SW",
]


for ticker in TEST_TICKERS:
    ticker_obj = yf.Ticker(ticker)

    history_5y = ticker_obj.history(
        period="5y",
        interval="1wk",
        auto_adjust=True,
    )

    history_2y = ticker_obj.history(
        period="2y",
        interval="1wk",
        auto_adjust=True,
    )

    primary = analyze_trend_structure(
        history_5y,
        periods_per_year=52,
    )

    history = yf.Ticker(ticker).history(
        period="5y",
        interval="1mo",
        auto_adjust=True,
    )

    print(f"Monate: {len(history)}")
    print(f"Start : {history.index[0]}")
    print(f"Ende  : {history.index[-1]}")

    primary_score, primary_explanation = (
    calculate_long_term_trend_score(primary)
    )

    secondary = analyze_trend_structure(
        history_2y,
        periods_per_year=52,
    )

    print()
    print("=" * 60)
    print(ticker)
    print("=" * 60)

    print("\nPRIMÄR – 5 Jahre")
    print(f"score: {primary_score}")
    print(f"explanation: {primary_explanation}")
    for key, value in primary.items():
        print(f"{key}: {value}")

    print("\nSEKUNDÄR – 2 Jahre")
    for key, value in secondary.items():
        print(f"{key}: {value}")