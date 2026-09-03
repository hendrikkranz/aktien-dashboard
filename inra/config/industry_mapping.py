from pathlib import Path

import pandas as pd


# Zentrale Modellgruppen für die Branchenlogik von InRA.
#
# Die konkrete Yahoo-Branche wird einer Damodaran-Branche
# und anschließend einer dieser Modellgruppen zugeordnet.

INDUSTRY_MODEL_STANDARD = "standard"
INDUSTRY_MODEL_TECHNOLOGY = "technology"
INDUSTRY_MODEL_INSURANCE = "insurance"
INDUSTRY_MODEL_BANKING = "banking"
INDUSTRY_MODEL_FINANCIAL_SERVICES = "financial_services"
INDUSTRY_MODEL_REAL_ESTATE = "real_estate"
INDUSTRY_MODEL_UTILITIES = "utilities"

INDUSTRY_MODELS = {
    INDUSTRY_MODEL_STANDARD,
    INDUSTRY_MODEL_TECHNOLOGY,
    INDUSTRY_MODEL_INSURANCE,
    INDUSTRY_MODEL_BANKING,
    INDUSTRY_MODEL_FINANCIAL_SERVICES,
    INDUSTRY_MODEL_REAL_ESTATE,
    INDUSTRY_MODEL_UTILITIES,
}


def get_industry_model(sector: str, industry: str = "") -> str:
    if sector == "Technology":
        return INDUSTRY_MODEL_TECHNOLOGY

    if sector == "Utilities":
        return INDUSTRY_MODEL_UTILITIES

    if sector == "Real Estate":
        return INDUSTRY_MODEL_REAL_ESTATE

    if sector == "Financial Services":
        if industry.startswith("Insurance"):
            return INDUSTRY_MODEL_INSURANCE

        if industry.startswith("Banks"):
            return INDUSTRY_MODEL_BANKING

        return INDUSTRY_MODEL_FINANCIAL_SERVICES

    return INDUSTRY_MODEL_STANDARD


BASE_DIR = Path(__file__).resolve().parents[1]

BENCHMARK_PATH = BASE_DIR / "data" / "damodaran_benchmarks_mgnroc.csv"
ROE_BENCHMARK_PATH = BASE_DIR / "data" / "damodaran_benchmarks_roe.csv"


def get_industry_benchmark(damodaran_industry: str) -> dict:
    if not BENCHMARK_PATH.exists():
        return {}

    df = pd.read_csv(BENCHMARK_PATH)

    row = df.loc[
        df["Damodaran_Branche"] == damodaran_industry
    ]

    if row.empty:
        return {}

    return row.iloc[0].to_dict()

MAPPING_PATH = BASE_DIR / "data" / "industry_mapping.csv"

def get_industry_roe_benchmark(damodaran_industry: str) -> dict:
    if not ROE_BENCHMARK_PATH.exists():
        return {}

    df = pd.read_csv(ROE_BENCHMARK_PATH)

    row = df.loc[
        df["Damodaran_Branche"] == damodaran_industry
    ]

    if row.empty:
        return {}

    return row.iloc[0].to_dict()

def get_benchmark_for_yahoo_industry(
    sector: str,
    industry: str,
) -> dict:
    if not MAPPING_PATH.exists():
        return {}

    mapping = pd.read_csv(MAPPING_PATH)

    row = mapping.loc[
        (mapping["Yahoo_Sektor"] == sector)
        & (mapping["Yahoo_Branche"] == industry)
    ]

    if row.empty:
        return {}

    damodaran_industry = row.iloc[0]["Damodaran_Branche"]

    if pd.isna(damodaran_industry):
        return {}

    return get_industry_benchmark(damodaran_industry)

def get_roe_benchmark_for_yahoo_industry(
    sector: str,
    industry: str,
) -> dict:
    if not MAPPING_PATH.exists():
        return {}

    mapping = pd.read_csv(MAPPING_PATH)

    row = mapping.loc[
        (mapping["Yahoo_Sektor"] == sector)
        & (mapping["Yahoo_Branche"] == industry)
    ]

    if row.empty:
        return {}

    damodaran_industry = row.iloc[0]["Damodaran_Branche"]

    if pd.isna(damodaran_industry):
        return {}

    return get_industry_roe_benchmark(damodaran_industry)

def get_quality_benchmarks_for_yahoo_industry(
    sector: str,
    industry: str,
) -> dict:
    return {
        "mgnroc": get_benchmark_for_yahoo_industry(
            sector,
            industry,
        ),
        "roe": get_roe_benchmark_for_yahoo_industry(
            sector,
            industry,
        ),
    }