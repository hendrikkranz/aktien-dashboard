from config.scoring import OPPORTUNITY_WEIGHTS
from config.industry_mapping import get_pe_benchmark_for_yahoo_industry
from modules.chart_score import calculate_technical_condition_v3_score


def calculate_real_estate_nav_score(data: dict):
    """
    Bewertet Immobilienunternehmen anhand des Börsenkurses relativ
    zum EPRA NTA bzw. NAV je Aktie.

    Rückgabe:
        (points, price_to_nav, nav_metric, nav_per_share)

    Maximal 30 Punkte. Ein Abschlag auf den Nettovermögenswert wird
    positiv, eine Prämie negativ bewertet.
    """
    real_estate_data = data.get("Real Estate Quality Data") or {}

    price = data.get("Kurs")

    epra_nta = real_estate_data.get("epra_nta_per_share")
    nav = real_estate_data.get("nav_per_share")

    if epra_nta is not None:
        nav_per_share = epra_nta
        nav_metric = "EPRA NTA"
    elif nav is not None:
        nav_per_share = nav
        nav_metric = "NAV"
    else:
        return None, None, None, None

    if (
        price is None
        or price <= 0
        or nav_per_share <= 0
    ):
        return None, None, nav_metric, nav_per_share

    price_to_nav = price / nav_per_share

    thresholds = [
        (0.70, 30),
        (0.80, 27),
        (0.90, 24),
        (1.00, 20),
        (1.10, 15),
        (1.20, 9),
        (1.35, 4),
    ]

    points = 0

    for maximum, score in thresholds:
        if price_to_nav <= maximum:
            points = score
            break

    return (
        points,
        price_to_nav,
        nav_metric,
        nav_per_share,
    )


def calculate_opportunity_breakdown(data: dict) -> list:
    breakdown = []

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")

    analyst_points = None

    if analyst_upside is not None:
        if analyst_upside < 0:
            analyst_points = 0
        elif analyst_upside < 5:
            analyst_points = 3
        elif analyst_upside < 10:
            analyst_points = 7
        elif analyst_upside < 15:
            analyst_points = 12
        elif analyst_upside < 20:
            analyst_points = 17
        elif analyst_upside < 30:
            analyst_points = 21
        else:
            analyst_points = OPPORTUNITY_WEIGHTS[
                "analystenpotenzial"
            ]

    # Kaufchance V3:
    # Analystenpotenzial bisher max. 25 -> künftig max. 15.
    if analyst_points is not None:
        analyst_points = round(
            analyst_points
            / OPPORTUNITY_WEIGHTS["analystenpotenzial"]
            * 15,
            1,
        )

    breakdown.append(
        {
            "Kriterium": "Analystenpotenzial",
            "Punkte": analyst_points,
            "Maximum": 15,
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

    pe_current_year = data.get("KGV GJ +0")
    pe_next_year = data.get("KGV GJ +1")

    current_year_points = calculate_forward_pe_core_score(
        pe_current_year,
        valuation_class,
    )
    next_year_points = calculate_forward_pe_core_score(
        pe_next_year,
        valuation_class,
    )

    if (
        current_year_points is not None
        and next_year_points is not None
    ):
        core_points = round(
            0.60 * current_year_points
            + 0.40 * next_year_points,
            1,
        )
    elif current_year_points is not None:
        core_points = current_year_points
    elif next_year_points is not None:
        core_points = next_year_points
    else:
        core_points = calculate_forward_pe_core_score(
            forward_pe,
            valuation_class,
        )

    if (
        pe_current_year is not None
        and pe_next_year is not None
    ):
        relative_forward_pe = (
            0.60 * pe_current_year
            + 0.40 * pe_next_year
        )
    elif pe_current_year is not None:
        relative_forward_pe = pe_current_year
    elif pe_next_year is not None:
        relative_forward_pe = pe_next_year
    else:
        relative_forward_pe = forward_pe

    relative_points = None
    regime_points = None

    if valuation_class != "SONDERFALL":
        relative_points = calculate_pe_industry_relative_score(
            relative_forward_pe,
            industry_forward_pe,
        )
        regime_points = calculate_pe_industry_regime_score(
            industry_forward_pe,
            historical_median,
        )

    if data.get("Real Estate Quality") is not None:
        (
            nav_points,
            price_to_nav,
            nav_metric,
            nav_per_share,
        ) = calculate_real_estate_nav_score(data)

        nav_discount_pct = None

        if price_to_nav is not None:
            nav_discount_pct = (
                1.0 - price_to_nav
            ) * 100

        breakdown.append(
            {
                "Kriterium": "NTA/NAV-Bewertung",
                "Punkte": nav_points,
                "Maximum": 30,
                "NTA/NAV-Kennzahl": nav_metric,
                "NTA/NAV je Aktie": nav_per_share,
                "Kurs/NTA-NAV": price_to_nav,
                "Abschlag/Prämie %": nav_discount_pct,
            }
        )
    else:
        breakdown.append(
            {
                "Kriterium": "Forward KGV",
                "Punkte": core_points,
                "Maximum": 24,
                "Bewertungsklasse": valuation_class,
                "Geschäftsjahr +0": data.get("Geschäftsjahr +0"),
                "KGV GJ +0": pe_current_year,
                "EPS GJ +0": data.get("EPS GJ +0"),
                "Analysten GJ +0": data.get(
                    "Analysten EPS GJ +0"
                ),
                "Punkte GJ +0": current_year_points,
                "Gewicht GJ +0": 0.60,
                "Geschäftsjahr +1": data.get("Geschäftsjahr +1"),
                "KGV GJ +1": pe_next_year,
                "EPS GJ +1": data.get("EPS GJ +1"),
                "Analysten GJ +1": data.get(
                    "Analysten EPS GJ +1"
                ),
                "Punkte GJ +1": next_year_points,
                "Gewicht GJ +1": 0.40,
            }
        )

        breakdown.append(
            {
                "Kriterium": "KGV vs. Branche",
                "Punkte": relative_points,
                "Maximum": 3,
                "Aktien KGV gewichtet": relative_forward_pe,
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


def calculate_entry_setup_score(data: dict):
    """Bewertet das aktuelle Entry Setup mit maximal 30 Punkten."""
    setup = data.get("Entry Setup")

    points = {
        "Lower Channel Bounce – bestätigt": 30.0,
        "Pullback Recovery – bestätigt": 28.5,
        "Median Support – bestätigt": 27.0,
        "Median Reclaim – bestätigt": 25.5,
        "30W Support/Reclaim – bestätigt": 25.5,
        "Breakout – bestätigt": 24.0,
        "Lower Channel Bounce": 22.5,
        "Median Reclaim": 21.0,
        "Widerstands-Anlauf – positiv": 19.5,
        "Untere Kanalhälfte – unbestätigt": 18.0,
        "Median Test – unbestätigt": 16.5,
        "Neutral": 15.0,
        "Median Reclaim – vorsichtig": 13.5,
        "Obere Kanalzone": 12.0,
        "Lower Channel Recovery – vorsichtig": 10.5,
        "Median Reclaim – schwach": 9.0,
        "Untere Kanalhälfte – schwach": 9.0,
        "Seitwärtstrend – kein Entry Setup": 9.0,
        "Median Test – schwach": 7.5,
        "Breakout – unbestätigt": 7.5,
        "Widerstands-Anlauf – unbestätigt": 7.5,
        "Widerstands-Anlauf – schwach": 6.0,
        "Kein belastbares Entry Setup": 6.0,
        "Tiefe Korrektur – Stabilisierung abwarten": 4.5,
        "Breakout – fragil": 4.5,
        "Abwärtstrend – kein Entry Setup": 3.0,
        "Support Breakdown": 0.0,
    }

    if setup in points:
        return points[setup]

    # Echter Datenmangel wird neutral behandelt.
    if setup in (None, "Nicht bewertbar"):
        return 15.0

    # Neue/unbekannte Setup-Klassen dürfen nicht still
    # als neutral in die Kaufchance eingehen.
    return None


def calculate_opportunity_v3_blocks(data: dict) -> dict:
    """Zentrale V3-Blöcke für Score, UI und Coverage."""
    fundamental_breakdown = calculate_opportunity_breakdown(data)

    fundamental_points = sum(
        item["Punkte"]
        for item in fundamental_breakdown
        if item["Punkte"] is not None
    )
    fundamental_available = sum(
        item["Maximum"]
        for item in fundamental_breakdown
        if item["Punkte"] is not None
    )

    technical_score_35 = calculate_technical_condition_v3_score(data)

    if technical_score_35 is None:
        technical_points = 12.5
        technical_available = 0
        technical_neutral = True
    else:
        technical_points = technical_score_35 / 35 * 25
        technical_available = 25
        technical_neutral = False

    entry_points = calculate_entry_setup_score(data)
    entry_setup = data.get("Entry Setup")

    if entry_points is None:
        entry_available = 0
        entry_neutral = False
    elif entry_setup in (None, "Nicht bewertbar"):
        entry_available = 0
        entry_neutral = True
    else:
        entry_available = 30
        entry_neutral = False

    return {
        "fundamental_points": fundamental_points,
        "fundamental_available": fundamental_available,
        "fundamental_maximum": 45,
        "technical_points": technical_points,
        "technical_available": technical_available,
        "technical_maximum": 25,
        "technical_neutral": technical_neutral,
        "entry_points": entry_points,
        "entry_available": entry_available,
        "entry_maximum": 30,
        "entry_neutral": entry_neutral,
        "entry_setup": entry_setup,
        "available_maximum": (
            fundamental_available
            + technical_available
            + entry_available
        ),
    }


def calculate_opportunity_score(data: dict):
    """Kaufchance V3: 45 fundamental + 25 Technik + 30 Entry."""
    blocks = calculate_opportunity_v3_blocks(data)

    if blocks["entry_points"] is None:
        return None

    score = (
        blocks["fundamental_points"]
        + blocks["technical_points"]
        + blocks["entry_points"]
    )

    return min(round(score), 100)


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
