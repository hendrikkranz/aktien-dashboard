"""
Datenebene für Immobilien-Quality V0.1.

Dieser Baustein ist bewusst von der regulären Aktienanalyse getrennt.

Ziel:
Unternehmensspezifische Immobilien-KPIs werden auf ein gemeinsames,
transparentes Datenmodell abgebildet, ohne fehlende Kennzahlen
künstlich aus Yahoo-Finanzdaten zu konstruieren.
"""

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class RealEstateQualityData:
    ticker: str
    company_name: Optional[str] = None
    real_estate_type: Optional[str] = None

    # Operative Ertragskraft
    earnings_metric: Optional[str] = None
    earnings_per_share: Optional[float] = None
    earnings_period: Optional[str] = None

    # Wachstum
    earnings_growth_pct: Optional[float] = None

    # Portfolio
    portfolio_growth_metric: Optional[str] = None
    portfolio_growth_pct: Optional[float] = None

    stability_metric: Optional[str] = None
    occupancy_pct: Optional[float] = None
    vacancy_pct: Optional[float] = None
    churn_pct: Optional[float] = None

    # Finanzierung
    ltv_pct: Optional[float] = None
    net_debt_ebitda: Optional[float] = None
    coverage_ratio: Optional[float] = None
    coverage_metric: Optional[str] = None

    # Später für Immobilien-Kaufchance
    epra_nta_per_share: Optional[float] = None
    nav_per_share: Optional[float] = None

    # Transparenz
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_period: Optional[str] = None

    def to_dict(self):
        return asdict(self)


REAL_ESTATE_TEST_UNIVERSE = {
    "VNA.DE": {
        "company_name": "Vonovia",
        "real_estate_type": "Residential",
    },
    "PLD": {
        "company_name": "Prologis",
        "real_estate_type": "Industrial / Logistics REIT",
    },
    "O": {
        "company_name": "Realty Income",
        "real_estate_type": "Net Lease REIT",
    },
    "SPG": {
        "company_name": "Simon Property Group",
        "real_estate_type": "Retail REIT",
    },
    "AMT": {
        "company_name": "American Tower",
        "real_estate_type": "Infrastructure / Tower REIT",
    },
    "TEG.DE": {
        "company_name": "TAG Immobilien",
        "real_estate_type": "Residential",
    },
    "PHP.L": {
        "company_name": "Primary Health Properties",
        "real_estate_type": "Healthcare REIT",
    },
}


def create_real_estate_quality_data(ticker):
    config = REAL_ESTATE_TEST_UNIVERSE.get(ticker)

    if config is None:
        raise ValueError(
            f"Kein Immobilien-Datenprofil für {ticker} vorhanden."
        )

    return RealEstateQualityData(
        ticker=ticker,
        company_name=config["company_name"],
        real_estate_type=config["real_estate_type"],
    )


def validate_real_estate_quality_data(data):
    """
    Einfache Plausibilitätsprüfung.

    Noch keine fachliche Score-Berechnung.
    """
    errors = []

    percentage_fields = {
        "earnings_growth_pct": data.earnings_growth_pct,
        "portfolio_growth_pct": data.portfolio_growth_pct,
        "occupancy_pct": data.occupancy_pct,
        "vacancy_pct": data.vacancy_pct,
        "churn_pct": data.churn_pct,
        "ltv_pct": data.ltv_pct,
    }

    for field, value in percentage_fields.items():
        if value is None:
            continue

        if field in {
            "occupancy_pct",
            "vacancy_pct",
            "churn_pct",
            "ltv_pct",
        } and not 0 <= value <= 100:
            errors.append(
                f"{field}: Prozentwert außerhalb 0–100: {value}"
            )

    if (
        data.occupancy_pct is not None
        and data.vacancy_pct is not None
    ):
        total = data.occupancy_pct + data.vacancy_pct

        if not 99.0 <= total <= 101.0:
            errors.append(
                "occupancy_pct + vacancy_pct ist nicht ungefähr 100."
            )

    if (
        data.net_debt_ebitda is not None
        and data.net_debt_ebitda < 0
    ):
        errors.append(
            "net_debt_ebitda darf nicht negativ sein."
        )

    if (
        data.coverage_ratio is not None
        and data.coverage_ratio < 0
    ):
        errors.append(
            "coverage_ratio darf nicht negativ sein."
        )

    return errors


PRIMARY_HEALTH_PROPERTIES_H1_2026_URL = (
    "https://www.phpgroup.co.uk/media/3n2bsnps/"
    "php-jun26-interim-presentation.pdf"
)


VONOVIA_H1_2026_URL = (
    "https://report.vonovia.com/2026/q2/en/key-figures"
)


def load_vonovia_h1_2026():
    """
    Vonovia H1 2026.

    V0.1 verwendet ausschließlich offiziell von Vonovia
    veröffentlichte Immobilien-KPIs.

    Adjusted EBT je Aktie:
        Bereinigte operative Ertragskennzahl von Vonovia.
        Sie ersetzt hier bewusst das klassische EPS/KGV-Denken.

    Organisches Mietwachstum:
        Wachstum der Bestandsmieten ohne Verzerrung durch
        Portfoliozukäufe und -verkäufe.

    Leerstandsquote:
        Anteil leerstehender Wohnungen am eigenen Bestand.
        Niedrige Werte sprechen für stabile Nachfrage.

    LTV:
        Finanzverschuldung relativ zum Immobilienvermögen.
        Zentrale Verschuldungskennzahl für Immobilienunternehmen.

    ICR:
        Zinsdeckungsgrad. Zeigt, wie oft das operative Ergebnis
        die Finanzierungskosten deckt.

    EPRA NTA je Aktie:
        Bereinigter Netto-Substanzwert des Immobilienvermögens
        je Aktie. Dient später zur Berechnung des Abschlags oder
        Aufschlags des Aktienkurses auf den Substanzwert.
    """
    return RealEstateQualityData(
        ticker="VNA.DE",
        company_name="Vonovia",
        real_estate_type="Residential",

        earnings_metric="Adjusted EBT je Aktie",
        earnings_per_share=1.13,
        earnings_period="H1 2026",
        earnings_growth_pct=-5.4,

        portfolio_growth_metric="Organisches Mietwachstum",
        portfolio_growth_pct=3.6,

        stability_metric="Leerstandsquote",
        vacancy_pct=2.3,
        occupancy_pct=97.7,

        ltv_pct=46.0,
        net_debt_ebitda=14.0,
        coverage_ratio=3.6,
        coverage_metric="ICR",

        epra_nta_per_share=46.22,

        source_name="Vonovia H1 2026 Interim Financial Report",
        source_url=VONOVIA_H1_2026_URL,
        source_period="30.06.2026",
    )


PROLOGIS_Q2_2026_URL = (
    "https://ir.prologis.com/news-events/press-releases/detail/"
    "1044/prologis-reports-second-quarter-2026-results"
)

REALTY_INCOME_Q2_2026_URL = (
    "https://www.realtyincome.com/investors/quarterly-and-annual-results"
)

SIMON_Q2_2026_URL = (
    "https://investors.simon.com/news-releases/news-release-details/"
    "simonr-reports-second-quarter-2026-results-and-increases"
)

AMERICAN_TOWER_Q2_2026_URL = (
    "https://www.sec.gov/Archives/edgar/data/1053507/"
    "000105350726000131/pressreleaseq22026.htm"
)

TAG_H1_2026_URL = (
    "https://www.tag-ag.com/news/pressemitteilungen/meldung/"
    "stark-wachsende-ergebnisse-im-ersten-halbjahr-2026-"
    "ffo-i-fuer-2026-am-oberen-ende-der-prognosespanne-"
    "erwartet-465420316"
)


def load_prologis_q2_2026():
    return RealEstateQualityData(
        ticker="PLD",
        company_name="Prologis",
        real_estate_type="Industrial / Logistics REIT",

        earnings_metric="Core FFO je Aktie",
        earnings_per_share=1.63,
        earnings_period="Q2 2026",
        earnings_growth_pct=11.6,

        portfolio_growth_metric="Cash Same Store NOI",
        portfolio_growth_pct=8.5,

        stability_metric="Period-End Occupancy",
        occupancy_pct=95.5,
        vacancy_pct=4.5,

        net_debt_ebitda=4.7,

        source_name="Prologis Q2 2026 Results",
        source_url=PROLOGIS_Q2_2026_URL,
        source_period="30.06.2026",
    )


def load_realty_income_q2_2026():
    return RealEstateQualityData(
        ticker="O",
        company_name="Realty Income",
        real_estate_type="Net Lease REIT",

        earnings_metric="AFFO je Aktie",
        earnings_per_share=1.09,
        earnings_period="Q2 2026",
        earnings_growth_pct=3.8,

        portfolio_growth_metric="Same Store Rent Growth",
        portfolio_growth_pct=1.0,

        stability_metric="Occupancy",
        occupancy_pct=98.8,
        vacancy_pct=1.2,

        net_debt_ebitda=5.4,

        source_name="Realty Income Q2 2026 Supplemental",
        source_url=REALTY_INCOME_Q2_2026_URL,
        source_period="30.06.2026",
    )


def load_simon_q2_2026():
    return RealEstateQualityData(
        ticker="SPG",
        company_name="Simon Property Group",
        real_estate_type="Retail REIT",

        earnings_metric="Real Estate FFO je Aktie",
        earnings_per_share=3.29,
        earnings_period="Q2 2026",
        earnings_growth_pct=7.9,

        portfolio_growth_metric="Portfolio NOI",
        portfolio_growth_pct=8.3,

        stability_metric="Occupancy",
        occupancy_pct=96.0,
        vacancy_pct=4.0,

        # SPG veröffentlicht für Q2 2026 keine für unser Modell
        # direkt vergleichbare LTV- oder Debt/EBITDA-Kennzahl.
        # Die konzernweite Fixed Charge Coverage wird dagegen
        # offiziell ausgewiesen und ist als Coverage-Kennzahl geeignet.
        ltv_pct=None,
        net_debt_ebitda=None,
        coverage_ratio=4.7,
        coverage_metric="Fixed Charge Coverage",

        source_name="Simon Property Group Q2 2026 Results",
        source_url=SIMON_Q2_2026_URL,
        source_period="30.06.2026",
    )


def load_american_tower_q2_2026():
    return RealEstateQualityData(
        ticker="AMT",
        company_name="American Tower",
        real_estate_type="Infrastructure / Tower REIT",

        earnings_metric="AFFO je Aktie",
        earnings_per_share=2.71,
        earnings_period="Q2 2026",
        earnings_growth_pct=4.2,

        portfolio_growth_metric="Organic Tenant Billings Growth",
        portfolio_growth_pct=1.7,

        # Für Tower-REITs ist klassische Immobilien-Occupancy
        # keine sinnvoll vergleichbare Kernkennzahl.
        stability_metric=None,
        occupancy_pct=None,
        vacancy_pct=None,

        # Konzernweite Leverage-Kennzahl. Eine vergleichbare
        # konzernweite Coverage-Kennzahl wurde nicht übernommen;
        # der berichtete DSCR bezieht sich auf eine Securitization.
        net_debt_ebitda=4.9,
        coverage_ratio=None,
        coverage_metric=None,

        source_name="American Tower Q2 2026 Results",
        source_url=AMERICAN_TOWER_Q2_2026_URL,
        source_period="30.06.2026",
    )


def load_tag_h1_2026():
    # TAG besitzt wesentliche Wohnungsportfolios in Deutschland und Polen.
    # Portfolio-Wachstum und Leerstand werden deshalb nach dem jeweiligen
    # Immobilienwert (GAV) zum 30.06.2026 gewichtet:
    # Deutschland EUR 5.506,9 Mio. / Polen EUR 2.271,0 Mio.
    germany_weight = 5506.9 / 7777.9
    poland_weight = 2271.0 / 7777.9

    portfolio_growth_pct = (
        3.0 * germany_weight
        + 2.4 * poland_weight
    )

    vacancy_pct = (
        3.8 * germany_weight
        + 2.1 * poland_weight
    )

    return RealEstateQualityData(
        ticker="TEG.DE",
        company_name="TAG Immobilien",
        real_estate_type="Residential",

        earnings_metric="FFO I",
        earnings_per_share=0.53,
        earnings_period="H1 2026",
        earnings_growth_pct=9.0,

        portfolio_growth_metric=(
            "Like-for-like Mietwachstum, GAV-gewichtet"
        ),
        portfolio_growth_pct=portfolio_growth_pct,

        stability_metric=(
            "Wohnungsleerstand, GAV-gewichtet"
        ),
        vacancy_pct=vacancy_pct,
        occupancy_pct=100.0 - vacancy_pct,

        ltv_pct=45.4,
        coverage_ratio=None,
        coverage_metric=None,

        epra_nta_per_share=21.38,

        source_name="TAG Immobilien H1 2026",
        source_url=TAG_H1_2026_URL,
        source_period="30.06.2026",
    )


def load_primary_health_properties_h1_2026():
    """
    Primary Health Properties H1 2026.

    Verwendet ausschließlich offiziell von PHP veröffentlichte
    Immobilien- und Finanzierungskennzahlen.

    Adjusted EPS Growth:
        Operative Ertragsentwicklung auf Basis des Adjusted EPS.

    LFL Rental Growth:
        Annualisiertes Like-for-like-Mietwachstum des Portfolios.

    Occupancy:
        Vermietungsquote des Immobilienportfolios.

    Finanzierung:
        LTV und Interest Cover bilden Verschuldung und
        Schuldentragfähigkeit getrennt ab.
    """
    return RealEstateQualityData(
        ticker="PHP.L",
        company_name="Primary Health Properties",
        real_estate_type="Healthcare REIT",

        earnings_metric="Adjusted EPS",
        earnings_growth_pct=9.0,
        earnings_period="H1 2026",

        portfolio_growth_metric=(
            "Like-for-like Rental Growth, annualisiert"
        ),
        portfolio_growth_pct=3.2,

        stability_metric="Occupancy",
        occupancy_pct=99.0,
        vacancy_pct=1.0,

        ltv_pct=57.0,
        coverage_ratio=2.6,
        coverage_metric="Interest Cover Ratio",

        epra_nta_per_share=99.0,

        source_name=(
            "Primary Health Properties H1 2026 "
            "Interim Presentation"
        ),
        source_url=PRIMARY_HEALTH_PROPERTIES_H1_2026_URL,
        source_period="30.06.2026",
    )


REAL_ESTATE_DATA_LOADERS = {
    "VNA.DE": load_vonovia_h1_2026,
    "PLD": load_prologis_q2_2026,
    "O": load_realty_income_q2_2026,
    "SPG": load_simon_q2_2026,
    "AMT": load_american_tower_q2_2026,
    "TEG.DE": load_tag_h1_2026,
    "PHP.L": load_primary_health_properties_h1_2026,
}


def load_real_estate_quality_data(ticker):
    loader = REAL_ESTATE_DATA_LOADERS.get(ticker)

    if loader is None:
        raise ValueError(
            f"Kein Immobilien-Datenloader für {ticker} vorhanden."
        )

    data = loader()
    errors = validate_real_estate_quality_data(data)

    if errors:
        raise ValueError(
            f"Ungültige Immobilien-KPIs für {ticker}: "
            + "; ".join(errors)
        )

    return data
