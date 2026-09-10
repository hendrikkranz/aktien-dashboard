import json
import re
import socket
from typing import Optional

from google import genai
from google.genai import types


QUALITATIVE_FACTORS = (
    "Burggraben / Wettbewerbsposition",
    "Kapitalallokation",
    "Management & Governance",
    "Bilanzierungs-/Ergebnisqualität",
    "Strukturelle Geschäftsrisiken",
)

QUALITATIVE_RATING_SCALE = {
    5: "Außergewöhnlich stark",
    4: "Stark",
    3: "Solide / neutral",
    2: "Schwach / erhöhtes Risiko",
    1: "Sehr schwach / kritisch",
}


QUALITATIVE_FACTOR_GUIDANCE = {
    "Burggraben / Wettbewerbsposition": (
        "Bewerte die Dauerhaftigkeit struktureller Wettbewerbsvorteile. "
        "Berücksichtige insbesondere Netzwerkeffekte, Wechselkosten, "
        "Markenstärke, technologische oder regulatorische Eintrittsbarrieren "
        "und Kosten- oder Skalenvorteile. Marktführerschaft allein ist kein "
        "Burggraben. Noch nicht etablierte Zukunftschancen oder Optionalität "
        "werden nicht als bestehender Wettbewerbsvorteil gewertet."
    ),
    "Kapitalallokation": (
        "Bewerte die Qualität langfristiger Entscheidungen über den Einsatz "
        "des Unternehmenskapitals. Berücksichtige Reinvestitionen, "
        "Akquisitionen, Desinvestitionen, Aktienrückkäufe und Finanzierung. "
        "Die Höhe der Dividende gehört nicht in diese Bewertung. "
        "Die aktuelle Verschuldung wird quantitativ in der Bilanzbewertung "
        "erfasst und soll hier nicht nochmals bewertet werden."
    ),
    "Management & Governance": (
        "Bewerte Integrität, strategische und operative Qualität des "
        "Managements, Interessenangleichung, Transparenz sowie Governance-, "
        "Kontroll- und Risikostrukturen. Die Entwicklung des Aktienkurses "
        "ist kein Bewertungskriterium. Gründerführung ist kein automatischer "
        "Vorteil und besondere Stimmrechtsstrukturen sind kein automatischer "
        "Nachteil."
    ),
    "Bilanzierungs-/Ergebnisqualität": (
        "Bewerte Zuverlässigkeit, Transparenz und wirtschaftliche "
        "Aussagekraft von Ergebnis-, Cashflow- und Vermögensdarstellung. "
        "Einmaleffekte führen nicht automatisch zu einer schlechten "
        "Bewertung. Wiederkehrende große Bereinigungen oder schwer "
        "nachvollziehbare Ergebnisdarstellungen können die Bewertung senken. "
        "Die finanzielle Stabilität der Bilanz wird separat quantitativ "
        "bewertet."
    ),
    "Strukturelle Geschäftsrisiken": (
        "Bewerte dauerhafte externe Abhängigkeiten und Risiken des "
        "Geschäftsmodells, insbesondere regulatorische, politische und "
        "geografische Risiken sowie Kunden-, Lieferanten- oder "
        "Ressourcenkonzentrationen. Normale Konjunkturzyklen, die aktuelle "
        "Makrolage, Verschuldung und Managementqualität gehören nicht in "
        "diesen Faktor. Neue Einzelereignisse werden zunächst separat als "
        "Event Impact behandelt."
    ),
}


QUALITATIVE_INDUSTRY_GUIDANCE = {
    "Banks": (
        "Bei Banken besonders berücksichtigen: Qualität und Stabilität des "
        "Einlagen- und Kreditgeschäfts, Kreditrisiken, Kapitaldisziplin, "
        "regulatorische Anforderungen, Risikokultur sowie Transparenz bei "
        "Risikovorsorge und Bewertung von Finanzinstrumenten. Klassische "
        "Industrie-Kennzahlen zur Verschuldung sind hier nur eingeschränkt "
        "aussagekräftig."
    ),
    "Insurance": (
        "Bei Versicherern besonders berücksichtigen: Qualität des "
        "Underwritings, Preissetzungsmacht, Diversifikation, "
        "Kapitaldisziplin, Reservierungsqualität, Rückversicherungsrisiken "
        "und regulatorische Kapitalanforderungen. Ergebnisvolatilität durch "
        "Kapitalmarkt- oder Schadensereignisse ist im Geschäftsmodellkontext "
        "zu beurteilen."
    ),
    "Real Estate": (
        "Bei REITs und Immobilienunternehmen besonders berücksichtigen: "
        "Qualität und Lage des Immobilienbestands, Mietermix, "
        "Vermietungsquote, Laufzeiten der Mietverträge, Zugang zu Kapital, "
        "Bewertungsannahmen für Immobilien sowie strukturelle Veränderungen "
        "der jeweiligen Immobiliennutzung. REIT-spezifische Ergebnisgrößen "
        "wie FFO oder AFFO sind aussagekräftiger als der reine Jahresgewinn."
    ),
    "Pharma/Biotech": (
        "Bei Pharma- und Biotechunternehmen besonders berücksichtigen: "
        "Patent- und Exklusivitätsdauer, Qualität und Diversifikation der "
        "Pipeline, Abhängigkeit von einzelnen Wirkstoffen, regulatorische "
        "Zulassungsrisiken, klinische Entwicklungsrisiken sowie Qualität "
        "von Forschung, Entwicklung und Akquisitionen. Noch unbewiesene "
        "Pipeline-Chancen dürfen nicht wie bestehende Wettbewerbsvorteile "
        "behandelt werden."
    ),
}


def build_qualitative_research_prompt(
    ticker: str,
    company_name: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
) -> str:
    industry_context = get_qualitative_industry_context(
        sector,
        industry,
        ticker,
    )

    factor_text = "\n\n".join(
        f"{index}. {factor}\n{QUALITATIVE_FACTOR_GUIDANCE[factor]}"
        for index, factor in enumerate(
            QUALITATIVE_FACTORS,
            start=1,
        )
    )

    context_text = ""

    if industry_context is not None:
        context_text = (
            "\n\nBranchenspezifischer Kontext:\n"
            + QUALITATIVE_INDUSTRY_GUIDANCE[
                industry_context
            ]
        )

    scale_text = "\n".join(
        f"{score}: {description}"
        for score, description in sorted(
            QUALITATIVE_RATING_SCALE.items(),
            reverse=True,
        )
    )

    return (
        f"Unternehmen: {company_name} ({ticker})\n"
        f"Sektor: {sector or 'Nicht angegeben'}\n"
        f"Branche: {industry or 'Nicht angegeben'}\n"
        f"{context_text}\n\n"
        "Nutze für diese Aufgabe zwingend die bereitgestellte Google-Suche "
        "und führe eine aktuelle Web-Recherche zum Unternehmen durch. "
        "Bewerte die Faktoren nicht ausschließlich aus deinem vorhandenen "
        "Modellwissen. Bevorzuge Primärquellen wie Geschäftsberichte, "
        "Investor-Relations-Unterlagen, regulatorische Veröffentlichungen "
        "und offizielle Unternehmensmeldungen. Ergänzend können etablierte "
        "Finanzmedien und Ratingagenturen verwendet werden.\n\n"
        "Bewerte anschließend die folgenden fünf qualitativen Faktoren "
        "auf einer Skala von 1 bis 5.\n\n"
        f"Bewertungsskala:\n{scale_text}\n\n"
        f"{factor_text}\n\n"
        "Gib das Ergebnis ausschließlich als JSON-Array zurück.\n"
        "Für jeden der fünf Faktoren muss genau ein Objekt enthalten sein mit:\n"
        '- "Faktor": exakter Name des Faktors\n'
        '- "Bewertung": Ganzzahl von 1 bis 5 oder null\n'
        '- "Status": "Bewertbar" oder "Nicht bewertbar"\n'
        '- "Begründung": kurze nachvollziehbare Begründung\n'
        '- Nur beim Faktor "Burggraben / Wettbewerbsposition": '
        '"Hauptkonkurrenten": Liste mit 1 bis 3 tatsächlich relevanten '
        'Hauptkonkurrenten. Bei allen anderen Faktoren dieses Feld weglassen.\n\n'
        "Keine Felder für Quellen oder Quellenstand ausgeben. "
        "Die tatsächlichen Quellen werden technisch aus den "
        "Google-Grounding-Metadaten übernommen.\n\n"
        "Quantitative Kennzahlen sollen nicht erneut bewertet werden, "
        "wenn sie bereits Bestandteil der quantitativen Quality sind."
    )


def build_empty_qualitative_research(
    ticker: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
) -> dict:
    industry_context = get_qualitative_industry_context(
        sector,
        industry,
        ticker,
    )

    return {
        "Ticker": ticker,
        "Branchenkontext": industry_context,
        "Faktoren": {
            factor: {
                "Bewertung": None,
                "Status": "Nicht bewertet",
                "Quelle": None,
                "Stand": None,
                "Begründung": None,
            }
            for factor in QUALITATIVE_FACTORS
        },
    }


def get_qualitative_industry_context(
    sector: Optional[str],
    industry: Optional[str],
    ticker: Optional[str] = None,
) -> Optional[str]:
    ticker_text = (ticker or "").upper()
    sector_text = (sector or "").lower()
    industry_text = (industry or "").lower()

    # Konzern-/Geschäftsmodell-Ausnahmen
    if ticker_text in {"BRK-B", "BN", "BAYN.DE", "MRK.DE"}:
        return None

    if ticker_text == "LGEN.L":
        return "Insurance"

    if "bank" in industry_text:
        return "Banks"

    if "insurance" in industry_text:
        return "Insurance"

    if (
        sector_text == "real estate"
        or "reit" in industry_text
        or "real estate" in industry_text
    ):
        return "Real Estate"

    if (
        sector_text == "healthcare"
        and (
            "drug manufacturer" in industry_text
            or "biotech" in industry_text
            or "biotechnology" in industry_text
        )
    ):
        return "Pharma/Biotech"

    return None


def _parse_json_response(response_text: str) -> list:
    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError(
            "Gemini-Antwort enthält kein JSON-Array."
        )

    return data


def _extract_grounding_sources(response) -> list:
    candidate = response.candidates[0]
    metadata = candidate.grounding_metadata

    if metadata is None:
        return []

    sources = []
    seen = set()

    for chunk in metadata.grounding_chunks or []:
        web = getattr(chunk, "web", None)

        if web is None:
            continue

        title = getattr(web, "title", None)
        uri = getattr(web, "uri", None)

        if not uri or uri in seen:
            continue

        seen.add(uri)

        sources.append(
            {
                "Titel": title,
                "URL": uri,
            }
        )

    return sources


def _extract_search_queries(response) -> list:
    candidate = response.candidates[0]
    metadata = candidate.grounding_metadata

    if metadata is None:
        return []

    return list(
        getattr(
            metadata,
            "web_search_queries",
            None,
        )
        or []
    )


def research_qualitative_quality_with_gemini(
    api_key: str,
    ticker: str,
    company_name: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    model: str = "gemini-3.6-flash",
) -> dict:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=90000,
            retryOptions=types.HttpRetryOptions(
                attempts=1,
            ),
        ),
    )

    prompt = build_qualitative_research_prompt(
        ticker=ticker,
        company_name=company_name,
        sector=sector,
        industry=industry,
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
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ],
            ),
        )
    finally:
        socket.getaddrinfo = original_getaddrinfo

    raw_factors = _parse_json_response(
        response.text
    )

    factors = {}

    for item in raw_factors:
        factor = item.get("Faktor")

        if factor not in QUALITATIVE_FACTORS:
            continue

        rating = item.get("Bewertung")
        status = item.get(
            "Status",
            "Nicht bewertbar",
        )
        reason = item.get("Begründung")
        competitors = item.get("Hauptkonkurrenten")

        if rating not in {1, 2, 3, 4, 5}:
            rating = None
            status = "Nicht bewertbar"

        if factor != "Burggraben / Wettbewerbsposition":
            competitors = None

        factors[factor] = {
            "Bewertung": rating,
            "Status": status,
            "Begründung": reason,
            "Hauptkonkurrenten": competitors,
        }

    for factor in QUALITATIVE_FACTORS:
        if factor not in factors:
            factors[factor] = {
                "Bewertung": None,
                "Status": "Nicht bewertbar",
                "Begründung": None,
            }

    return {
        "Ticker": ticker,
        "Branchenkontext": get_qualitative_industry_context(
            sector,
            industry,
            ticker,
        ),
        "Faktoren": factors,
        "Quellen": _extract_grounding_sources(
            response
        ),
        "Suchanfragen": _extract_search_queries(
            response
        ),
    }
