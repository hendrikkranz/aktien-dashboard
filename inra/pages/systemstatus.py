import streamlit as st

from utils.data_health import (
    check_benchmark_cache_health,
    check_benchmark_core_coverage,
    check_benchmark_plausibility,
    check_market_risk_snapshot_health,
)


st.title("Systemstatus")
st.caption(
    "Frühwarnsystem für Datenqualität und technische "
    "Probleme in InRA."
)


checks = [
    check_benchmark_cache_health(),
    check_benchmark_core_coverage(),
    check_benchmark_plausibility(),
    check_market_risk_snapshot_health(),
]

status_rank = {
    "ok": 0,
    "warning": 1,
    "error": 2,
}

overall_status = max(
    (result["status"] for result in checks),
    key=lambda status: status_rank.get(status, 2),
)

status_config = {
    "ok": {
        "icon": "🟢",
        "title": "System betriebsbereit",
        "message": "Keine relevanten Datenprobleme erkannt.",
    },
    "warning": {
        "icon": "🟡",
        "title": "Hinweise vorhanden",
        "message": (
            "InRA ist betriebsbereit, aber mindestens ein "
            "Datenbereich sollte geprüft werden."
        ),
    },
    "error": {
        "icon": "🔴",
        "title": "Datenproblem erkannt",
        "message": (
            "Mindestens ein kritischer Datenbereich ist "
            "nicht zuverlässig verfügbar."
        ),
    },
}

overall = status_config[overall_status]

st.subheader(
    f"{overall['icon']} {overall['title']}"
)
st.write(overall["message"])

ok_count = sum(
    result["status"] == "ok"
    for result in checks
)
warning_count = sum(
    result["status"] == "warning"
    for result in checks
)
error_count = sum(
    result["status"] == "error"
    for result in checks
)

st.caption(
    f"{ok_count} OK · "
    f"{warning_count} Hinweise · "
    f"{error_count} Fehler"
)

st.divider()

st.subheader("Prüfungen")

icons = {
    "ok": "🟢",
    "warning": "🟡",
    "error": "🔴",
}

for result in checks:
    icon = icons.get(result["status"], "⚪")

    with st.container(border=True):
        st.markdown(
            f"**{icon} {result['component']}**"
        )
        st.write(result["detail"])

        metadata = []

        if result.get("source"):
            metadata.append(
                f"Quelle: {result['source']}"
            )

        if result.get("age_days") is not None:
            age_days = result["age_days"]
            age_label = "Tag" if age_days == 1 else "Tage"
            metadata.append(
                f"Alter: {age_days} {age_label}"
            )

        if result.get("coverage") is not None:
            metadata.append(
                f"Coverage: {result['coverage']:.0%}"
            )

        if metadata:
            st.caption(" · ".join(metadata))

        if result.get("error"):
            with st.expander("Diagnosedetails"):
                st.code(result["error"])


st.divider()

st.caption(
    "Hinweis: Manuell bzw. kostenpflichtig aktualisierte "
    "Quality- und News-Daten werden nicht allein aufgrund "
    "ihres Alters als Warnung bewertet."
)
