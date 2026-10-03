import json
import re
import socket
from typing import Optional

from google import genai
from google.genai import types


def _parse_json_object(text: str) -> dict:
    cleaned = (text or "").strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Gemini-Antwort enthält kein JSON-Objekt."
        )

    return json.loads(cleaned[start:end + 1])


def create_company_portrait_with_gemini(
    api_key: str,
    company_name: str,
    business_summary: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    model: str = "gemini-3.6-flash",
) -> dict:
    if not business_summary:
        raise ValueError(
            "Keine Unternehmensbeschreibung verfügbar."
        )

    prompt = f"""
Du erstellst ein sehr kompaktes Unternehmensporträt für
eine deutschsprachige Aktienanalyse.

Unternehmen:
{company_name}

Sektor:
{sector or "nicht angegeben"}

Branche:
{industry or "nicht angegeben"}

Quelltext:
{business_summary}

Aufgabe:

1. Erkläre in 2 bis maximal 3 kurzen deutschen Sätzen,
   was das Unternehmen macht und womit es hauptsächlich
   Geld verdient.

2. Nenne genau 3 zentrale wirtschaftliche Geschäftsfelder,
   sofern der Quelltext drei sinnvoll unterscheidbare Felder
   hergibt. Jeder Begriff soll möglichst kurz sein.

Regeln:
- Verwende ausschließlich Informationen aus dem Quelltext.
- Die Geschäftsfelder müssen auf Deutsch formuliert sein.
- Englische Segmentnamen nicht einfach übernehmen, sondern
  ihren wirtschaftlichen Inhalt knapp auf Deutsch benennen.
- Wähle Geschäftsfelder auf vergleichbarem Abstraktionsniveau.
- Bevorzuge tragende Geschäftsbereiche gegenüber einzelnen
  Produkten, Marken oder Produktvarianten.
- Einzelne Produkte nur nennen, wenn sie selbst einen
  wesentlichen eigenständigen Geschäftsbereich darstellen.
- Firmennamen und etablierte Produkt- oder Markennamen dürfen
  in der Kurzbeschreibung unverändert bleiben.
- Keine Bewertung des Unternehmens.
- Keine Anlageempfehlung.
- Keine erfundenen Fakten.
- Keine allgemeinen Marketingformulierungen.
- Schreibe verständliches, präzises Deutsch.
- Antworte ausschließlich als gültiges JSON-Objekt.

Exaktes Format:

{{
  "Kurzbeschreibung": "...",
  "Kerngeschaeft": [
    "...",
    "...",
    "..."
  ]
}}
""".strip()

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=90000,
            retryOptions=types.HttpRetryOptions(
                attempts=1,
            ),
        ),
    )

    original_getaddrinfo = socket.getaddrinfo

    def ipv4_only(*args, **kwargs):
        results = original_getaddrinfo(*args, **kwargs)
        return [
            item
            for item in results
            if item[0] == socket.AF_INET
        ]

    socket.getaddrinfo = ipv4_only

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
            ),
        )
    finally:
        socket.getaddrinfo = original_getaddrinfo

    result = _parse_json_object(response.text)

    description = str(
        result.get("Kurzbeschreibung") or ""
    ).strip()

    core_business = result.get("Kerngeschaeft") or []

    if not isinstance(core_business, list):
        core_business = []

    core_business = [
        str(item).strip()
        for item in core_business
        if str(item).strip()
    ][:3]

    if not description:
        raise ValueError(
            "Gemini hat keine Kurzbeschreibung geliefert."
        )

    usage = getattr(
        response,
        "usage_metadata",
        None,
    )

    return {
        "Kurzbeschreibung": description,
        "Kerngeschaeft": core_business,
        "Usage": {
            "Prompt Tokens": getattr(
                usage,
                "prompt_token_count",
                None,
            ),
            "Output Tokens": getattr(
                usage,
                "candidates_token_count",
                None,
            ),
            "Thinking Tokens": getattr(
                usage,
                "thoughts_token_count",
                None,
            ),
            "Total Tokens": getattr(
                usage,
                "total_token_count",
                None,
            ),
        },
    }


from datetime import date
from pathlib import Path

import pandas as pd


COMPANY_PORTRAIT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "company_portraits.csv"
)

COMPANY_PORTRAIT_COLUMNS = [
    "Ticker",
    "Kurzbeschreibung",
    "Kerngeschaeft_1",
    "Kerngeschaeft_2",
    "Kerngeschaeft_3",
    "Aktualisiert",
]


def load_company_portraits() -> pd.DataFrame:
    if not COMPANY_PORTRAIT_PATH.exists():
        return pd.DataFrame(
            columns=COMPANY_PORTRAIT_COLUMNS
        )

    portraits = pd.read_csv(
        COMPANY_PORTRAIT_PATH
    )

    for column in COMPANY_PORTRAIT_COLUMNS:
        if column not in portraits.columns:
            portraits[column] = None

    return portraits[COMPANY_PORTRAIT_COLUMNS]


def get_company_portrait(ticker: str):
    portraits = load_company_portraits()

    if portraits.empty:
        return None

    ticker_normalized = str(ticker).strip().upper()

    match = portraits[
        portraits["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
        == ticker_normalized
    ]

    if match.empty:
        return None

    row = match.iloc[-1]

    core_business = []

    for column in (
        "Kerngeschaeft_1",
        "Kerngeschaeft_2",
        "Kerngeschaeft_3",
    ):
        value = row.get(column)

        if pd.notna(value) and str(value).strip():
            core_business.append(str(value).strip())

    return {
        "Ticker": ticker_normalized,
        "Kurzbeschreibung": (
            str(row["Kurzbeschreibung"]).strip()
            if pd.notna(row["Kurzbeschreibung"])
            else ""
        ),
        "Kerngeschaeft": core_business,
        "Aktualisiert": (
            str(row["Aktualisiert"]).strip()
            if pd.notna(row["Aktualisiert"])
            else None
        ),
    }


def save_company_portrait(
    ticker: str,
    portrait: dict,
) -> None:
    portraits = load_company_portraits()

    ticker_normalized = str(ticker).strip().upper()

    core_business = (
        portrait.get("Kerngeschaeft") or []
    )[:3]

    row = {
        "Ticker": ticker_normalized,
        "Kurzbeschreibung": portrait.get(
            "Kurzbeschreibung",
            "",
        ),
        "Kerngeschaeft_1": (
            core_business[0]
            if len(core_business) > 0
            else None
        ),
        "Kerngeschaeft_2": (
            core_business[1]
            if len(core_business) > 1
            else None
        ),
        "Kerngeschaeft_3": (
            core_business[2]
            if len(core_business) > 2
            else None
        ),
        "Aktualisiert": date.today().isoformat(),
    }

    if not portraits.empty:
        portraits = portraits[
            portraits["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
            != ticker_normalized
        ]

    portraits = pd.concat(
        [
            portraits,
            pd.DataFrame([row]),
        ],
        ignore_index=True,
    )

    COMPANY_PORTRAIT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    portraits.to_csv(
        COMPANY_PORTRAIT_PATH,
        index=False,
    )
