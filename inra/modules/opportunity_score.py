from config.scoring import OPPORTUNITY_WEIGHTS
from config.industry_mapping import get_pe_benchmark_for_yahoo_industry
from modules.chart_score import calculate_chart_score


def calculate_opportunity_breakdown(data: dict) -> list:
    breakdown = []

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")

    analyst_points = None

    if analyst_upside is not None:
        analyst_points = 0

        if analyst_upside >= 20:
            analyst_points = OPPORTUNITY_WEIGHTS[
                "analystenpotenzial"
            ]
        elif analyst_upside >= 10:
            analyst_points = round(
                OPPORTUNITY_WEIGHTS["analystenpotenzial"]
                * 0.625
            )

    breakdown.append(
        {
            "Kriterium": "Analystenpotenzial",
            "Punkte": analyst_points,
            "Maximum": OPPORTUNITY_WEIGHTS[
                "analystenpotenzial"
            ],
        }
    )

    valuation_class = get_pe_valuation_class(data)

    pe_benchmark = get_pe_benchmark_for_yahoo_industry(
        data.get("Sektor") or "",
        data.get("Branche") or "",
    )

    industry_forward_pe = pe_benchmark.get(
        "current_forward_pe"
    )
    historical_median = pe_benchmark.get(
        "historical_forward_pe_median"
    )

    core_points = calculate_forward_pe_core_score(
        forward_pe,
        valuation_class,
    )

    relative_points = None
    regime_points = None

    if valuation_class != "SONDERFALL":
        relative_points = calculate_pe_industry_relative_score(
            forward_pe,
            industry_forward_pe,
        )
        regime_points = calculate_pe_industry_regime_score(
            industry_forward_pe,
            historical_median,
        )

    breakdown.append(
        {
            "Kriterium": "Forward KGV",
            "Punkte": core_points,
            "Maximum": 24,
            "Bewertungsklasse": valuation_class,
        }
    )

    breakdown.append(
        {
            "Kriterium": "KGV vs. Branche",
            "Punkte": relative_points,
            "Maximum": 3,
            "Branchen KGV": industry_forward_pe,
            "Damodaran Branche": pe_benchmark.get(
                "damodaran_industry"
            ),
        }
    )

    breakdown.append(
        {
            "Kriterium": "Branchenbewertung historisch",
            "Punkte": regime_points,
            "Maximum": 3,
            "Branchen KGV": industry_forward_pe,
            "Historischer Median": historical_median,
            "Historische Jahre": pe_benchmark.get(
                "historical_years"
            ),
        }
    )

    return breakdown


def calculate_opportunity_score(data: dict) -> int:
    breakdown = calculate_opportunity_breakdown(data)

    score = sum(
        item["Punkte"]
        for item in breakdown
        if item["Punkte"] is not None
    )

    score += calculate_chart_score(data)

    return min(score, 100)

LOW_PE_INDUSTRIES = {
    "Banks - Diversified",
    "Banks - Regional",
    "Insurance - Diversified",
    "Insurance - Reinsurance",
    "Auto Manufacturers",
    "Oil & Gas Integrated",
    "Telecom Services",
}

GROWTH_PE_INDUSTRIES = {
    "Software - Application",
    "Software - Infrastructure",
    "Semiconductors",
    "Semiconductor Equipment & Materials",
    "Internet Content & Information",
    "Internet Retail",
}


def get_pe_valuation_class(data: dict) -> str:
    sector = data.get("Sektor") or ""
    industry = data.get("Branche") or ""
    ticker = (data.get("Ticker") or "").upper().strip()

    if ticker == "BRK-B":
        return "SONDERFALL"

    if sector == "Real Estate":
        return "SONDERFALL"

    if industry in LOW_PE_INDUSTRIES:
        return "NIEDRIG"

    if industry in GROWTH_PE_INDUSTRIES:
        return "WACHSTUM"

    return "STANDARD"


def calculate_forward_pe_core_score(
    forward_pe,
    valuation_class: str,
):
    tables = {
        "NIEDRIG": [
            (8, 24),
            (11, 20),
            (14, 17),
            (17, 12),
            (21, 7),
            (26, 2),
        ],
        "STANDARD": [
            (12, 24),
            (16, 20),
            (20, 17),
            (24, 12),
            (29, 7),
            (35, 2),
        ],
        "WACHSTUM": [
            (15, 24),
            (20, 20),
            (25, 17),
            (30, 12),
            (38, 7),
            (50, 2),
        ],
    }

    if (
        forward_pe is None
        or forward_pe <= 0
        or valuation_class == "SONDERFALL"
    ):
        return None

    for limit, points in tables[valuation_class]:
        if forward_pe <= limit:
            return points

    return 0


def calculate_pe_industry_relative_score(
    forward_pe,
    industry_forward_pe,
):
    if (
        forward_pe is None
        or industry_forward_pe is None
        or forward_pe <= 0
        or industry_forward_pe <= 0
    ):
        return None

    difference = (
        forward_pe / industry_forward_pe - 1
    ) * 100

    if difference <= -30:
        return 3
    if difference <= -15:
        return 2
    if difference <= 15:
        return 1

    return 0


def calculate_pe_industry_regime_score(
    industry_forward_pe,
    historical_median,
):
    if (
        industry_forward_pe is None
        or historical_median is None
        or industry_forward_pe <= 0
        or historical_median <= 0
    ):
        return None

    difference = (
        industry_forward_pe / historical_median - 1
    ) * 100

    if difference <= -30:
        return 3
    if difference <= -15:
        return 2
    if difference <= 30:
        return 1

    return 0
