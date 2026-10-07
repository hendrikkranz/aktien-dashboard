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
        'Hauptkonkurrenten. Bei allen anderen Faktoren dieses Feld weglassen.\n'
        '- Nur beim Faktor "Bilanzierungs-/Ergebnisqualität": recherchiere '
        'zusätzlich für das jüngste abgeschlossene Geschäftsjahr ein direkt '
        'vergleichbares Paar aus verwässertem GAAP-EPS und vom Unternehmen '
        'ausgewiesenem bereinigtem bzw. Non-GAAP-EPS. Beide Werte müssen '
        'denselben Berichtszeitraum und dieselbe Aktienbasis betreffen. '
        'Bevorzuge dafür Geschäftsbericht, Earnings Release oder '
        'Investor-Relations-Unterlagen des Unternehmens. Wenn kein '
        'belastbares direkt vergleichbares Paar verfügbar ist, verwende '
        'für beide Werte null. Gib dafür zusätzlich aus:\n'
        '  - "GAAP EPS": Zahl oder null\n'
        '  - "Adjusted EPS": Zahl oder null\n'
        '  - "Bereinigungsursache": kurze Beschreibung der wesentlichen '
        'wiederkehrenden Bereinigungen, insbesondere SBC, '
        'akquisitionsbedingte Abschreibungen oder Restrukturierungen; '
        'null, wenn nicht belastbar bestimmbar.\n'
        'Die Bereinigungsquote NICHT selbst berechnen und kein Feld '
        '"Bereinigungsquote" ausgeben.\n\n'
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

    # Falls Gemini trotz Vorgabe Begleittext ausgibt,
    # nur das eigentliche JSON-Array verwenden.
    array_start = text.find("[")
    array_end = text.rfind("]")

    if (
        array_start != -1
        and array_end != -1
        and array_end > array_start
    ):
        text = text[array_start:array_end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # Häufiger Gemini-Formatfehler:
        # überflüssiges Komma unmittelbar vor } oder ].
        repaired_text = re.sub(
            r",\s*([}\]])",
            r"\1",
            text,
        )

        try:
            data = json.loads(repaired_text)
        except json.JSONDecodeError:
            raise ValueError(
                "Gemini-Antwort enthält kein gültiges JSON. "
                f"Fehler bei Zeile {exc.lineno}, "
                f"Spalte {exc.colno}."
            ) from exc

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

        gaap_eps = None
        adjusted_eps = None
        adjustment_ratio = None
        adjustment_reason = None

        if factor == "Bilanzierungs-/Ergebnisqualität":
            gaap_eps = item.get("GAAP EPS")
            adjusted_eps = item.get("Adjusted EPS")
            adjustment_reason = item.get(
                "Bereinigungsursache"
            )

            try:
                gaap_eps = float(gaap_eps)
                adjusted_eps = float(adjusted_eps)

                if adjusted_eps > 0 and gaap_eps >= 0:
                    adjustment_ratio = (
                        (adjusted_eps - gaap_eps)
                        / adjusted_eps
                        * 100
                    )
                else:
                    gaap_eps = None
                    adjusted_eps = None
                    adjustment_ratio = None
            except (TypeError, ValueError):
                gaap_eps = None
                adjusted_eps = None
                adjustment_ratio = None

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
            "GAAP EPS": gaap_eps,
            "Adjusted EPS": adjusted_eps,
            "Bereinigungsquote": (
                round(adjustment_ratio, 1)
                if adjustment_ratio is not None
                else None
            ),
            "Bereinigungsursache": adjustment_reason,
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


SPECIAL_QUANT_DIMENSIONS = (
    "Ertragskraft",
    "Wertentwicklung / wirtschaftliche Substanz",
    "Finanzielle Stabilität",
)

SPECIAL_QUANT_RATINGS = (
    "Stark",
    "Solide",
    "Schwach",
    "Nicht belastbar bewertbar",
)


def build_special_quantitative_research_prompt(
    ticker: str,
    company_name: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
) -> str:
    return (
        f"Unternehmen: {company_name} ({ticker})\n"
        f"Sektor: {sector or 'Nicht angegeben'}\n"
        f"Branche: {industry or 'Nicht angegeben'}\n\n"

        "Das standardisierte quantitative InRA-Quality-Modell ist für "
        "dieses Unternehmen aufgrund seiner diversifizierten Holding- bzw. "
        "Konzernstruktur nicht ausreichend aussagekräftig.\n\n"

        "Erstelle deshalb eine ergänzende kennzahlenbasierte Analyse. "
        "Verwende für jedes Unternehmen dieselben drei Bewertungsdimensionen, "
        "wähle innerhalb dieser Dimensionen aber nur solche finanziellen "
        "Kennzahlen aus, die für das konkrete Geschäftsmodell wirtschaftlich "
        "aussagekräftig und aus belastbaren Quellen verfügbar sind.\n\n"

        "Die Analyse darf KEINE individuelle zusätzliche Bewertungsdimension "
        "erfinden und KEIN eigenes Sondermodell für das einzelne Unternehmen "
        "entwickeln.\n\n"

        "Nutze zwingend die bereitgestellte Google-Suche. Bevorzuge "
        "Geschäftsberichte, regulatorische Veröffentlichungen und "
        "Investor-Relations-Unterlagen. Sekundärquellen nur ergänzend.\n\n"

        "Bewerte ausschließlich diese drei Dimensionen:\n\n"

        "1. Ertragskraft\n"
        "Ermittle die für die Unternehmensstruktur aussagekräftigsten "
        "Kennzahlen für nachhaltige Ertrags- oder Cashflowkraft. "
        "Beurteile möglichst die Entwicklung über mehrere Jahre. "
        "Verwende keine Kennzahl nur deshalb, weil sie bei klassischen "
        "Industrieunternehmen üblich ist.\n\n"

        "2. Wertentwicklung / wirtschaftliche Substanz\n"
        "Ermittle belastbare finanzielle Größen, die die langfristige "
        "wirtschaftliche Wert- oder Substanzentwicklung des Unternehmens "
        "abbilden. Wenn keine ausreichend belastbare und vergleichbare "
        "Größe verfügbar ist, muss die Dimension als nicht belastbar "
        "bewertbar gekennzeichnet werden.\n\n"

        "3. Finanzielle Stabilität\n"
        "Ermittle die für die konkrete Konzernstruktur aussagekräftigen "
        "Kennzahlen zu Verschuldung, Liquidität und Finanzierung. "
        "Berücksichtige strukturelle Unterschiede zwischen Holding- bzw. "
        "Muttergesellschaft und Beteiligungen, wenn diese für die "
        "wirtschaftliche Beurteilung wesentlich sind.\n\n"

        "Kapitalallokation, Management, Governance, Wettbewerbsvorteile, "
        "Dividendenpolitik und allgemeine strukturelle Geschäftsrisiken "
        "NICHT bewerten. Diese Themen werden in anderen InRA-Modulen "
        "bereits separat beurteilt.\n\n"

        "Für jede Dimension ist genau eines dieser Urteile zulässig:\n"
        "- Stark\n"
        "- Solide\n"
        "- Schwach\n"
        "- Nicht belastbar bewertbar\n\n"

        "Gib ausschließlich ein JSON-Array mit genau drei Objekten zurück. "
        "Jedes Objekt enthält:\n"
        '- "Dimension": exakter Name der Dimension\n'
        '- "Urteil": eines der vier zulässigen Urteile\n'
        '- "Kennzahlen": Liste der tatsächlich verwendeten Kennzahlen\n'
        '- "Begründung": kurze, faktenbasierte Begründung der Einordnung\n\n'

        "Keine numerische Punktzahl und keinen Gesamt-Quality-Score "
        "berechnen. Fehlende oder ungeeignete Daten niemals als schlechte "
        "Bewertung interpretieren. In diesem Fall "
        '"Nicht belastbar bewertbar" verwenden.\n\n'

        "Keine Quellenfelder im JSON erzeugen. Quellen werden technisch "
        "aus den Google-Grounding-Metadaten übernommen."
    )


def research_special_quantitative_quality_with_gemini(
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

    prompt = build_special_quantitative_research_prompt(
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

    raw_dimensions = _parse_json_response(
        response.text
    )

    dimensions = {}

    for item in raw_dimensions:
        dimension = item.get("Dimension")

        if dimension not in SPECIAL_QUANT_DIMENSIONS:
            continue

        rating = item.get("Urteil")
        metrics = item.get("Kennzahlen")
        reason = item.get("Begründung")

        if rating not in SPECIAL_QUANT_RATINGS:
            rating = "Nicht belastbar bewertbar"

        if not isinstance(metrics, list):
            metrics = []

        metrics = [
            str(metric).strip()
            for metric in metrics
            if str(metric).strip()
        ]

        dimensions[dimension] = {
            "Urteil": rating,
            "Kennzahlen": metrics,
            "Begründung": reason,
        }

    for dimension in SPECIAL_QUANT_DIMENSIONS:
        if dimension not in dimensions:
            dimensions[dimension] = {
                "Urteil": "Nicht belastbar bewertbar",
                "Kennzahlen": [],
                "Begründung": None,
            }

    candidate = response.candidates[0]
    grounding_metadata = getattr(
        candidate,
        "grounding_metadata",
        None,
    )

    grounding_chunks = (
        getattr(
            grounding_metadata,
            "grounding_chunks",
            None,
        )
        if grounding_metadata is not None
        else None
    )

    search_queries = _extract_search_queries(
        response
    )

    return {
        "Ticker": ticker,
        "Typ": "special_quantitative_quality",
        "Dimensionen": dimensions,
        "Quellen": _extract_grounding_sources(
            response
        ),
        "Suchanfragen": search_queries,
        "Grounding Diagnose": {
            "Metadata": grounding_metadata is not None,
            "Chunks": len(grounding_chunks or []),
            "Suchanfragen": len(search_queries),
        },
    }
