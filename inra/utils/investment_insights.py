def create_investment_insights(data: dict) -> list:
    insights = []

    roe = data.get("Eigenkapitalrendite")
    margin = data.get("Nettomarge")
    debt = data.get("Verschuldungsgrad")
    revenue_growth = data.get("Umsatzwachstum")
    dividend_yield = data.get("Dividendenrendite")
    forward_pe = data.get("Forward KGV")
    analyst_upside = data.get("Analystenpotenzial")

    if roe is not None:
        if roe >= 25:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Die Eigenkapitalrendite deutet auf eine "
                        "außergewöhnlich hohe Ertragskraft hin."
                    ),
                }
            )
        elif roe < 10:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Die Eigenkapitalrendite fällt derzeit "
                        "vergleichsweise niedrig aus."
                    ),
                }
            )

    if margin is not None:
        if margin >= 20:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Die hohe Nettomarge spricht für Effizienz "
                        "und Preissetzungsmacht."
                    ),
                }
            )
        elif margin < 5:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Die niedrige Nettomarge lässt nur begrenzten "
                        "Spielraum für operative Belastungen."
                    ),
                }
            )

    if revenue_growth is not None:
        if revenue_growth >= 10:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Das Umsatzwachstum zeigt eine starke "
                        "operative Dynamik."
                    ),
                }
            )
        elif revenue_growth < 0:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Der Umsatz ist zuletzt zurückgegangen."
                    ),
                }
            )
        elif revenue_growth < 3:
            insights.append(
                {
                    "category": "neutral",
                    "text": (
                        "Das Umsatzwachstum fällt derzeit verhalten aus."
                    ),
                }
            )

    if debt is not None:
        if debt <= 50:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Die Verschuldung erscheint auf Basis von "
                        "Debt/Equity gut kontrolliert."
                    ),
                }
            )
        elif debt > 200:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Die hohe Verschuldung erhöht die finanzielle "
                        "Abhängigkeit und sollte beobachtet werden."
                    ),
                }
            )
        elif debt > 120:
            insights.append(
                {
                    "category": "neutral",
                    "text": (
                        "Die Verschuldung liegt auf einem erhöhten Niveau."
                    ),
                }
            )

    if dividend_yield is not None:
        if dividend_yield >= 3:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Die Dividendenrendite ist für "
                        "einkommensorientierte Anleger attraktiv."
                    ),
                }
            )
        elif 0 < dividend_yield < 1:
            insights.append(
                {
                    "category": "neutral",
                    "text": (
                        "Die Dividende spielt für die aktuelle "
                        "Investmentthese nur eine untergeordnete Rolle."
                    ),
                }
            )

    if forward_pe is not None:
        if forward_pe <= 20:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Das Forward-KGV liegt im aktuell als attraktiv "
                        "bewerteten Bereich."
                    ),
                }
            )
        elif forward_pe > 30:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Das Forward-KGV signalisiert eine anspruchsvolle "
                        "Bewertung."
                    ),
                }
            )

    if analyst_upside is not None:
        if analyst_upside >= 20:
            insights.append(
                {
                    "category": "strength",
                    "text": (
                        "Das durchschnittliche Analystenziel deutet auf "
                        "deutliches rechnerisches Kurspotenzial hin."
                    ),
                }
            )
        elif analyst_upside < 0:
            insights.append(
                {
                    "category": "warning",
                    "text": (
                        "Das durchschnittliche Analystenziel liegt unter "
                        "dem aktuellen Aktienkurs."
                    ),
                }
            )

    return insights