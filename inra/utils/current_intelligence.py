import json
import re
import socket
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from datetime import date
from typing import Optional

from google import genai
from google.genai import types


ALLOWED_EVENT_IMPACTS = {-10, -5, -2, 0, 2, 5, 10}


def build_current_intelligence_prompt(
    ticker: str,
    company_name: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    momentum_1m: Optional[float] = None,
    momentum_3m: Optional[float] = None,
    momentum_6m: Optional[float] = None,
    research_context: Optional[str] = None,
) -> str:
    today = date.today().isoformat()

    price_context = []
    if momentum_1m is not None:
        price_context.append(f"1 Monat: {momentum_1m:+.1f} %")
    if momentum_3m is not None:
        price_context.append(f"3 Monate: {momentum_3m:+.1f} %")
    if momentum_6m is not None:
        price_context.append(f"6 Monate: {momentum_6m:+.1f} %")

    price_text = (
        " | ".join(price_context)
        if price_context
        else "Keine Kursperformance von InRA mitgegeben."
    )

    research_text = (
        research_context
        if research_context
        else "Keine verifizierbare Web-Recherche verfügbar."
    )

    return f"""
Du arbeitest als Research-Modul des Investment Research Assistant InRA.

Unternehmen: {company_name}
Ticker: {ticker}
Sektor: {sector or "unbekannt"}
Branche: {industry or "unbekannt"}
Heutiges Datum: {today}

Von InRA gemessene jüngere Kursentwicklung:
{price_text}

RECHERCHEGRUNDLAGE

Dir wurde bereits eine aktuelle Web-Recherche mit Quellen
bereitgestellt. Nutze ausschließlich diese Recherche als
aktuelle Tatsachengrundlage. Erfinde keine zusätzlichen
Nachrichten, Quellen oder aktuellen Entwicklungen aus deinem
Modellwissen.

RESEARCH-PAKET
{research_text}

QUELLENKLASSEN
A = Primärquelle
B = etabliertes Qualitätsmedium
C = Fach-/Anlegermedium oder sonstige verwendbare Webquelle
D = Sekundärquelle/Meinung

Bevorzuge A vor B vor C vor D.
Materielle Tatsachen und insbesondere ein Event Impact sollen
möglichst durch Quellen der Klassen A oder B gestützt sein.
Klasse D darf nicht allein die Grundlage für einen materiellen
Event Impact bilden.

AUFGABE

Werte das bereitgestellte Research-Paket aus.

Die Recherche soll insbesondere beantworten:

1. Was hat die Aktie in jüngerer Zeit wesentlich bewegt?
2. Welche konkreten Unternehmensereignisse erklären auffällige
   Kursbewegungen?
3. Welche positiven Entwicklungen sind für die Investmentthese
   derzeit materiell relevant?
4. Welche negativen Entwicklungen oder Risiken sind derzeit
   materiell relevant?
5. Welche wichtigen Entwicklungen sind noch offen und können
   künftig zum Katalysator oder Risiko werden?
6. Verändert das aktuelle Nachrichten- und Ereignisbild die
   Kaufchance gegenüber einer rein fundamentalen und technischen
   Analyse?

QUELLENHIERARCHIE

Bevorzuge:
1. Primärquellen: Investor Relations, Ad-hoc-Mitteilungen,
   Quartals-/Jahresberichte, regulatorische Veröffentlichungen.
2. Reuters und etablierte Wirtschaftsmedien.
3. Etablierte Anlegermedien wie BÖRSE ONLINE, FOCUS MONEY,
   DER AKTIONÄR, Barron's, MarketWatch, finanzen.net oder
   vergleichbare seriöse Quellen.
4. Veröffentlichte Analysteneinschätzungen ergänzend.

Trenne Tatsachen von journalistischen oder analystischen
Einschätzungen. Eine Meinung eines Mediums ist kein Fakt.

WICHTIGE REGELN

Führe die Recherche in zwei Zeithorizonten durch:

A) AKTUELLE ENTWICKLUNGEN
- Recherchiere relevante Nachrichten und Unternehmensereignisse
  der letzten 90 Tage.

B) FORTWIRKENDE STRATEGISCHE EREIGNISSE
- Recherchiere zusätzlich bis zu 18 Monate zurück.
- Nimm aus diesem Zeitraum nur Ereignisse auf, die noch nicht
  abgeschlossen sind oder die Investmentthese heute weiterhin
  wesentlich beeinflussen.
- Suche ausdrücklich nach laufenden Abspaltungen, Entkonsolidierungen,
  Übernahmen, Beteiligungsverkäufen, strategischen Umbauten,
  Restrukturierungen, regulatorischen Verfahren und anderen
  mehrmonatigen Transformationsprozessen.
- Prüfe bei solchen Ereignissen den aktuellen Umsetzungsstand.

Weitere Regeln:

- Reine Kursbewegungen sind kein eigener positiver oder negativer Event.
- Mehrere Artikel über dasselbe Ereignis zählen als ein Ereignis.
- Behaupte keine Ursache für eine Kursbewegung, wenn sie nicht
  ausreichend durch die Recherche gestützt wird.
- Wiederhole keine allgemeinen Kennzahlen, die eine normale
  Fundamentalanalyse ohnehin abdeckt, sofern keine neue Entwicklung
  dahintersteht.
- Konzentriere dich auf maximal 3 positive und maximal 3 negative
  Entwicklungen.
- Der Event Impact bewertet die VERÄNDERUNG DES INFORMATIONSSTANDS,
  nicht einfach, ob Nachrichten positiv oder negativ sind.
- Gute oder schlechte Nachrichten erhalten nicht automatisch Punkte.
- Bestätigt eine Entwicklung im Wesentlichen das bereits bekannte
  Investmentbild, ist 0 zulässig und häufig angemessen.
- Behaupte nicht ohne belastbare Evidenz, eine Nachricht sei bereits
  "eingepreist".
- Eine neue Entwicklung darf nur dann einen von 0 abweichenden Impact
  erhalten, wenn sie für die Investmententscheidung relevant ist.
- Ein einmaliges oder nicht strukturelles Ergebnisplus soll nicht
  wie eine dauerhafte Verbesserung behandelt werden.
- Strategische Veränderungen mit unklarer Wirkung sind grundsätzlich
  neutral zu behandeln, bis eine belastbare Richtung erkennbar ist.
- Trenne bei strategischen Ereignissen strikt zwischen FAKT und
  INTERPRETATION. Beispiel: Eine angekündigte Abspaltung ist ein Fakt;
  mögliche Vorteile durch höheren Streubesitz, größere Eigenständigkeit
  oder eine veränderte Bewertung sind zunächst Einordnungen.
- Formuliere erwartete oder mögliche Kapitalmarktwirkungen niemals als
  bereits eingetretene Tatsache.
- Aussagen wie "schafft Klarheit", "beseitigt Unsicherheit",
  "stärkt die Eigenständigkeit" oder vergleichbare Wirkungsbehauptungen
  sind als Einordnung zu kennzeichnen, sofern die konkrete Wirkung nicht
  durch die Recherche als eingetretener Fakt belegt ist.
- Ein Event Impact von +/-10 ist nur für außergewöhnliche,
  thesis-verändernde Entwicklungen vorgesehen.
- Normalerweise soll der Event Impact zwischen -5 und +5 liegen.
- Der Event Impact ist eine Gesamtbewertung des aktuellen
  Ereignisbilds und NICHT die Summe einzelner Nachrichten.

EVENT-IMPACT-SKALA B+

+10 = außergewöhnlicher positiver struktureller Wendepunkt
 +5 = materielle positive Veränderung des Investmentbildes
 +2 = neue, belastbare und entscheidungsrelevante positive Entwicklung
  0 = bestätigt Bekanntes / gemischtes Bild / nicht relevant neu
 -2 = neue, belastbare und entscheidungsrelevante negative Entwicklung
 -5 = materielle negative Veränderung des Investmentbildes
-10 = außergewöhnlicher negativer struktureller Wendepunkt

QUELLENZUORDNUNG

- Jede positive und negative Entwicklung muss ihre Quellen-IDs nennen.
- Jeder offene Faktor muss seine Quellen-IDs nennen.
- Die Kursbewegung muss die Quellen-IDs ihrer behaupteten Ursachen nennen.
- Der Event Impact muss eigene Event_Impact_Quellen_IDs enthalten.
- Verwende ausschließlich IDs aus dem bereitgestellten Research-Paket.
- Ein von 0 abweichender Event Impact benötigt mindestens eine konkret
  zugeordnete Quelle der Klasse A oder B.
- Klasse D allein darf keinen von 0 abweichenden Event Impact begründen.

Antworte ausschließlich als gültiges JSON-Objekt in genau dieser Struktur:

{{
  "Kursbewegung": {{
    "Zeitraum": "kurze Angabe",
    "Beschreibung": "kurze Beschreibung",
    "Ursachen": [
      "maximal drei konkret recherchierte Ursachen"
    ],
    "Sicherheit": "hoch|mittel|niedrig",
      "Quellen_IDs": ["Q1", "Q2"]
  }},
  "Positive_Entwicklungen": [
    {{
      "Datum": "YYYY-MM-DD oder null",
      "Titel": "kurzer Titel",
      "Beschreibung": "knappe investmentrelevante Einordnung",
      "Typ": "Fakt|Einordnung",
      "Relevanz": "hoch|mittel|niedrig",
        "Quellen_IDs": ["Q1", "Q2"]
    }}
  ],
  "Negative_Entwicklungen": [
    {{
      "Datum": "YYYY-MM-DD oder null",
      "Titel": "kurzer Titel",
      "Beschreibung": "knappe investmentrelevante Einordnung",
      "Typ": "Fakt|Einordnung",
      "Relevanz": "hoch|mittel|niedrig",
        "Quellen_IDs": ["Q1", "Q2"]
    }}
  ],
  "Offene_Faktoren": [
    {{
      "Titel": "kurzer Titel",
      "Beschreibung": "was noch offen ist und warum es relevant ist",
        "Quellen_IDs": ["Q1"]
    }}
  ],
  "Event_Impact_Vorschlag": 0,
    "Event_Impact_Quellen_IDs": ["Q1", "Q2"],
  "Event_Impact_Begruendung": "kurze Begründung der Gesamtbewertung",
  "KI_Fazit": "maximal 4 Sätze mit der Essenz dessen, was eine rein quantitative Analyse derzeit nicht erfasst"
}}
""".strip()


def _parse_json_response(response_text: str) -> dict:
    text = response_text.strip()

    if text.lower().startswith("```json"):
        text = text[7:].lstrip()
    elif text.startswith("```"):
        text = text[3:].lstrip()

    if text.endswith("```"):
        text = text[:-3].rstrip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as first_error:
        # Sehr begrenzte Reparatur:
        # fehlendes Komma zwischen zwei JSON-Feldern,
        # wenn das nächste Feld in einer neuen Zeile beginnt.
        repaired_text = re.sub(
            r'([}\]"0-9])\s*\n\s*(?="[^"]+"\s*:)',
            r'\1,\n',
            text,
        )

        try:
            data = json.loads(repaired_text)
        except json.JSONDecodeError as second_error:
            raise ValueError(
                "Gemini hat kein gültiges JSON geliefert. "
                f"Ursprünglicher Fehler: "
                f"Zeile {first_error.lineno}, "
                f"Spalte {first_error.colno}. "
                f"Reparaturversuch ebenfalls fehlgeschlagen: "
                f"Zeile {second_error.lineno}, "
                f"Spalte {second_error.colno}."
            ) from second_error

    if not isinstance(data, dict):
        raise ValueError(
            "Gemini-Antwort enthält kein JSON-Objekt."
        )

    return data

def _classify_source(
    url: str,
    company_name: str,
) -> dict:
    url_lower = (url or "").lower()

    try:
        hostname = (
            urlparse(url).hostname or ""
        ).lower()
    except ValueError:
        hostname = ""

    company_tokens = [
        token.lower()
        for token in re.findall(
            r"[A-Za-z0-9]+",
            company_name or "",
        )
        if len(token) >= 5
        and token.lower() not in {
            "corporation",
            "company",
            "incorporated",
            "limited",
            "holding",
            "holdings",
            "aktiengesellschaft",
        }
    ]

    blocked_domains = (
        "youtube.com",
        "youtu.be",
        "linkedin.com",
        "perplexity.ai",
    )

    quality_domains = (
        "reuters.com",
        "bloomberg.com",
        "ft.com",
        "wsj.com",
        "handelsblatt.com",
        "cnbc.com",
    )

    specialist_domains = (
        "boerse-online.de",
        "deraktionaer.de",
        "focus-money.de",
        "finanzen.net",
        "marketwatch.com",
        "barrons.com",
        "massdevice.com",
        "mddionline.com",
        "investing.com",
    )

    secondary_domains = (
        "finance.yahoo.com",
        "stockanalysis.com",
        "seekingalpha.com",
        "simplywall.st",
    )

    if any(domain in url_lower for domain in blocked_domains):
        return {
            "Klasse": "E",
            "Quellentyp": "Nicht als Beleg",
            "Verwendbar": False,
        }

    is_company_domain = any(
        token in hostname
        for token in company_tokens
    )

    if is_company_domain:
        return {
            "Klasse": "A",
            "Quellentyp": "Primärquelle",
            "Verwendbar": True,
        }

    if (
        "sec.gov" in url_lower
        or "bundesanzeiger.de" in url_lower
    ):
        return {
            "Klasse": "B",
            "Quellentyp": "Regulatorische Quelle – Bezug ungeprüft",
            "Verwendbar": True,
        }

    if any(domain in url_lower for domain in quality_domains):
        return {
            "Klasse": "B",
            "Quellentyp": "Qualitätsmedium",
            "Verwendbar": True,
        }

    if any(domain in url_lower for domain in specialist_domains):
        return {
            "Klasse": "C",
            "Quellentyp": "Fach-/Anlegermedium",
            "Verwendbar": True,
        }

    if any(domain in url_lower for domain in secondary_domains):
        return {
            "Klasse": "D",
            "Quellentyp": "Sekundärquelle/Meinung",
            "Verwendbar": True,
        }

    return {
        "Klasse": "D",
        "Quellentyp": "Sonstige Webquelle",
        "Verwendbar": True,
    }


def _build_tavily_queries(
    ticker: str,
    company_name: str,
) -> list:
    current_query = (
        f'"{company_name}" {ticker} '
        "latest earnings results guidance outlook "
        "revenue profit margins cash flow "
        "current developments"
    )

    strategic_query = (
        f'"{company_name}" {ticker} '
        "strategy acquisition divestment spin-off "
        "deconsolidation restructuring regulation "
        "strategic review ongoing"
    )

    return [
        {
            "Bereich": "Aktuell/operativ",
            "Query": current_query,
        },
        {
            "Bereich": "Strategisch",
            "Query": strategic_query,
        },
    ]


def _run_tavily_search(
    api_key: str,
    query: str,
    max_results: int,
) -> list:
    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        data = json.load(response)

    return data.get("results", [])


def _search_current_intelligence_with_tavily(
    api_key: str,
    ticker: str,
    company_name: str,
    max_results_per_query: int = 8,
) -> dict:
    queries = _build_tavily_queries(
        ticker=ticker,
        company_name=company_name,
    )

    sources = []
    research_parts = []
    seen_urls = set()

    for query_info in queries:
        area = query_info["Bereich"]
        query = query_info["Query"]

        results = _run_tavily_search(
            api_key=api_key,
            query=query,
            max_results=max_results_per_query,
        )

        for item in results:
            title = item.get("title")
            url = item.get("url")
            content = (item.get("content") or "").strip()
            score = item.get("score")

            if not url:
                continue

            normalized_url = url.rstrip("/").lower()

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)

            source_quality = _classify_source(
                url=url,
                company_name=company_name,
            )

            source_id = f"Q{len(sources) + 1}"

            source = {
                "ID": source_id,
                "Titel": title,
                "URL": url,
                "Score": score,
                "Bereich": area,
                "Klasse": source_quality["Klasse"],
                "Quellentyp": source_quality["Quellentyp"],
                "Verwendbar": source_quality["Verwendbar"],
            }

            sources.append(source)

            if not source_quality["Verwendbar"]:
                continue

            research_parts.append(
                "\n".join(
                    [
                        f"QUELLE {source_id}",
                        f"Recherchebereich: {area}",
                        f"Quellenklasse: {source_quality['Klasse']}",
                        f"Quellentyp: {source_quality['Quellentyp']}",
                        f"Titel: {title or 'Ohne Titel'}",
                        f"URL: {url}",
                        f"Inhalt: {content[:1500]}",
                    ]
                )
            )

    return {
        "queries": [
            item["Query"]
            for item in queries
        ],
        "sources": sources,
        "research_context": "\n\n".join(
            research_parts
        ),
    }


def _validate_event_impact(value) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return 0

    if value not in ALLOWED_EVENT_IMPACTS:
        return 0

    return value


def _normalize_source_ids(value) -> list:
    if not isinstance(value, list):
        return []

    result = []
    seen = set()

    for item in value:
        if not isinstance(item, str):
            continue

        source_id = item.strip().upper()

        if not re.fullmatch(r"Q[1-9][0-9]*", source_id):
            continue

        if source_id not in seen:
            seen.add(source_id)
            result.append(source_id)

    return result


def _validate_event_impact_sources(
    impact: int,
    source_ids,
    sources: list,
) -> dict:
    normalized_ids = _normalize_source_ids(source_ids)

    source_by_id = {
        source.get("ID"): source
        for source in sources
        if source.get("ID")
    }

    valid_sources = [
        source_by_id[source_id]
        for source_id in normalized_ids
        if source_id in source_by_id
        and source_by_id[source_id].get("Verwendbar")
    ]

    valid_ids = [source["ID"] for source in valid_sources]

    strong_sources = [
        source
        for source in valid_sources
        if source.get("Klasse") in {"A", "B"}
    ]

    if impact == 0:
        return {
            "impact": 0,
            "source_ids": valid_ids,
            "status": "Quellenbasis verifiziert",
            "hinweis": None,
        }

    if not valid_sources:
        return {
            "impact": 0,
            "source_ids": [],
            "status": "Nicht verifiziert",
            "hinweis": (
                "Event Impact auf 0 gesetzt: keine gültige "
                "konkret zugeordnete Quelle."
            ),
        }

    if not strong_sources:
        return {
            "impact": 0,
            "source_ids": valid_ids,
            "status": "Nicht ausreichend verifiziert",
            "hinweis": (
                "Event Impact auf 0 gesetzt: keine konkret "
                "zugeordnete Quelle der Klasse A oder B."
            ),
        }

    return {
        "impact": impact,
        "source_ids": valid_ids,
        "status": "Quellenbasis verifiziert",
        "hinweis": None,
    }


def generate_inra_final_conclusion(
    client,
    model: str,
    company_name: str,
    ticker: str,
    inra_context: dict,
    current_intelligence: dict,
) -> dict:
    """
    Erzeugt nach der Quellenvalidierung ein kurzes finales InRA-Fazit.

    Keine Websuche. Keine neue Bewertung. Ausschließlich Synthese der
    bereits berechneten InRA-Ergebnisse und der validierten aktuellen
    Entwicklungen.
    """

    compact_intelligence = {
        "Positive_Entwicklungen": (
            current_intelligence.get("Positive_Entwicklungen") or []
        ),
        "Negative_Entwicklungen": (
            current_intelligence.get("Negative_Entwicklungen") or []
        ),
        "Offene_Faktoren": (
            current_intelligence.get("Offene_Faktoren") or []
        ),
        "Event_Impact": current_intelligence.get(
            "Event_Impact_Vorschlag",
            0,
        ),
        "Event_Impact_Begruendung": current_intelligence.get(
            "Event_Impact_Begruendung"
        ),
    }

    prompt = f"""
Du bist der Schlussredakteur von InRA – Investment Research Assistant.

Erstelle für {company_name} ({ticker}) ein kurzes finales InRA-Fazit.

WICHTIG:
- Verwende AUSSCHLIESSLICH die unten gelieferten Informationen.
- Keine Websuche.
- Keine neuen Fakten erfinden.
- Keine neuen Scores berechnen.
- Keine Kauf-/Verkaufsempfehlung erfinden.
- Widersprich den gelieferten InRA-Scores nicht.
- Der bereits validierte Event Impact ist verbindlich.
- Wiederhole nicht einfach alle Kennzahlen.
- Verdichte das Gesamtbild auf das, was für die Investmententscheidung
  wirklich zählt.
- Schreibe wie eine seriöse gute Börsenzeitschrift:
  prägnant, verständlich, aktiv und lesenswert.
- Nicht flapsig, nicht werblich, kein Clickbait.
- Benenne Spannungen im Investmentcase klar, zum Beispiel:
  gute Qualität, aber hohe Bewertung; günstige Bewertung, aber
  schwache Qualität; positive Nachrichten, aber nur Einmaleffekte.
- Unterscheide dauerhafte operative Entwicklungen von Einmaleffekten.
- Formuliere Unsicherheit als Unsicherheit.

INRA-GESAMTBILD:
{json.dumps(inra_context, ensure_ascii=False, indent=2)}

VALIDIERTE AKTUELLE ENTWICKLUNGEN:
{json.dumps(compact_intelligence, ensure_ascii=False, indent=2)}

Antworte ausschließlich als gültiges JSON in diesem Format:

{{
  "Kernaussage": "eine prägnante Überschrift bzw. ein Satz",
  "Dafuer": "genau 1 kompakter Satz: Was spricht im Gesamtbild für die Aktie?",
  "Dagegen": "genau 1 kompakter Satz: Was bremst oder erhöht das Risiko?",
  "Worauf_es_ankommt": "eine kurze entscheidende Frage oder ein prägnanter Schlusssatz"
}}
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
        ),
    )

    result = _parse_json_response(response.text)

    return {
        "Kernaussage": str(
            result.get("Kernaussage") or ""
        ).strip(),
        "Dafuer": str(
            result.get("Dafuer") or ""
        ).strip(),
        "Dagegen": str(
            result.get("Dagegen") or ""
        ).strip(),
        "Worauf_es_ankommt": str(
            result.get("Worauf_es_ankommt") or ""
        ).strip(),
    }


CURRENT_INTELLIGENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "current_intelligence.json"
)


def load_current_intelligence() -> dict:
    if not CURRENT_INTELLIGENCE_PATH.exists():
        return {}

    try:
        raw = json.loads(
            CURRENT_INTELLIGENCE_PATH.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        return {}

    return raw if isinstance(raw, dict) else {}


def get_current_intelligence(
    ticker: str,
) -> Optional[dict]:
    if not ticker:
        return None

    saved = load_current_intelligence()

    result = saved.get(
        str(ticker).strip().upper()
    )

    return result if isinstance(result, dict) else None


def save_current_intelligence(
    research_result: dict,
) -> None:
    ticker = str(
        research_result.get("Ticker") or ""
    ).strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker fehlt im Rechercheergebnis."
        )

    if not research_result.get("Analyse_Datum"):
        raise ValueError(
            "Analyse-Datum fehlt im Rechercheergebnis."
        )

    saved = load_current_intelligence()

    saved[ticker] = research_result

    CURRENT_INTELLIGENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    CURRENT_INTELLIGENCE_PATH.write_text(
        json.dumps(
            saved,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def research_current_intelligence_with_gemini(
    api_key: str,
    tavily_api_key: str,
    ticker: str,
    company_name: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    momentum_1m: Optional[float] = None,
    momentum_3m: Optional[float] = None,
    momentum_6m: Optional[float] = None,
    inra_context: Optional[dict] = None,
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

    tavily_research = (
        _search_current_intelligence_with_tavily(
            api_key=tavily_api_key,
            ticker=ticker,
            company_name=company_name,
        )
    )

    prompt = build_current_intelligence_prompt(
        ticker=ticker,
        company_name=company_name,
        sector=sector,
        industry=industry,
        momentum_1m=momentum_1m,
        momentum_3m=momentum_3m,
        momentum_6m=momentum_6m,
        research_context=tavily_research[
            "research_context"
        ],
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

    result = _parse_json_response(response.text)

    result["Event_Impact_Vorschlag"] = (
        _validate_event_impact(
            result.get("Event_Impact_Vorschlag")
        )
    )

    result["Ticker"] = ticker
    result["Unternehmen"] = company_name
    result["Analyse_Datum"] = date.today().isoformat()
    result["Quellen"] = tavily_research["sources"]
    result["Suchanfragen"] = tavily_research["queries"]

    usable_sources = [
        source
        for source in result["Quellen"]
        if source.get("Verwendbar")
    ]

    strong_sources = [
        source
        for source in usable_sources
        if source.get("Klasse") in {"A", "B"}
    ]

    result["Verwendbare_Quellen"] = len(usable_sources)
    result["Starke_Quellen"] = len(strong_sources)

    event_validation = _validate_event_impact_sources(
        impact=result["Event_Impact_Vorschlag"],
        source_ids=result.get("Event_Impact_Quellen_IDs"),
        sources=result["Quellen"],
    )

    result["Event_Impact_Vorschlag"] = event_validation["impact"]
    result["Event_Impact_Quellen_IDs"] = event_validation["source_ids"]
    result["Event_Impact_Status"] = event_validation["status"]
    result["Event_Impact_Hinweis"] = event_validation["hinweis"]

    if inra_context:
        original_getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = ipv4_only

        try:
            result["InRA_Fazit"] = generate_inra_final_conclusion(
                client=client,
                model=model,
                company_name=company_name,
                ticker=ticker,
                inra_context=inra_context,
                current_intelligence=result,
            )
        finally:
            socket.getaddrinfo = original_getaddrinfo
    else:
        result["InRA_Fazit"] = None

    return result
