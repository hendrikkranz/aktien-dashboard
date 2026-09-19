import streamlit as st

from utils.market_environment_data import (
    load_market_risk_snapshot,
)


def render_explainer_text(text):
    st.html(
        f'''
        <div style="
            font-size: 0.86rem;
            line-height: 1.55;
            color: #b8bec7;
            margin: 0.15rem 0 0.8rem 0;
        ">
            {text}
        </div>
        '''
    )


def render_explainer_heading(text):
    st.html(
        f'''
        <div style="
            font-size: 0.9rem;
            font-weight: 700;
            color: #f0f2f6;
            margin: 0.85rem 0 0.3rem 0;
        ">
            {text}
        </div>
        '''
    )


def render_signal_line(title, text):
    st.html(
        f'''
        <div style="
            margin: 0.25rem 0 0.55rem 0;
            padding-left: 0.65rem;
            border-left: 2px solid #4b5563;
        ">
            <div style="
                font-size: 0.86rem;
                font-weight: 700;
                color: #f0f2f6;
                margin-bottom: 0.12rem;
            ">
                {title}
            </div>
            <div style="
                font-size: 0.82rem;
                line-height: 1.5;
                color: #aeb6c2;
            ">
                {text}
            </div>
        </div>
        '''
    )


def render_indicator(
    name,
    component,
    max_points,
    show_market_trend_details=False,
):
    if component is None:
        st.markdown(f"**{name}**")
        st.caption(
            f"Nicht bewertbar · 0 von {max_points:.0f} Punkten "
            "werden nicht als Nullrisiko gewertet."
        )
        return

    score = component.get("score")
    coverage = component.get("coverage")

    score_text = (
        f"{score:.1f} / {max_points:.0f}"
        if score is not None
        else "Nicht bewertbar"
    )

    if score is None:
        risk_icon = "⚪"
    else:
        risk_ratio = score / max_points

        if risk_ratio < 0.25:
            risk_icon = "🟢"
        elif risk_ratio < 0.50:
            risk_icon = "🟡"
        elif risk_ratio < 0.75:
            risk_icon = "🟠"
        else:
            risk_icon = "🔴"

    st.markdown(
        f"{risk_icon} **{name}** &nbsp; · &nbsp; {score_text}",
        unsafe_allow_html=True,
    )

    interpretations = {
        "Markttrend": (
            "Global überwiegend intakte Aufwärtstrends. "
            "Das negative Trendsignal ist derzeit auf China konzentriert."
        ),
        "Credit Stress": (
            "Kreditmärkte derzeit entspannt. US-High-Yield-Spreads "
            "sind niedrig; in Europa nur leichte Ausweitung."
        ),
        "Volatilität": (
            "Etwas erhöhte Unsicherheit, aber keine breite "
            "Stresseskalation. Emerging Markets bleiben volatiler."
        ),
        "Globale Liquidität": (
            "Uneinheitliche Liquiditätslage: Fed leicht expansiv, "
            "EZB leicht kontraktiv, BoJ deutlich kontraktiv. "
            "Insgesamt moderates Frühwarnsignal."
        ),
        "Zinskurve": (
            "Deutliches Frühwarnsignal aus der vorausgegangenen langen "
            "US-Zinskurveninversion und der anschließenden Versteilerung."
        ),
        "OECD CLI": (
            "Gemischtes Konjunkturbild: USA und Europa verbessern sich, "
            "China schwächt sich ab; der G20-Indikator stagniert."
        ),
        "Breiter US-Dollar": (
            "Der breite US-Dollar hat über drei und sechs Monate "
            "nachgegeben und erzeugt derzeit keinen Liquiditätsgegenwind."
        ),
        "Inflation": (
            "Inflationsrisiko insgesamt begrenzt, aber regional "
            "uneinheitlich. In der Eurozone bleibt der Preisdruck höher."
        ),
        "US-Erstanträge Arbeitslosenhilfe": (
            "Keine erkennbare Verschlechterung am US-Arbeitsmarkt: "
            "Die Erstanträge liegen weiterhin nahe ihrem 52-Wochen-Tief."
        ),
        "CAPE / Marktbewertung": (
            "Erhöhte Fallhöhe durch hohe Bewertungen, vor allem in den "
            "USA. China ist deutlich günstiger bewertet."
        ),
    }

    interpretation = interpretations.get(name)

    if interpretation:
        st.caption(interpretation)

    if name == "Zinskurve":
        series = component.get("series", {})

        for curve in series.values():
            metrics = curve.get("metrics")

            if metrics is None:
                continue

            spread = metrics["current_spread"]
            duration = metrics["inversion_duration_months"]
            resteepening = metrics["resteepening_from_minimum"]

            if curve.get("series_id") == "T10Y2Y":
                curve_name = "10J – 2J"
            elif curve.get("series_id") == "T10Y3M":
                curve_name = "10J – 3M"
            else:
                curve_name = curve.get("series_name", "Zinskurve")

            render_signal_line(
                curve_name,
                f"Aktuell <b>{spread:+.2f} pp</b> · "
                f"vorher <b>{duration} Monate invers</b> · "
                f"Versteilerung <b>{resteepening:+.2f} pp</b>",
            )

    if name == "OECD CLI":
        regions = component.get("regions", {})

        for region_id, region in regions.items():
            metrics = region.get("metrics")

            if metrics is None:
                render_signal_line(
                    region.get("name", "Region"),
                    "Nicht bewertbar",
                )
                continue

            if region_id == "G4E":
                region_name = "Europa (4 große Volkswirtschaften)"
            else:
                region_name = region.get("name", region_id)

            current_value = metrics["current_value"]
            change_3m = metrics["change_3m"]
            change_6m = metrics["change_6m"]

            render_signal_line(
                region_name,
                f"CLI <b>{current_value:.2f}</b> · "
                f"3M <b>{change_3m:+.2f}</b> · "
                f"6M <b>{change_6m:+.2f}</b>",
            )

    if name == "Breiter US-Dollar":
        data = component.get("data", {})

        if data and data.get("current_value") is not None:
            current_value = data["current_value"]
            change_3m = data["change_3m_pct"]
            change_6m = data["change_6m_pct"]

            render_signal_line(
                "Broad Dollar Index",
                f"Index <b>{current_value:.2f}</b> · "
                f"3M <b>{change_3m:+.1f} %</b> · "
                f"6M <b>{change_6m:+.1f} %</b>",
            )

    if name == "Inflation":
        regions = component.get("regions", {})

        for region_name, region in regions.items():
            headline = region.get("headline")
            core = region.get("core")

            if headline is None:
                render_signal_line(
                    region_name,
                    "Nicht bewertbar",
                )
                continue

            headline_yoy = headline["yoy_pct"]
            headline_momentum = headline["momentum_3m_annualized_pct"]

            if core is not None:
                core_yoy = core["yoy_pct"]
                core_momentum = core["momentum_3m_annualized_pct"]

                signal_text = (
                    f"Headline YoY <b>{headline_yoy:.1f} %</b> · "
                    f"3M-Momentum <b>{headline_momentum:.1f} %</b> · "
                    f"Kern YoY <b>{core_yoy:.1f} %</b> · "
                    f"3M-Momentum <b>{core_momentum:.1f} %</b>"
                )
            else:
                signal_text = (
                    f"Headline YoY <b>{headline_yoy:.1f} %</b> · "
                    f"3M-Momentum <b>{headline_momentum:.1f} %</b>"
                )

            render_signal_line(
                region_name,
                signal_text,
            )

    if name == "US-Erstanträge Arbeitslosenhilfe":
        data = component.get("data", {})

        if data and data.get("value") is not None:
            value = data["value"]
            ma4 = data["ma4"]
            low52 = data["low52"]
            rise = data["rise_from_52w_low_pct"]

            render_signal_line(
                "USA",
                f"Aktuell <b>{value / 1000:.0f} Tsd.</b> · "
                f"4W-Durchschnitt <b>{ma4 / 1000:.0f} Tsd.</b> · "
                f"52W-Tief <b>{low52 / 1000:.0f} Tsd.</b> · "
                f"Abstand zum 52W-Tief <b>{rise:+.1f} %</b>",
            )

    if name == "CAPE / Marktbewertung":
        regions = component.get("regions", {})

        for region_name, region in regions.items():
            cape = region.get("cape")
            percentile = region.get("cape_percentile")

            if cape is None or percentile is None:
                render_signal_line(
                    region_name,
                    "Nicht bewertbar",
                )
                continue

            render_signal_line(
                region_name,
                f"CAPE <b>{cape:.1f}</b> · "
                f"historisches Perzentil <b>{percentile:.0f}</b>",
            )

    if coverage is not None and coverage < 1:
        st.markdown(
            f"""
            <div style="
                font-size: 0.72rem;
                color: #8b949e;
                margin-top: -0.35rem;
                margin-bottom: 0.25rem;
            ">
                Datenabdeckung: {coverage * 100:.0f} %
            </div>
            """,
            unsafe_allow_html=True,
        )

    if name == "Volatilität":
        regions = component.get("regions", {})

        for region in regions.values():
            metrics = region.get("metrics")
            risk_score = region.get("risk_score")

            if metrics is None or risk_score is None:
                render_signal_line(
                    region.get("name", "Region"),
                    "Nicht bewertbar",
                )
                continue

            level = metrics["volatility_level"]
            percentile = metrics["percentile_history"]
            change_20d = metrics["change_20d"]
            change_60d = metrics["change_60d"]

            render_signal_line(
                region["name"],
                f"Volatilität <b>{level:.2f}</b> · "
                f"Perzentil <b>{percentile:.0f}</b> · "
                f"20T {change_20d:+.2f} · "
                f"60T {change_60d:+.2f}",
            )

        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Die Volatilitätskomponente misst die erwartete "
                "Schwankungsintensität an den Aktienmärkten. InRA "
                "verwendet den <b>VIX für die USA</b> und den "
                "<b>VXEEM für Emerging Markets</b>. Für Europa "
                "ist der VSTOXX derzeit nicht belastbar verfügbar."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Stark steigende Volatilität ist ein direktes Zeichen "
                "zunehmender Unsicherheit und Risikoaversion. Besonders "
                "aussagekräftig ist die Kombination aus einem bereits "
                "<b>hohen Volatilitätsniveau</b> und einer zusätzlich "
                "<b>steigenden Volatilitätsdynamik</b>."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "Der regionale Score besteht zu <b>80 % aus dem "
                "Volatilitätsniveau</b> und zu <b>20 % aus der "
                "Volatilitätsdynamik</b>. Das Niveau wird relativ zur "
                "jeweiligen langfristigen Historie bewertet. Die "
                "Dynamik berücksichtigt die Veränderung über "
                "20 und 60 Handelstage zu gleichen Teilen.<br><br>"
                "Regionalgewichtung: <b>USA 50 % · Europa 30 % · "
                "Emerging Markets 20 %</b>. Fehlende Regionen werden "
                "nicht als Nullrisiko behandelt, sondern aus der "
                "Berechnung herausgenommen."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Volatilität misst vor allem <b>gegenwärtigen "
                "Marktstress</b>. Sie zeigt damit eher, ob Unsicherheit "
                "bereits im Markt angekommen ist, als dass sie eine "
                "längerfristige Marktverschlechterung vorhersagt."
            )

            available_dates = []

            for region in regions.values():
                metrics = region.get("metrics")
                if metrics and metrics.get("as_of"):
                    available_dates.append(metrics["as_of"])

            if available_dates:
                latest_date = max(available_dates)
                date_text = (
                    f"{latest_date[8:10]}."
                    f"{latest_date[5:7]}."
                    f"{latest_date[:4]}"
                )
                st.caption(
                    f"Datenstand der verfügbaren Reihen: {date_text}."
                )

    if name == "Credit Stress":
        regions = component.get("regions", {})

        for region in regions.values():
            metrics = region.get("metrics")
            risk_score = region.get("risk_score")

            if metrics is None or risk_score is None:
                render_signal_line(
                    region.get("name", "Region"),
                    "Nicht bewertbar",
                )
                continue

            spread = metrics["spread_pct"]
            percentile = metrics["percentile_history"]
            change_20d = metrics["change_20d_pp"]
            change_60d = metrics["change_60d_pp"]

            render_signal_line(
                region["name"],
                f"HY-Spread <b>{spread:.2f} pp</b> · "
                f"Perzentil <b>{percentile:.0f}</b> · "
                f"20T {change_20d:+.2f} pp · "
                f"60T {change_60d:+.2f} pp",
            )

        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Credit Stress misst die Risikoaufschläge von "
                "<b>High-Yield-Unternehmensanleihen</b> gegenüber "
                "sicheren Staatsanleihen. Steigende Spreads bedeuten, "
                "dass Investoren für Kreditrisiken eine höhere "
                "Entschädigung verlangen."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Deutlich steigende High-Yield-Spreads können anzeigen, "
                "dass sich <b>Finanzierungsbedingungen verschlechtern</b> "
                "und die Risikoaversion im Finanzsystem zunimmt. "
                "Niedrige und stabile Spreads sprechen dagegen gegen "
                "akuten Kreditmarktstress."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "Der regionale Score besteht zu <b>70 % aus dem "
                "Spread-Niveau</b> und zu <b>30 % aus der "
                "Spread-Dynamik</b> über 20 und 60 Handelstage. "
                "Beim Niveau berücksichtigt InRA sowohl die absolute "
                "Höhe des Spreads als auch seine Position innerhalb "
                "der verfügbaren Historie.<br><br>"
                "Regionalgewichtung: <b>USA 60 % · Europa 40 %</b>."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Credit Spreads beschreiben vor allem den "
                "<b>aktuellen Zustand der Kreditmärkte</b>. Sie können "
                "sich bei Stress schnell verschlechtern, sind aber "
                "keine eigenständige Prognose für einen bevorstehenden "
                "Markteinbruch."
            )

            available_dates = []

            for region in regions.values():
                metrics = region.get("metrics")
                if metrics and metrics.get("as_of"):
                    available_dates.append(metrics["as_of"])

            if available_dates:
                latest_date = max(available_dates)
                date_text = (
                    f"{latest_date[8:10]}."
                    f"{latest_date[5:7]}."
                    f"{latest_date[:4]}"
                )
                st.caption(
                    f"Datenstand der verfügbaren Reihen: {date_text}."
                )

    if show_market_trend_details:
        regions = component.get("regions", {})

        for region in regions.values():
            metrics = region.get("metrics")
            risk_score = region.get("risk_score")

            if metrics is None or risk_score is None:
                render_signal_line(
                    region.get("name", "Region"),
                    "Nicht bewertbar",
                )
                continue

            distance = metrics["distance_to_sma200_pct"]
            slope = metrics["sma200_slope_20d_pct"]

            if risk_score >= 14:
                status = "ausgeprägter Abwärtstrend"
            elif risk_score >= 9:
                status = "beschädigter Trend"
            elif risk_score >= 5:
                status = "Korrektur im Aufwärtstrend"
            elif risk_score >= 4:
                status = "nachlassender Trend"
            else:
                status = "intakter Aufwärtstrend"

            render_signal_line(
                f"{region['name']} – {status}",
                f"<b>{distance:+.1f} %</b> zur 200-Tage-Linie · "
                f"Trend der 200-Tage-Linie über 20T "
                f"<b>{slope:+.1f} %</b>",
            )

        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Der Markttrend prüft für vier große "
                "Aktienmarktregionen, ob der jeweilige Markt "
                "<b>über oder unter seiner 200-Tage-Linie</b> liegt "
                "und ob diese langfristige Trendlinie steigt oder fällt."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Ein fallender Markt unter einer ebenfalls fallenden "
                "200-Tage-Linie spricht für einen bereits "
                "<b>beschädigten langfristigen Trend</b>. Das ist ein "
                "anderes Signal als eine kurzfristige Korrektur "
                "innerhalb eines weiterhin steigenden langfristigen "
                "Trends."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "<b>0/14</b> = intakter Aufwärtstrend · "
                "<b>4/14</b> = nachlassender Trend · "
                "<b>5/14</b> = Korrektur bei noch steigender "
                "200-Tage-Linie · "
                "<b>9/14</b> = beschädigter Trend · "
                "<b>14/14</b> = ausgeprägter Abwärtstrend.<br><br>"
                "Regionalgewichtung: <b>USA 40 % · Europa 25 % · "
                "China 20 % · Emerging Markets ex China 15 %</b>."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Die Trendbewertung beschreibt den "
                "<b>aktuellen Marktzustand</b>. Sie kann eine bereits "
                "laufende Verschlechterung sichtbar machen, ist aber "
                "keine eigenständige Prognose für einen bevorstehenden "
                "Markteinbruch."
            )

    if name == "Globale Liquidität":
        central_banks = component.get("central_banks", {})

        for bank in central_banks.values():
            metrics = bank.get("metrics")
            risk_score = bank.get("risk_score")

            bank_name = (
                f"{bank['name']} ({bank['region']})"
            )

            if metrics is None or risk_score is None:
                render_signal_line(
                    bank_name,
                    "Nicht bewertbar",
                )
                continue

            change_3m = metrics["change_3m_pct"]
            change_12m = metrics["change_12m_pct"]

            if change_12m >= 2:
                status = "expansiv"
            elif change_12m <= -5:
                status = "deutlich kontraktiv"
            elif change_12m < 0:
                status = "leicht kontraktiv"
            else:
                status = "weitgehend stabil"

            render_signal_line(
                f"{bank_name} – {status}",
                f"3 Monate <b>{change_3m:+.1f} %</b> · "
                f"12 Monate <b>{change_12m:+.1f} %</b>",
            )

        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Die globale Liquidität betrachtet die Entwicklung "
                "der <b>Zentralbankbilanzen</b> wichtiger "
                "Wirtschaftsräume. InRA misst, ob die Bilanzen über "
                "<b>3 und 12 Monate</b> wachsen oder schrumpfen."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Eine Ausweitung der Zentralbankbilanzen kann "
                "zusätzliche Liquidität in das Finanzsystem bringen "
                "und grundsätzlich risikofreundlich wirken. Eine "
                "deutliche und breit angelegte Bilanzverkürzung kann "
                "dagegen <b>Liquiditätsgegenwind</b> für Finanzmärkte "
                "darstellen. Entscheidend ist das globale Gesamtbild."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "Die Veränderung über <b>12 Monate zählt 70 %</b>, "
                "die Veränderung über <b>3 Monate 30 %</b>.<br><br>"
                "Regionalgewichtung: <b>USA 35 % · Eurozone 25 % · "
                "China 25 % · Japan 15 %</b>. Fehlende Regionen "
                "werden nicht als Nullrisiko behandelt, sondern aus "
                "der Berechnung herausgenommen."
            )

            render_explainer_heading("Datenqualität")

            for bank in central_banks.values():
                status = bank.get("status", "unavailable")
                as_of = bank.get("as_of")
                age_days = bank.get("age_days")

                status_text = {
                    "fresh": "🟢 aktuell",
                    "warning": "🟡 verzögert",
                    "stale": "🔴 veraltet",
                    "unavailable": "⚪ nicht verfügbar",
                }.get(status, status)

                if as_of:
                    date_text = (
                        f"{as_of[8:10]}.{as_of[5:7]}.{as_of[:4]}"
                    )
                    age_text = (
                        f" · {age_days} Tage alt"
                        if age_days is not None
                        else ""
                    )
                    render_explainer_text(
                        f"<b>{bank['name']}:</b> {status_text} · "
                        f"Stand {date_text}{age_text}"
                    )
                else:
                    render_explainer_text(
                        f"<b>{bank['name']}:</b> {status_text}"
                    )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Zentralbankbilanzen sind nur ein Teil der globalen "
                "Finanzierungs- und Liquiditätsbedingungen. Der "
                "Indikator ist deshalb ein <b>Frühwarn- und "
                "Umfeldsignal</b>, kein eigenständiges Timing-Signal "
                "für fallende Aktienkurse."
            )

    if name == "OECD CLI":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Der <b>OECD Composite Leading Indicator (CLI)</b> "
                "bündelt mehrere konjunkturelle Frühindikatoren. "
                "Er soll Wendepunkte der wirtschaftlichen Aktivität "
                "relativ zu ihrem längerfristigen Trend frühzeitig "
                "sichtbar machen."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Eine breit angelegte Abschwächung der Frühindikatoren "
                "kann auf nachlassende wirtschaftliche Dynamik in den "
                "kommenden Monaten hindeuten. Für Aktienmärkte ist "
                "besonders relevant, ob sich die Verschlechterung "
                "<b>über mehrere große Wirtschaftsregionen</b> erstreckt."
            )

            render_explainer_heading("So liest InRA das Signal")
            render_explainer_text(
                "InRA berücksichtigt sowohl das <b>aktuelle "
                "CLI-Niveau</b> als auch die Veränderung über "
                "<b>3 und 6 Monate</b>. Dadurch wird unterschieden, "
                "ob eine Region über oder unter ihrem langfristigen "
                "Trend liegt und ob sich die konjunkturelle Dynamik "
                "zuletzt verbessert oder verschlechtert.<br><br>"
                "Regionalgewichtung: <b>USA 40 % · Europa 25 % · "
                "China 20 % · G20 15 %</b>."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Der CLI ist ein <b>Konjunktur-Frühindikator</b> und "
                "kein direkter Aktienmarktindikator. Wirtschaftliche "
                "Abschwächungen müssen nicht unmittelbar zu fallenden "
                "Aktienkursen führen. Außerdem werden die monatlichen "
                "Daten mit zeitlicher Verzögerung veröffentlicht."
            )

            available_dates = []

            for region in component.get("regions", {}).values():
                metrics = region.get("metrics")
                if metrics and metrics.get("as_of"):
                    available_dates.append(metrics["as_of"])

            if available_dates:
                latest_date = max(available_dates)
                year, month = latest_date.split("-")
                st.caption(
                    f"Datenstand der verfügbaren Reihen: "
                    f"{month}.{year}."
                )

    if name == "Breiter US-Dollar":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Der breite US-Dollar-Index misst den Wert des "
                "<b>US-Dollars gegenüber einem breiten Korb "
                "internationaler Währungen</b>. InRA verwendet die "
                "Fed-Reihe DTWEXBGS und betrachtet insbesondere die "
                "Veränderung über 3 und 6 Monate."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Ein stark steigender US-Dollar kann die globalen "
                "Finanzierungsbedingungen verschärfen. Das gilt "
                "besonders für Unternehmen und Staaten außerhalb der "
                "USA mit Dollarverbindlichkeiten. Eine ausgeprägte "
                "Dollaraufwertung kann deshalb als "
                "<b>globaler Liquiditätsgegenwind</b> wirken."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "InRA bewertet die <b>Dynamik des breiten "
                "US-Dollars über 3 und 6 Monate</b>. Eine deutliche "
                "und anhaltende Aufwertung erhöht das Risikosignal. "
                "Ein stabiler oder fallender Dollar erzeugt dagegen "
                "keinen zusätzlichen Risikopunkt."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Der Dollar wird von vielen Faktoren beeinflusst, "
                "darunter Zinsdifferenzen, Geldpolitik und "
                "Kapitalströme. Eine Dollaraufwertung ist deshalb "
                "nicht automatisch ein Vorläufer fallender "
                "Aktienmärkte, sondern ein <b>Frühwarnsignal für "
                "möglicherweise straffere globale "
                "Finanzierungsbedingungen</b>."
            )

            data = component.get("data", {})
            as_of = data.get("as_of")

            if as_of:
                date = as_of[:10]
                year, month, day = date.split("-")
                st.caption(
                    f"Datenstand: {day}.{month}.{year} · "
                    f"Federal Reserve, DTWEXBGS."
                )

    if name == "Inflation":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Der Inflationsindikator betrachtet sowohl die "
                "<b>jährliche Teuerungsrate</b> als auch das auf ein "
                "Jahr hochgerechnete <b>3-Monats-Momentum</b>. "
                "Damit erfasst InRA nicht nur das aktuelle "
                "Inflationsniveau, sondern auch, ob sich der "
                "Preisdruck zuletzt beschleunigt oder abschwächt."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Hartnäckige oder erneut steigende Inflation kann den "
                "Spielraum der Zentralbanken für Zinssenkungen "
                "einschränken und länger hohe Zinsen begünstigen. "
                "Das kann Bewertungen und Finanzierungsbedingungen "
                "an den Aktienmärkten belasten."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "InRA berücksichtigt <b>Inflationsniveau und "
                "kurzfristige Dynamik</b> und ordnet beide zusätzlich "
                "relativ zu ihrer verfügbaren historischen Verteilung "
                "ein.<br><br>"
                "Regionalgewichtung im vollständigen Modell: "
                "<b>USA 50 % · Eurozone 30 % · China 20 %</b>. "
                "Fehlende Regionen werden nicht als Nullrisiko "
                "behandelt, sondern aus der Berechnung herausgenommen."
            )

            render_explainer_heading("Historische Einordnung")

            for region_name, region in component.get(
                "regions", {}
            ).items():
                headline = region.get("headline")
                core = region.get("core")

                if headline is None:
                    render_explainer_text(
                        f"<b>{region_name}:</b> nicht bewertbar."
                    )
                    continue

                text_parts = [
                    f"Headline YoY-Perzentil "
                    f"<b>{headline['yoy_percentile']:.0f}</b>",
                    f"3M-Momentum-Perzentil "
                    f"<b>{headline['momentum_3m_percentile']:.0f}</b>",
                ]

                if core is not None:
                    text_parts.extend(
                        [
                            f"Kern YoY-Perzentil "
                            f"<b>{core['yoy_percentile']:.0f}</b>",
                            f"Kern-Momentum-Perzentil "
                            f"<b>{core['momentum_3m_percentile']:.0f}</b>",
                        ]
                    )

                render_explainer_text(
                    f"<b>{region_name}:</b> "
                    + " · ".join(text_parts)
                )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Inflation wirkt auf Aktienmärkte vor allem über "
                "<b>Zinsen, Geldpolitik und Gewinnerwartungen</b>. "
                "Ein erhöhtes Inflationssignal bedeutet deshalb nicht "
                "automatisch fallende Aktienkurse. Entscheidend sind "
                "auch Wachstum, Zentralbankreaktion und die bereits "
                "eingepreisten Erwartungen."
            )

            available_dates = []

            for region in component.get("regions", {}).values():
                for key in ("headline", "core"):
                    series = region.get(key)
                    if series and series.get("as_of"):
                        available_dates.append(series["as_of"])

            if available_dates:
                latest_date = max(available_dates)[:10]
                year, month, day = latest_date.split("-")
                st.caption(
                    f"Datenstand der verfügbaren Reihen: "
                    f"{day}.{month}.{year}."
                )

    if name == "US-Erstanträge Arbeitslosenhilfe":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Die wöchentlichen <b>Erstanträge auf "
                "Arbeitslosenunterstützung</b> zeigen, wie viele "
                "Menschen in den USA erstmals entsprechende Leistungen "
                "beantragen. InRA betrachtet zusätzlich den "
                "4-Wochen-Durchschnitt und den Abstand zum "
                "52-Wochen-Tief."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Der US-Arbeitsmarkt reagiert häufig früh auf eine "
                "konjunkturelle Verschlechterung. Ein nachhaltiger "
                "Anstieg der Erstanträge von zuvor niedrigen Niveaus "
                "kann deshalb auf eine <b>zunehmende Abschwächung am "
                "Arbeitsmarkt</b> hindeuten."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "InRA misst, wie deutlich sich der geglättete "
                "Arbeitsmarktindikator von seinem <b>52-Wochen-Tief</b> "
                "entfernt hat. Kleine Schwankungen nahe dem Tief "
                "erzeugen kein Risikosignal. Erst eine zunehmend "
                "ausgeprägte Verschlechterung erhöht die "
                "Frühwarnpunkte."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "Wöchentliche Erstanträge können schwanken und durch "
                "Sondereffekte beeinflusst werden. Deshalb ist der "
                "4-Wochen-Durchschnitt wichtiger als eine einzelne "
                "Wochenzahl. Außerdem bildet der Indikator nur den "
                "<b>US-Arbeitsmarkt</b> ab."
            )

            data = component.get("data", {})
            as_of = data.get("as_of")

            if as_of:
                date = as_of[:10]
                year, month, day = date.split("-")
                st.caption(
                    f"Datenstand: {day}.{month}.{year} · "
                    f"US Initial Claims (ICSA)."
                )

    if name == "CAPE / Marktbewertung":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Das <b>CAPE</b> setzt das aktuelle Kursniveau eines "
                "Aktienmarktes ins Verhältnis zu den über mehrere "
                "Jahre geglätteten, inflationsbereinigten Gewinnen. "
                "Dadurch werden kurzfristige Gewinnschwankungen "
                "weniger stark gewichtet als bei einem normalen KGV."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Sehr hohe Bewertungen bedeuten nicht, dass ein "
                "Markteinbruch unmittelbar bevorsteht. Sie können aber "
                "die <b>Fallhöhe</b> erhöhen: Wenn Wachstumserwartungen, "
                "Zinsen oder Risikobereitschaft enttäuschen, besteht "
                "bei hoch bewerteten Märkten grundsätzlich mehr Raum "
                "für Bewertungsrückgänge."
            )

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "Entscheidend ist nicht nur die absolute CAPE-Höhe, "
                "sondern vor allem die <b>Position innerhalb der "
                "jeweiligen historischen Bewertungsspanne</b>. "
                "Je höher das historische Perzentil, desto größer "
                "wird die bewertungsbedingte Fallhöhe.<br><br>"
                "Regionalgewichtung: <b>USA 40 % · Europa 25 % · "
                "China 20 % · Emerging Markets 15 %</b>."
            )

            render_explainer_heading("Besonderheit der Regionaldaten")
            render_explainer_text(
                "Die von der verwendeten Datenquelle ausgewiesene "
                "Region <b>Emerging Markets enthält auch China</b>. "
                "China wird in InRA zusätzlich separat betrachtet. "
                "Diese Überschneidung ist eine bekannte Einschränkung "
                "der V0.1-Datenbasis und wird bei der Interpretation "
                "berücksichtigt."
            )

            render_explainer_heading("Grenzen des Signals")
            render_explainer_text(
                "CAPE ist vor allem ein Maß für "
                "<b>langfristige Bewertungsanfälligkeit</b>, nicht für "
                "kurzfristiges Markt-Timing. Hoch bewertete Märkte "
                "können über längere Zeit weiter steigen. Deshalb "
                "verwendet InRA CAPE ausschließlich für die Fallhöhe "
                "und nicht als Signal dafür, dass eine Korrektur "
                "unmittelbar bevorsteht."
            )

            as_of = component.get("as_of")
            source = component.get("source")

            if as_of:
                st.caption(
                    f"Datenstand: {as_of} · "
                    f"Quelle: {source or 'Research Affiliates'}."
                )

    if name == "Zinskurve":
        with st.expander("Warum dieses Signal?"):
            render_explainer_heading("Was misst der Indikator?")
            render_explainer_text(
                "Die Zinskurve vergleicht langfristige "
                "US-Staatsanleiherenditen mit kurzfristigen Renditen. "
                "InRA verwendet die Differenzen zwischen "
                "<b>10 Jahren und 2 Jahren</b> sowie zwischen "
                "<b>10 Jahren und 3 Monaten</b>. Eine negative "
                "Differenz bedeutet eine <b>inverse Zinskurve</b>."
            )

            render_explainer_heading("Warum ist das relevant?")
            render_explainer_text(
                "Längere Inversionsphasen traten historisch häufig vor "
                "konjunkturellen Abschwüngen auf. Relevant kann auch "
                "die Phase danach sein, wenn sich die Kurve wieder "
                "deutlich versteilert. Das ist ein "
                "<b>Frühwarnsignal</b>, aber kein präzises "
                "Timing-Signal für fallende Aktienkurse."
            )

            series = component.get("series", {})

            render_explainer_heading("So bewertet InRA")
            render_explainer_text(
                "InRA berücksichtigt <b>Dauer und Tiefe der "
                "vorangegangenen Inversion</b> sowie die anschließende "
                "<b>Versteilerung</b>. Gewichtung: "
                "<b>10 Jahre – 3 Monate 60 %</b> · "
                "<b>10 Jahre – 2 Jahre 40 %</b>.<br><br>"
                "Das aktuelle Signal entsteht vor allem aus der "
                "ungewöhnlich langen vorausgegangenen Inversion und "
                "dem anschließenden Re-Steepening. Zwischen diesem "
                "Signal und einer möglichen konjunkturellen oder "
                "marktseitigen Verschlechterung können erhebliche "
                "Zeitabstände liegen."
            )

            available_dates = []

            for curve in series.values():
                metrics = curve.get("metrics")
                if metrics and metrics.get("as_of"):
                    available_dates.append(metrics["as_of"])

            if available_dates:
                latest_date = max(available_dates)
                date_text = (
                    f"{latest_date[8:10]}."
                    f"{latest_date[5:7]}."
                    f"{latest_date[:4]}"
                )
                st.caption(
                    f"Datenstand der aktuellen Zinsreihen: {date_text}."
                )


st.markdown(
    """
    <div style="
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 0.15rem;
    ">
        Marktlage
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Wie hoch ist aktuell das Risiko, dass eine allgemeine "
    "Marktverschlechterung attraktive Aktien mit nach unten zieht?"
)

snapshot = load_market_risk_snapshot()

if snapshot is None:
    st.warning(
        "Noch kein gespeicherter Market-Risk-Snapshot vorhanden."
    )
    st.stop()

score = snapshot["score"]
label = snapshot["label"]
coverage = snapshot["coverage"]
blocks = snapshot["blocks"]

if score is None:
    st.warning(
        "Die Marktlage kann derzeit nicht belastbar bewertet werden."
    )
    st.stop()


st.markdown("## Globales Marktrisiko")

score_col, text_col = st.columns(
    [1, 2],
    vertical_alignment="center",
)

with score_col:
    if score < 25:
        ring_color = "#2ea043"
        status_color = "#2ea043"
    elif score < 45:
        ring_color = "#d6a72d"
        status_color = "#d6a72d"
    elif score < 65:
        ring_color = "#db6d28"
        status_color = "#db6d28"
    else:
        ring_color = "#f85149"
        status_color = "#f85149"

    score_angle = score * 3.6

    st.html(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            max-width: 190px;
            margin: 0 auto;
        ">
            <div style="
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #8b949e;
                margin-bottom: 0.55rem;
            ">
                Market Risk Score
            </div>

            <div style="
                width: 150px;
                height: 150px;
                border-radius: 50%;
                background:
                    conic-gradient(
                        {ring_color} 0deg {score_angle:.1f}deg,
                        #30363d {score_angle:.1f}deg 360deg
                    );
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            ">
                <div style="
                    width: 132px;
                    height: 132px;
                    border-radius: 50%;
                    background: #0e1117;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    box-shadow:
                        inset 0 0 18px rgba(255,255,255,0.025);
                ">
                    <div style="
                        font-size: 2.55rem;
                        line-height: 1;
                        font-weight: 750;
                        color: #fafafa;
                    ">
                        {score:.0f}
                    </div>
                    <div style="
                        font-size: 1rem;
                        color: #8b949e;
                        margin-top: 0.25rem;
                    ">
                        / 100
                    </div>
                </div>
            </div>

            <div style="
                margin-top: 0.7rem;
                padding: 0.28rem 0.75rem;
                border: 1px solid {status_color};
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 650;
                color: #f0f0f0;
                background: color-mix(
                    in srgb,
                    {status_color} 14%,
                    transparent
                );
            ">
                <span style="color:{status_color};">●</span>
                &nbsp;{label}
            </div>
        </div>
        """
    )

with text_col:
    current_stress = blocks["current_stress"]["score"]
    early_warning = blocks["early_warning"]["score"]
    fall_height = blocks["fall_height"]["score"]

    st.markdown(
        f"""
        **Aktuelle Einordnung: {label}**

        Der Markt zeigt derzeit **vergleichsweise wenig akuten Stress**.
        Die Frühwarnindikatoren liefern einzelne Risikosignale, ohne
        bislang auf eine breit angelegte Marktverschlechterung
        hinzudeuten.

        Die **Fallhöhe ist mit {fall_height:.1f} von 25 Punkten erhöht**.
        Hauptgrund ist die hohe Bewertung wichtiger Aktienmärkte.
        Das erhöht die Verwundbarkeit bei negativen Überraschungen,
        ist für sich genommen aber kein Timing-Signal.
        """
    )

generated_at = snapshot.get("generated_at")

snapshot_status = (
    f" · Snapshot erstellt: "
    f"{generated_at[8:10]}.{generated_at[5:7]}.{generated_at[:4]} "
    f"{generated_at[11:16]} Uhr"
    if generated_at
    else ""
)

st.caption(
    f"Datenabdeckung des Gesamtmodells: {coverage * 100:.0f} %"
    f"{snapshot_status}"
)

st.divider()

st.markdown("### Die drei Ebenen der Marktlage")

current = blocks["current_stress"]
early = blocks["early_warning"]
fall = blocks["fall_height"]

def render_market_level(icon, title, block, question, description):
    score = block.get("score")
    max_points = block.get("max_points")

    normalized_score = (
        score / max_points * 100
        if score is not None
        and max_points is not None
        and max_points > 0
        else None
    )

    if normalized_score is None:
        risk_label = "Nicht bewertbar"
        ring_color = "#8b949e"
        score_angle = 0
        score_text = "—"
    elif normalized_score < 25:
        risk_label = "Niedrig"
        ring_color = "#2ea043"
        score_angle = normalized_score * 3.6
        score_text = f"{normalized_score:.0f}"
    elif normalized_score < 45:
        risk_label = "Moderat"
        ring_color = "#d6a72d"
        score_angle = normalized_score * 3.6
        score_text = f"{normalized_score:.0f}"
    elif normalized_score < 65:
        risk_label = "Erhöht"
        ring_color = "#db6d28"
        score_angle = normalized_score * 3.6
        score_text = f"{normalized_score:.0f}"
    else:
        risk_label = "Hoch" if normalized_score < 80 else "Sehr hoch"
        ring_color = "#f85149"
        score_angle = normalized_score * 3.6
        score_text = f"{normalized_score:.0f}"

    left_col, gauge_col = st.columns(
        [5.5, 1],
        vertical_alignment="center",
    )

    with left_col:
        st.markdown(
            f"**{icon} {title} — "
            f"{score:.1f} / {max_points:.0f}**"
        )

        st.markdown(
            f"""
            <div style="
                font-size: 0.88rem;
                line-height: 1.45;
                margin-top: -0.35rem;
            ">
                <em>{question}</em> · {description}
            </div>
            <div style="
                font-size: 0.72rem;
                color: #8b949e;
                margin-top: 0.15rem;
                margin-bottom: 0.8rem;
            ">
                Abdeckung {block['coverage'] * 100:.0f} %
                {" · Score auf verfügbare Daten normalisiert"
                 if block["coverage"] < 1 else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with gauge_col:
        st.html(
            f"""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
                max-width: 100px;
            ">
                <div style="
                    width: 82px;
                    height: 82px;
                    border-radius: 50%;
                    background:
                        conic-gradient(
                            {ring_color} 0deg {score_angle:.1f}deg,
                            #30363d {score_angle:.1f}deg 360deg
                        );
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="
                        width: 68px;
                        height: 68px;
                        border-radius: 50%;
                        background: #0e1117;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                    ">
                        <div style="
                            font-size: 1.35rem;
                            line-height: 1;
                            font-weight: 750;
                            color: #fafafa;
                        ">
                            {score_text}
                        </div>
                        <div style="
                            font-size: 0.65rem;
                            color: #8b949e;
                            margin-top: 0.12rem;
                        ">
                            / 100
                        </div>
                    </div>
                </div>

                <div style="
                    margin-top: 0.3rem;
                    padding: 0.12rem 0.45rem;
                    border: 1px solid {ring_color};
                    border-radius: 999px;
                    font-size: 0.58rem;
                    font-weight: 700;
                    color: #f0f0f0;
                    white-space: nowrap;
                ">
                    <span style="color:{ring_color};">●</span>
                    {risk_label}
                </div>
            </div>
            """
        )


render_market_level(
    "🚨",
    "Aktueller Marktstress",
    current,
    "Kippt der Markt bereits?",
    "Stress in Kursen, Kreditmärkten und Volatilität",
)

render_market_level(
    "🔭",
    "Frühwarnindikatoren",
    early,
    "Bauen sich Risiken auf?",
    "Wirtschaftliche und finanzielle Vorboten einer Marktverschlechterung",
)

render_market_level(
    "🪂",
    "Fallhöhe",
    fall,
    "Wie verwundbar ist der Markt?",
    "Verwundbarkeit bei negativen Überraschungen",
)

st.divider()

st.markdown("### Was steckt hinter dem Score?")

st.markdown("#### 🚨 Aktueller Marktstress")
st.caption(
    "Zeigt, ob eine Marktverschlechterung bereits in "
    "wichtigen Finanzmarktindikatoren sichtbar wird."
)

render_indicator(
    "Markttrend",
    snapshot["components"]["market_trend"],
    14,
    show_market_trend_details=True,
)
render_indicator(
    "Credit Stress",
    snapshot["components"]["credit_stress"],
    11,
)
render_indicator(
    "Volatilität",
    snapshot["components"]["volatility_stress"],
    8,
)
render_indicator(
    "Marktbreite",
    snapshot["components"]["market_breadth"],
    7,
)

st.markdown("---")

st.markdown("#### 🔭 Frühwarnindikatoren")
st.caption(
    "Sucht nach Signalen, die einer breiteren "
    "Marktverschlechterung vorausgehen können."
)

render_indicator(
    "Globale Liquidität",
    snapshot["components"]["global_liquidity"],
    8,
)
render_indicator(
    "Zinskurve",
    snapshot["components"]["yield_curve"],
    7,
)
render_indicator(
    "OECD CLI",
    snapshot["components"]["oecd_cli"],
    7,
)
render_indicator(
    "Breiter US-Dollar",
    snapshot["components"]["broad_dollar"],
    5,
)
render_indicator(
    "Inflation",
    snapshot["components"]["inflation_trend"],
    5,
)
render_indicator(
    "US-Erstanträge Arbeitslosenhilfe",
    snapshot["components"]["initial_jobless_claims"],
    3,
)

st.markdown("---")

st.markdown("#### 🪂 Fallhöhe")
st.caption(
    "Zeigt, wie verwundbar der Aktienmarkt bei "
    "negativen Überraschungen sein könnte."
)

render_indicator(
    "CAPE / Marktbewertung",
    snapshot["components"]["valuation"],
    25,
)

st.divider()

st.caption(
    "InRA Market Risk V0.1 · 0 = niedriges allgemeines Marktrisiko · "
    "100 = sehr hohes allgemeines Marktrisiko"
)


st.markdown("### 📡 Under the Radar")
st.caption(
    "Ergänzende Markt- und Regimesignale mit eigenständiger "
    "Informationsbasis. Sie verändern den InRA Market Risk Score "
    "derzeit bewusst nicht."
)

from utils.market_environment_data import build_under_the_radar_snapshot

under_radar = build_under_the_radar_snapshot()

for key, title, question in [
    (
        "anfci",
        "ANFCI · US-Finanzbedingungen",
        "Verschärfen sich die Finanzbedingungen ungewöhnlich schnell?",
    ),
    (
        "gebert",
        "Gebert-Indikator · Europa/DAX",
        "Welches Regime zeigen Inflation, Zins, Euro und Saison?",
    ),
    (
        "sahm",
        "Sahm Rule · US-Rezessionsregime",
        "Zeigt der US-Arbeitsmarkt bereits eine deutliche Verschlechterung?",
    ),
]:
    item = under_radar.get(key, {})

    status = item.get("status")
    label = item.get("label", "Nicht verfügbar")
    detail = item.get("detail", "")
    as_of = item.get("as_of")

    if status == "warning":
        icon = "🔴"
    elif status == "normal":
        icon = "🟢"
    else:
        icon = "⚪"

    if hasattr(as_of, "date"):
        date_text = as_of.date().isoformat()
    elif as_of:
        date_text = str(as_of)[:10]
    else:
        date_text = "unbekannt"

    st.markdown(f"**{icon} {title} — {label}**")
    st.caption(question)
    st.write(detail)
    st.caption(f"Datenstand: {date_text}")

