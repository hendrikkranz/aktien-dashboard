from typing import Optional

import streamlit as st

from utils.fundamental_interpreter import (
    interpret_debt_equity,
    interpret_momentum,
    interpret_net_margin,
    interpret_roe,
)


def _icon(level: str) -> str:
    if level in ("excellent", "good"):
        return "🟢"

    if level == "solid":
        return "🟡"

    if level in ("weak", "poor"):
        return "🔴"

    return "⚪"


def _label(result: Optional[dict]) -> str:
    if result is None:
        return "Keine Einordnung"

    level = result.get("level")

    mapping = {
        "excellent": "Exzellent",
        "good": "Stark",
        "solid": "Solide",
        "weak": "Schwach",
        "poor": "Kritisch",
    }

    return mapping.get(level, "Keine Einordnung")


def _render_rating(result: Optional[dict]) -> None:
    if result is None:
        st.markdown("⚪ **Keine Einordnung**")
        return

    level = result.get("level")

    if not isinstance(level, str):
        st.markdown("⚪ **Keine Einordnung**")
        return

    st.markdown(
        f"{_icon(level)} **{_label(result)}**"
    )


def _format_percentage(value: Optional[float]) -> str:
    if value is None:
        return "–"

    return f"{value:+.1f} %"


def render_key_metrics(data: dict) -> None:
    roe = data.get("Eigenkapitalrendite")
    margin = data.get("Nettomarge")
    debt = data.get("Verschuldungsgrad")

    roe_result = interpret_roe(roe)
    margin_result = interpret_net_margin(margin)
    debt_result = interpret_debt_equity(debt)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "ROE",
            f"{roe:.1f} %" if roe is not None else "–",
            help=(
                "Return on Equity / Eigenkapitalrendite: Zeigt, wie viel Gewinn "
                "das Unternehmen mit dem eingesetzten Eigenkapital erzielt. "
                "Orientierung: Unter 10 % eher schwach, 10–20 % solide und "
                "über 20 % sehr stark. Sehr hohe Werte können durch Verschuldung "
                "oder Aktienrückkäufe verzerrt sein."
            ),
        )
        _render_rating(roe_result)

    with c2:
        st.metric(
            "Nettomarge",
            f"{margin:.1f} %" if margin is not None else "–",
            help=(
                "Zeigt, welcher Anteil des Umsatzes nach sämtlichen Kosten "
                "als Gewinn übrig bleibt. Orientierung: Unter 5 % häufig "
                "niedrig, 5–15 % solide und über 15 % stark. Die Einordnung "
                "ist branchenabhängig."
            ),
        )
        _render_rating(margin_result)

    with c3:
        st.metric(
            "Debt / Equity",
            f"{debt:.1f}" if debt is not None else "–",
            help=(
                "Verhältnis von Schulden zu Eigenkapital. Ein Wert von 50 "
                "entspricht ungefähr 50 Einheiten Schulden je 100 Einheiten "
                "Eigenkapital. Niedrigere Werte sind meist günstiger, die "
                "Einordnung ist jedoch stark branchenabhängig."
            ),
        )
        _render_rating(debt_result)
