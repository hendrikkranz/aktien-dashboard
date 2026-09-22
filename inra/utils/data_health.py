from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

BENCHMARK_CACHE_PATH = Path("data/benchmark_cache.csv")
UNIVERSE_PATH = Path("data/universe.csv")


def _health_result(
    component: str,
    status: str,
    detail: str,
    *,
    source: Optional[str] = None,
    as_of=None,
    age_days: Optional[int] = None,
    coverage: Optional[float] = None,
    error: Optional[str] = None,
) -> dict:
    return {
        "component": component,
        "status": status,
        "source": source,
        "as_of": as_of,
        "age_days": age_days,
        "coverage": coverage,
        "detail": detail,
        "error": error,
    }


def check_benchmark_cache_health() -> dict:
    path = Path(BENCHMARK_CACHE_PATH)

    if not path.exists():
        return _health_result(
            "Benchmark-Cache",
            "error",
            "Benchmark-Cache fehlt.",
            source="Lokaler Cache",
            error=f"Datei nicht gefunden: {path}",
        )

    modified_at = datetime.fromtimestamp(path.stat().st_mtime)
    age_days = max(
        0,
        (datetime.now().date() - modified_at.date()).days,
    )

    try:
        cache = pd.read_csv(path)
    except Exception as exc:
        return _health_result(
            "Benchmark-Cache",
            "error",
            "Benchmark-Cache kann nicht gelesen werden.",
            source="Lokaler Cache",
            as_of=modified_at,
            age_days=age_days,
            error=str(exc),
        )

    if cache.empty:
        return _health_result(
            "Benchmark-Cache",
            "error",
            "Benchmark-Cache ist leer.",
            source="Lokaler Cache",
            as_of=modified_at,
            age_days=age_days,
        )

    if "Ticker" not in cache.columns:
        return _health_result(
            "Benchmark-Cache",
            "error",
            "Pflichtspalte 'Ticker' fehlt.",
            source="Lokaler Cache",
            as_of=modified_at,
            age_days=age_days,
        )

    duplicate_count = int(
        cache["Ticker"]
        .astype(str)
        .str.upper()
        .duplicated()
        .sum()
    )

    coverage = None
    universe_count = None

    try:
        universe = pd.read_csv(UNIVERSE_PATH)

        if "Ticker" in universe.columns:
            universe_tickers = set(
                universe["Ticker"]
                .dropna()
                .astype(str)
                .str.upper()
            )
            cache_tickers = set(
                cache["Ticker"]
                .dropna()
                .astype(str)
                .str.upper()
            )

            universe_count = len(universe_tickers)

            if universe_count:
                coverage = len(
                    universe_tickers & cache_tickers
                ) / universe_count

    except Exception:
        pass

    problems = []

    if age_days > 7:
        problems.append(
            f"Datenstand ist {age_days} Tage alt"
        )

    if duplicate_count:
        problems.append(
            f"{duplicate_count} doppelte Ticker"
        )

    if coverage is not None and coverage < 0.90:
        problems.append(
            f"Universe-Abdeckung nur {coverage:.0%}"
        )

    if problems:
        status = "warning"
        detail = " · ".join(problems)
    else:
        status = "ok"
        detail = (
            f"{len(cache)} Cache-Zeilen"
            + (
                f" · {coverage:.0%} Universe-Abdeckung"
                if coverage is not None
                else ""
            )
        )

    return _health_result(
        "Benchmark-Cache",
        status,
        detail,
        source="Lokaler Cache",
        as_of=modified_at,
        age_days=age_days,
        coverage=coverage,
    )


CORE_CACHE_FIELDS = (
    "Kurs",
    "Unternehmensqualität",
    "Kaufchance Basis",
    "Kaufchance",
)


def check_benchmark_core_coverage() -> dict:
    path = Path(BENCHMARK_CACHE_PATH)

    if not path.exists():
        return _health_result(
            "Benchmark-Kerndaten",
            "error",
            "Benchmark-Cache fehlt.",
            source="Lokaler Cache",
        )

    try:
        cache = pd.read_csv(path)
    except Exception as exc:
        return _health_result(
            "Benchmark-Kerndaten",
            "error",
            "Benchmark-Cache kann nicht gelesen werden.",
            source="Lokaler Cache",
            error=str(exc),
        )

    missing_columns = [
        field
        for field in CORE_CACHE_FIELDS
        if field not in cache.columns
    ]

    if missing_columns:
        return _health_result(
            "Benchmark-Kerndaten",
            "error",
            "Erwartete Kernfelder fehlen: "
            + ", ".join(missing_columns),
            source="Lokaler Cache",
        )

    if cache.empty:
        return _health_result(
            "Benchmark-Kerndaten",
            "error",
            "Keine Aktien für Coverage-Prüfung vorhanden.",
            source="Lokaler Cache",
        )

    field_coverage = {
        field: float(cache[field].notna().mean())
        for field in CORE_CACHE_FIELDS
    }

    minimum_coverage = min(field_coverage.values())

    affected = {}
    for field in CORE_CACHE_FIELDS:
        missing = cache.loc[
            cache[field].isna(),
            "Ticker",
        ].dropna().astype(str).tolist()

        if missing:
            affected[field] = missing

    if minimum_coverage < 0.90:
        status = "error"
    elif minimum_coverage < 0.98:
        status = "warning"
    else:
        status = "ok"

    coverage_text = " · ".join(
        f"{field}: {coverage:.0%}"
        for field, coverage in field_coverage.items()
    )

    if affected:
        affected_text = "; ".join(
            f"{field}: {', '.join(tickers[:10])}"
            for field, tickers in affected.items()
        )
        detail = f"{coverage_text} · Fehlend: {affected_text}"
    else:
        detail = f"{coverage_text} · alle Kernfelder vollständig"

    return _health_result(
        "Benchmark-Kerndaten",
        status,
        detail,
        source="Lokaler Cache",
        coverage=minimum_coverage,
    )


MARKET_RISK_SNAPSHOT_PATH = Path(
    "data/market_risk/latest_snapshot.json"
)


def check_market_risk_snapshot_health() -> dict:
    import json

    path = MARKET_RISK_SNAPSHOT_PATH

    if not path.exists():
        return _health_result(
            "Marktlage-Snapshot",
            "error",
            "Gespeicherter Marktlage-Snapshot fehlt.",
            source="Market Risk",
            error=f"Datei nicht gefunden: {path}",
        )

    try:
        snapshot = json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        return _health_result(
            "Marktlage-Snapshot",
            "error",
            "Marktlage-Snapshot kann nicht gelesen werden.",
            source="Market Risk",
            error=str(exc),
        )

    generated_at_raw = snapshot.get("generated_at")

    if not generated_at_raw:
        return _health_result(
            "Marktlage-Snapshot",
            "error",
            "Zeitstempel des Marktlage-Snapshots fehlt.",
            source="Market Risk",
        )

    try:
        generated_at = datetime.fromisoformat(
            generated_at_raw
        )
        generated_date = generated_at.date()
        age_days = max(
            0,
            (datetime.now().date() - generated_date).days,
        )
    except (TypeError, ValueError) as exc:
        return _health_result(
            "Marktlage-Snapshot",
            "error",
            "Zeitstempel des Marktlage-Snapshots ist ungültig.",
            source="Market Risk",
            error=str(exc),
        )

    coverage = snapshot.get("coverage")

    if not isinstance(coverage, (int, float)):
        return _health_result(
            "Marktlage-Snapshot",
            "error",
            "Gesamt-Coverage des Marktlage-Snapshots fehlt.",
            source="Market Risk",
            as_of=generated_at,
            age_days=age_days,
        )

    if age_days > 7 or coverage < 0.60:
        status = "error"
    elif age_days > 5 or coverage < 0.80:
        status = "warning"
    else:
        status = "ok"

    details = [
        f"Snapshot {age_days} Tage alt",
        f"Coverage {coverage:.0%}",
    ]

    if snapshot.get("score") is None:
        status = "error"
        details.append("Market-Risk-Score fehlt")

    return _health_result(
        "Marktlage-Snapshot",
        status,
        " · ".join(details),
        source="Market Risk",
        as_of=generated_at,
        age_days=age_days,
        coverage=float(coverage),
    )


def check_benchmark_plausibility() -> dict:
    path = Path(BENCHMARK_CACHE_PATH)

    try:
        cache = pd.read_csv(path)
    except Exception as exc:
        return _health_result(
            "Benchmark-Plausibilität",
            "error",
            "Benchmark-Daten können nicht geprüft werden.",
            source="Lokaler Cache",
            error=str(exc),
        )

    required = (
        "Ticker",
        "Kurs",
        "Unternehmensqualität",
        "Kaufchance",
    )

    missing_columns = [
        column
        for column in required
        if column not in cache.columns
    ]

    if missing_columns:
        return _health_result(
            "Benchmark-Plausibilität",
            "error",
            "Prüffelder fehlen: "
            + ", ".join(missing_columns),
            source="Lokaler Cache",
        )

    invalid_price = cache[
        cache["Kurs"].notna()
        & (pd.to_numeric(cache["Kurs"], errors="coerce") <= 0)
    ]

    quality = pd.to_numeric(
        cache["Unternehmensqualität"],
        errors="coerce",
    )
    opportunity = pd.to_numeric(
        cache["Kaufchance"],
        errors="coerce",
    )

    invalid_quality = cache[
        quality.notna()
        & ((quality < 0) | (quality > 100))
    ]

    invalid_opportunity = cache[
        opportunity.notna()
        & ((opportunity < 0) | (opportunity > 100))
    ]

    problems = []

    if not invalid_price.empty:
        problems.append(
            "Ungültiger Kurs: "
            + ", ".join(
                invalid_price["Ticker"].astype(str).tolist()[:10]
            )
        )

    if not invalid_quality.empty:
        problems.append(
            "Quality außerhalb 0–100: "
            + ", ".join(
                invalid_quality["Ticker"].astype(str).tolist()[:10]
            )
        )

    if not invalid_opportunity.empty:
        problems.append(
            "Kaufchance außerhalb 0–100: "
            + ", ".join(
                invalid_opportunity["Ticker"].astype(str).tolist()[:10]
            )
        )

    if problems:
        return _health_result(
            "Benchmark-Plausibilität",
            "error",
            " · ".join(problems),
            source="Lokaler Cache",
        )

    return _health_result(
        "Benchmark-Plausibilität",
        "ok",
        "Kurse und zentrale Scores im erwarteten Wertebereich.",
        source="Lokaler Cache",
    )
