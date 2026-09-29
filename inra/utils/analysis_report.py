"""
Datenaufbereitung für den InRA-Analyse-Report.

Der Report besitzt keine eigene Bewertungslogik.
Er verwendet ausschließlich bereits berechnete InRA-Ergebnisse.
"""

from components.investment_decision import get_investment_decision
from modules.opportunity_score import calculate_opportunity_v3_blocks
from utils.current_intelligence import get_current_intelligence
from utils.market_data import load_price_history


def build_analysis_report_data(data: dict) -> dict:
    """
    Erstellt die zentrale Datenstruktur für den maximal
    zweiseitigen InRA-Analyse-Report.

    Erwartet das finale Analyse-data nach Anwendung von
    Current Intelligence / Event Impact.
    """
    ticker = data.get("Ticker")

    current_intelligence = (
        get_current_intelligence(ticker)
        if ticker
        else None
    ) or {}

    investment_decision = get_investment_decision(data)
    opportunity_blocks = calculate_opportunity_v3_blocks(data)

    price_history = (
        load_price_history(ticker, period="1y")
        if ticker
        else None
    )

    price_history_data = []

    if price_history is not None and not price_history.empty:
        price_history_data = [
            {
                "date": row.Datum.strftime("%Y-%m-%d"),
                "close": float(row.Schlusskurs),
            }
            for row in price_history.itertuples(index=False)
        ]

    return {
        "company": {
            "name": data.get("Name"),
            "ticker": ticker,
            "exchange": data.get("Börse"),
            "currency": data.get("Währung"),
            "country": data.get("Land"),
            "sector": data.get("Sektor"),
            "industry": data.get("Branche"),
            "price": data.get("Kurs"),
            "market_cap": data.get("Marktkapitalisierung"),
            "dividend_yield": data.get("Dividendenrendite"),
        },
        "price_history": price_history_data,
        "investment_decision": {
            "title": investment_decision.get("title"),
            "text": investment_decision.get("text"),
            "score": investment_decision.get(
                "investment_score"
            ),
            "icon": investment_decision.get("icon"),
        },
        "inra_summary": (
            current_intelligence.get("InRA_Fazit") or {}
        ),
        "scores": {
            "quality": data.get("Unternehmensqualität"),
            "opportunity": data.get("Kaufchance"),
            "dividend": data.get("Dividendenstrategie Score"),
        },
        "quality": {
            "quantitative": data.get("Quantitative Quality"),
            "qualitative": data.get("Qualitative Quality"),
            "breakdown": data.get("Quality Breakdown") or {},
        },
        "opportunity": {
            "breakdown": data.get("Opportunity Breakdown") or {},
            "blocks": opportunity_blocks,
            "entry_setup": data.get("Entry Setup"),
            "entry_setup_explanation": data.get(
                "Entry Setup Erklärung"
            ),
            "momentum_3m": data.get("Momentum 3M"),
            "momentum_6m": data.get("Momentum 6M"),
            "momentum_12m": data.get("Momentum 12M"),
            "rsi_14": data.get("RSI 14"),
            "distance_52w_high": data.get("Abstand 52W Hoch"),
        },
        "dividend": {
            "status": data.get("Dividendenstrategie Status"),
            "score": data.get("Dividendenstrategie Score"),
            "maximum": 15,
            "raw_score": data.get(
                "Dividendenstrategie Score vor Begrenzung"
            ),
            "yield": data.get("Dividendenrendite"),
            "yield_points": data.get(
                "Dividendenrendite Punkte"
            ),
            "payout_ratio": data.get("Ausschüttungsquote"),
            "payout_points": data.get(
                "Ausschüttungsquote Punkte"
            ),
            "growth_3y": data.get("Dividendenwachstum 3J"),
            "growth_points": data.get(
                "Dividendenwachstum Punkte"
            ),
            "continuity_years": data.get(
                "Dividendenkontinuität Jahre"
            ),
            "continuity_points": data.get(
                "Dividendenkontinuität Punkte"
            ),
            "allocation_points": data.get(
                "Kapitalallokation Punkte"
            ),
        },
        "valuation": {
            "pe": data.get("KGV"),
            "forward_pe": data.get("Forward KGV"),
            "analyst_target": data.get("Analystenziel"),
            "analyst_upside": data.get("Analystenpotenzial"),
        },
        "current_intelligence": current_intelligence,
    }
