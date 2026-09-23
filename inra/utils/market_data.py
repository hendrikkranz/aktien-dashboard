from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from modules.opportunity_score import (
    calculate_opportunity_breakdown,
    calculate_opportunity_score,
)
from modules.quality_score import (
    calculate_basis_quality_score,
    calculate_quality_breakdown,
    calculate_quality_score,
    calculate_qualitative_quality_score,
)
from modules.real_estate_quality_score import (
    calculate_real_estate_quality_score,
)
from utils.real_estate_quality_data import (
    REAL_ESTATE_DATA_LOADERS,
    load_real_estate_quality_data,
)
from utils.research_adjustments import (
    apply_research_adjustments,
)
from utils.qualitative_quality import (
    get_qualitative_quality_details,
    get_qualitative_quality_ratings,
)
from modules.trend_structure import (
    analyze_30w_support_reclaim,
    analyze_entry_confirmation,
    analyze_trend_structure,
    calculate_long_term_trend_score,
    classify_entry_setup,
)

MANUAL_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "data" / "manual_overrides.csv"

def _load_manual_overrides() -> pd.DataFrame:
    if not MANUAL_OVERRIDES_PATH.exists():
        return pd.DataFrame(
            columns=["Ticker", "Feld", "Wert", "Stand", "Quelle"]
        )

    return pd.read_csv(MANUAL_OVERRIDES_PATH)

def _get_manual_override(
    ticker: str,
    field: str,
) -> Optional[float]:
    overrides = _load_manual_overrides()

    match = overrides[
        (overrides["Ticker"] == ticker)
        & (overrides["Feld"] == field)
    ]

    if match.empty:
        return None

    value = match.iloc[0]["Wert"]

    if pd.isna(value):
        return None

    return float(value)

def _get_manual_override_metadata(
    ticker: str,
    field: str,
) -> dict:
    overrides = _load_manual_overrides()

    match = overrides[
        (overrides["Ticker"] == ticker)
        & (overrides["Feld"] == field)
    ]

    if match.empty:
        return {}

    row = match.iloc[0]

    return {
        "Stand": row.get("Stand"),
        "Quelle": row.get("Quelle"),
    }

def save_manual_override(
    ticker: str,
    field: str,
    value: float,
    date: str,
    source: str,
) -> None:
    overrides = _load_manual_overrides()

    new_row = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Feld": field,
                "Wert": value,
                "Stand": date,
                "Quelle": source,
            }
        ]
    )

    overrides = overrides[
        ~(
            (overrides["Ticker"] == ticker)
            & (overrides["Feld"] == field)
        )
    ]

    overrides = pd.concat(
        [overrides, new_row],
        ignore_index=True,
    )

    overrides.to_csv(
        MANUAL_OVERRIDES_PATH,
        index=False,
    )

def _calculate_period_return(
    close_prices: pd.Series,
    trading_days: int,
) -> Optional[float]:
    clean_prices = close_prices.dropna()

    if len(clean_prices) <= trading_days:
        return None

    start_price = clean_prices.iloc[-trading_days - 1]
    end_price = clean_prices.iloc[-1]

    if start_price is None or start_price == 0:
        return None

    return ((end_price / start_price) - 1) * 100


def _calculate_pullback_recovery(
    close_prices: pd.Series,
    lookback_days: int = 126,
    min_pullback_pct: float = 5.0,
) -> dict:
    """Diagnose des aktuell noch offenen Pullback-Zyklus.

    Ein Pullback beginnt an einem Hoch, wenn der Kurs danach
    mindestens min_pullback_pct zurücksetzt.

    Sobald das Ausgangshoch wieder erreicht oder überschritten wird,
    gilt die Episode als abgeschlossen. Abgeschlossene historische
    Pullbacks werden nicht als aktuelles Entry-Signal weitergeführt.

    Noch kein Score.
    """
    result = {
        "Pullback Hoch": None,
        "Pullback Tief": None,
        "Pullback %": None,
        "Recovery %": None,
        "Abstand Pullback-Hoch %": None,
        "Tage seit Pullback-Tief": None,
    }

    prices = pd.to_numeric(
        close_prices,
        errors="coerce",
    ).dropna()

    if len(prices) < 20:
        return result

    window = prices.tail(
        min(lookback_days, len(prices))
    )

    if len(window) < 20:
        return result

    values = window.to_numpy(dtype=float)

    # Das höchste noch nicht zurückeroberte Hoch definiert
    # den aktuell offenen Pullback-Zyklus.
    high_position = 0
    high_price = float(values[0])

    low_position = None
    low_price = None
    max_drawdown = 0.0
    pullback_active = False

    for position in range(1, len(values)):
        price = float(values[position])

        # Neues Hoch: vorherige Episode ist abgeschlossen.
        # Ab hier beginnt die Suche nach einem neuen Pullback.
        if price >= high_price:
            high_position = position
            high_price = price
            low_position = None
            low_price = None
            max_drawdown = 0.0
            pullback_active = False
            continue

        drawdown = (
            price / high_price - 1
        ) * 100

        if drawdown <= -min_pullback_pct:
            pullback_active = True

        if (
            low_price is None
            or price < low_price
        ):
            low_price = price
            low_position = position
            max_drawdown = drawdown

    if (
        not pullback_active
        or low_position is None
        or low_price is None
        or high_price <= low_price
    ):
        return result

    current_price = float(values[-1])

    recovery_pct = (
        (current_price - low_price)
        / (high_price - low_price)
        * 100
    )

    # Numerisch kann ein offener Zyklus maximal 100 % erholt sein.
    recovery_pct = max(
        0.0,
        min(100.0, recovery_pct),
    )

    distance_from_high_pct = (
        current_price / high_price - 1
    ) * 100

    days_since_low = (
        len(values) - 1 - low_position
    )

    result.update(
        {
            "Pullback Hoch": high_price,
            "Pullback Tief": low_price,
            "Pullback %": max_drawdown,
            "Recovery %": recovery_pct,
            "Abstand Pullback-Hoch %": distance_from_high_pct,
            "Tage seit Pullback-Tief": days_since_low,
        }
    )

    return result


def load_momentum_metrics(ticker: str) -> dict:
    empty_result = {
        "Momentum 3M": None,
        "Momentum 6M": None,
        "Momentum 12M": None,
        "RSI 14": None,
        "Pressure Balance": None,
        "CM MACD": None,
        "CM Signal": None,
        "CM Histogram": None,
        "CM MACD Weekly": None,
        "CM Signal Weekly": None,
        "CM Histogram Weekly": None,
        "Vorheriges 52W Hoch": None,
        "Abstand vorheriges 52W Hoch %": None,
    }

    try:
        history = yf.Ticker(ticker).history(
            period="5y",
            auto_adjust=True,
        )
    except Exception:
        return empty_result

    if history.empty or "Close" not in history.columns:
        return empty_result

    close_prices = history["Close"].dropna()
    weekly_close_prices = (
        close_prices
        .resample("W-FRI")
        .last()
        .dropna()
    )    

    if close_prices.empty:
        return empty_result

    previous_52w_high = None
    distance_to_previous_52w_high_pct = None

    # Vorheriges 52W-Hoch ohne die jüngsten 5 Handelstage.
    # Damit lässt sich diagnostizieren, ob der aktuelle Kurs
    # über ein bereits bestehendes Hoch ausgebrochen ist.
    if len(close_prices) >= 257:
        previous_window = close_prices.iloc[-257:-5]

        if not previous_window.empty:
            previous_52w_high = float(
                previous_window.max()
            )

            current_close = float(
                close_prices.iloc[-1]
            )

            if previous_52w_high > 0:
                distance_to_previous_52w_high_pct = (
                    current_close
                    / previous_52w_high
                    - 1
                ) * 100

    rsi_14 = None
    pressure_balance = None
    cm_macd = None
    cm_signal = None
    cm_histogram = None
    cm_macd_weekly = None
    cm_signal_weekly = None
    cm_histogram_weekly = None    

    if len(close_prices) >= 15:
        price_changes = close_prices.diff()

        gains = price_changes.clip(lower=0)
        losses = -price_changes.clip(upper=0)

        average_gain = gains.ewm(
            alpha=1 / 14,
            adjust=False,
            min_periods=14,
        ).mean()

        average_loss = losses.ewm(
            alpha=1 / 14,
            adjust=False,
            min_periods=14,
        ).mean()

        current_gain = average_gain.iloc[-1]
        current_loss = average_loss.iloc[-1]

        if current_loss == 0:
            rsi_14 = 100.0
        elif current_gain == 0:
            rsi_14 = 0.0
        else:
            relative_strength = (
                current_gain / current_loss
            )

            rsi_14 = 100 - (
                100 / (1 + relative_strength)
            )

    # Pressure Balance V0.1
    #
    # Misst den Kauf-/Verkaufsdruck der letzten 20 Handelstage.
    # Tagesdruck = Tagesrendite in % * relatives Handelsvolumen.
    # Die Balance liegt zwischen -1 (Distribution) und
    # +1 (Akkumulation).
    if "Volume" in history.columns:
        pressure_data = history[["Close", "Volume"]].copy()

        pressure_data["Close"] = pd.to_numeric(
            pressure_data["Close"],
            errors="coerce",
        )
        pressure_data["Volume"] = pd.to_numeric(
            pressure_data["Volume"],
            errors="coerce",
        )

        valid_volume_days = (
            pressure_data["Volume"].notna()
            & (pressure_data["Volume"] > 0)
        ).sum()

        if len(pressure_data) >= 40 and valid_volume_days >= 40:
            pressure_data["ReturnPct"] = (
                pressure_data["Close"]
                .pct_change(fill_method=None)
                * 100
            )

            pressure_data["AvgVolume20"] = (
                pressure_data["Volume"]
                .rolling(20)
                .mean()
            )

            pressure_data["RelativeVolume"] = (
                pressure_data["Volume"]
                / pressure_data["AvgVolume20"]
            )

            pressure_data["Pressure"] = (
                pressure_data["ReturnPct"]
                * pressure_data["RelativeVolume"]
            )

            pressure_last20 = pressure_data.tail(20)

            positive_pressure = pressure_last20.loc[
                pressure_last20["Pressure"] > 0,
                "Pressure",
            ].sum()

            negative_pressure = abs(
                pressure_last20.loc[
                    pressure_last20["Pressure"] < 0,
                    "Pressure",
                ].sum()
            )

            total_pressure = (
                positive_pressure + negative_pressure
            )

            if total_pressure > 0:
                pressure_balance = (
                    positive_pressure - negative_pressure
                ) / total_pressure

    if len(close_prices) >= 35:
        ema_12 = close_prices.ewm(
            span=12,
            adjust=False,
        ).mean()

        ema_26 = close_prices.ewm(
            span=26,
            adjust=False,
        ).mean()

        macd_line = ema_12 - ema_26

        signal_line = macd_line.ewm(
            span=9,
            adjust=False,
        ).mean()

        histogram = macd_line - signal_line

        cm_macd = macd_line.iloc[-1]
        cm_signal = signal_line.iloc[-1]
        cm_histogram = histogram.iloc[-1]

    if len(weekly_close_prices) >= 35:
        weekly_ema_12 = weekly_close_prices.ewm(
            span=12,
            adjust=False,
        ).mean()

        weekly_ema_26 = weekly_close_prices.ewm(
            span=26,
            adjust=False,
        ).mean()

        weekly_macd_line = (
            weekly_ema_12 - weekly_ema_26
        )

        weekly_signal_line = weekly_macd_line.ewm(
            span=9,
            adjust=False,
        ).mean()

        weekly_histogram = (
            weekly_macd_line - weekly_signal_line
        )

        cm_macd_weekly = weekly_macd_line
        cm_signal_weekly = weekly_signal_line
        cm_histogram_weekly = weekly_histogram        

    pullback_recovery = _calculate_pullback_recovery(
        close_prices
    )

    return {
        "Momentum 3M": _calculate_period_return(
            close_prices,
            63,
        ),
        "Momentum 6M": _calculate_period_return(
            close_prices,
            126,
        ),
        "Momentum 12M": _calculate_period_return(
            close_prices,
            251,
        ),
        "RSI 14": rsi_14,
        "Pressure Balance": pressure_balance,
        "Pullback Hoch": pullback_recovery["Pullback Hoch"],
        "Pullback Tief": pullback_recovery["Pullback Tief"],
        "Pullback %": pullback_recovery["Pullback %"],
        "Recovery %": pullback_recovery["Recovery %"],
        "Abstand Pullback-Hoch %": pullback_recovery[
            "Abstand Pullback-Hoch %"
        ],
        "Tage seit Pullback-Tief": pullback_recovery[
            "Tage seit Pullback-Tief"
        ],
        "CM MACD": cm_macd,
        "CM Signal": cm_signal,
        "CM Histogram": cm_histogram,
        "CM MACD Weekly": (
            cm_macd_weekly.tolist()
            if cm_macd_weekly is not None
            else None
        ),
        "CM Signal Weekly": (
            cm_signal_weekly.tolist()
            if cm_signal_weekly is not None
            else None
        ),
        "CM Histogram Weekly": (
            cm_histogram_weekly.tolist()
            if cm_histogram_weekly is not None
            else None
        ),
        "Vorheriges 52W Hoch": previous_52w_high,
        "Abstand vorheriges 52W Hoch %": (
            distance_to_previous_52w_high_pct
        ),
    }


def load_company_snapshot(ticker: str) -> dict:
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.get_info()
    dividend_history = ticker_obj.dividends
    annual_dividends = {}

    if not dividend_history.empty:
        annual_dividends = (
            dividend_history
            .groupby(dividend_history.index.year)
            .sum()
            .to_dict()
        )

    if annual_dividends:
        first_dividend_year = min(annual_dividends)
        current_year = pd.Timestamp.now().year

        for year in range(
            first_dividend_year,
            current_year,
        ):
            annual_dividends.setdefault(year, 0.0)

    dividend_growth_3y = None

    completed_years = sorted(
        year
        for year in annual_dividends
        if year < pd.Timestamp.now().year
    )

    if len(completed_years) >= 3:
        last_three_years = completed_years[-3:]

        start_dividend = annual_dividends[
            last_three_years[0]
        ]
        end_dividend = annual_dividends[
            last_three_years[-1]
        ]

        if start_dividend > 0:
            dividend_growth_3y = (
                (
                    end_dividend / start_dividend
                ) ** (1 / 2)
                - 1
            ) * 100

    dividend_growth_points = None

    if dividend_growth_3y is not None:
        if dividend_growth_3y >= 5:
            dividend_growth_points = 2
        elif dividend_growth_3y >= 0:
            dividend_growth_points = 1
        else:
            dividend_growth_points = 0

    dividend_continuity_years = None
    dividend_cut_last_3y = None

    if len(completed_years) >= 3:
        recent_years = completed_years[-5:]

        recent_cut_years = completed_years[-3:]

        dividend_cut_last_3y = any(
            annual_dividends[year] <= 0
            or (
                year - 1 in annual_dividends
                and annual_dividends[year]
                < annual_dividends[year - 1]
            )
            for year in recent_cut_years
        )

        dividend_continuity_years = 0

        if annual_dividends[recent_years[-1]] > 0:
            dividend_continuity_years = 1

            for previous_year, current_year in reversed(
                list(
                    zip(
                        recent_years,
                        recent_years[1:],
                    )
                )
            ):
                previous_dividend = annual_dividends[
                    previous_year
                ]
                current_dividend = annual_dividends[
                    current_year
                ]

                if (
                    previous_dividend <= 0
                    or current_dividend < previous_dividend
                ):
                    break

                dividend_continuity_years += 1

    dividend_continuity_points = None

    if dividend_continuity_years is not None:
        if dividend_cut_last_3y:
            dividend_continuity_points = 0
        elif dividend_continuity_years >= 5:
            dividend_continuity_points = 2
        elif dividend_continuity_years >= 3:
            dividend_continuity_points = 1

    dividend_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")
    five_year_avg_dividend_yield = info.get(
        "fiveYearAvgDividendYield"
    )
    dividend_rate = info.get("dividendRate")
    trailing_dividend_rate = info.get(
        "trailingAnnualDividendRate"
    )

    is_non_dividend_payer = (
        not annual_dividends
        and dividend_yield in (None, 0)
        and dividend_rate in (None, 0)
        and trailing_dividend_rate in (None, 0)
    )

    payout_ratio_points = None
    dividend_yield_points = None

    if is_non_dividend_payer:
        dividend_yield = 0.0
        payout_ratio_points = None
        dividend_yield_points = None

    else:
        if payout_ratio is not None:
            payout_percent = payout_ratio * 100

            if payout_percent > 110:
                payout_ratio_points = 0
            elif payout_percent > 90:
                payout_ratio_points = 1
            elif payout_percent > 70:
                payout_ratio_points = 2
            elif payout_percent > 20:
                payout_ratio_points = 3
            elif payout_percent > 0:
                payout_ratio_points = 2
            else:
                payout_ratio_points = 0

        if (
            dividend_yield is None
            and trailing_dividend_rate == 0
        ):
            dividend_yield = 0.0

        if dividend_yield is not None:
            if dividend_yield >= 5:
                dividend_yield_points = 5
            elif dividend_yield >= 4:
                dividend_yield_points = 4
            elif dividend_yield >= 3:
                dividend_yield_points = 3
            elif dividend_yield >= 2:
                dividend_yield_points = 2
            elif dividend_yield > 0:
                dividend_yield_points = 1
            else:
                dividend_yield_points = 0

    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        )
    analyst_target = info.get("targetMeanPrice")

    analyst_target_manual = False
    analyst_target_metadata = {}

    if analyst_target is None or pd.isna(analyst_target):
        analyst_target = _get_manual_override(
            ticker,
            "Analystenziel",
        )

        if analyst_target is not None:
            analyst_target_manual = True
            analyst_target_metadata = _get_manual_override_metadata(
                ticker,
                "Analystenziel",
            )

    # Explizite EPS-Konsensschätzungen für das laufende und
    # das folgende Geschäftsjahr. Daraus werden die KGVs selbst
    # berechnet, damit der Zeithorizont transparent bleibt.
    earnings_estimate = None

    try:
        earnings_estimate = ticker_obj.get_earnings_estimate()
    except Exception:
        earnings_estimate = None

    fiscal_year_current = None
    fiscal_year_next = None
    eps_current_year = None
    eps_next_year = None
    pe_current_year = None
    pe_next_year = None
    analysts_current_year = None
    analysts_next_year = None

    next_fiscal_year_end = info.get("nextFiscalYearEnd")

    if next_fiscal_year_end:
        try:
            fiscal_year_current = pd.to_datetime(
                next_fiscal_year_end,
                unit="s",
            ).year
            fiscal_year_next = fiscal_year_current + 1
        except (TypeError, ValueError, OverflowError):
            pass

    if (
        earnings_estimate is not None
        and not earnings_estimate.empty
    ):
        if "0y" in earnings_estimate.index:
            row = earnings_estimate.loc["0y"]
            eps_current_year = row.get("avg")
            analysts_current_year = row.get("numberOfAnalysts")

        if "+1y" in earnings_estimate.index:
            row = earnings_estimate.loc["+1y"]
            eps_next_year = row.get("avg")
            analysts_next_year = row.get("numberOfAnalysts")

    # Yahoo liefert die expliziten EPS-Schätzungen bei manchen
    # internationalen Aktien/ADRs in einer anderen Währungs- oder
    # Share-Einheit als den aktuellen Aktienkurs. forwardEps ist
    # dagegen mit forwardPE und currentPrice konsistent.
    #
    # Deshalb wird der +1y-EPS über forwardEps normalisiert und
    # derselbe Faktor auf den +0y-EPS angewendet.
    forward_eps_reference = info.get("forwardEps")
    eps_normalization_factor = None

    if (
        info.get("currency")
        and info.get("financialCurrency")
        and info.get("currency") != info.get("financialCurrency")
        and forward_eps_reference is not None
        and not pd.isna(forward_eps_reference)
        and forward_eps_reference > 0
        and eps_next_year is not None
        and not pd.isna(eps_next_year)
        and eps_next_year > 0
    ):
        eps_normalization_factor = (
            forward_eps_reference / eps_next_year
        )

        eps_current_year = (
            eps_current_year * eps_normalization_factor
            if (
                eps_current_year is not None
                and not pd.isna(eps_current_year)
                and eps_current_year > 0
            )
            else None
        )

        eps_next_year = (
            eps_next_year * eps_normalization_factor
        )

    # London-Aktien können bei Yahoo in Pence (GBp) notieren,
    # während EPS-Daten in Pfund (GBP) angegeben werden. Für die
    # KGV-Berechnung müssen Kurs und EPS dieselbe Einheit haben.
    pe_price = current_price

    if (
        pe_price is not None
        and info.get("currency") == "GBp"
        and info.get("financialCurrency") == "GBP"
    ):
        pe_price = pe_price / 100

    if (
        pe_price is not None
        and eps_current_year is not None
        and not pd.isna(eps_current_year)
        and eps_current_year > 0
    ):
        pe_current_year = pe_price / eps_current_year

    if (
        pe_price is not None
        and eps_next_year is not None
        and not pd.isna(eps_next_year)
        and eps_next_year > 0
    ):
        pe_next_year = pe_price / eps_next_year

    forward_pe = info.get("forwardPE")
    forward_pe_manual = False
    forward_pe_metadata = {}

    if forward_pe is None or pd.isna(forward_pe):
        forward_pe = _get_manual_override(
            ticker,
            "Forward KGV",
        )

        if forward_pe is not None:
            forward_pe_manual = True

        forward_pe_metadata = _get_manual_override_metadata(
            ticker,
            "Forward KGV",
        )

    analyst_upside = None

    if current_price and analyst_target:
        analyst_upside = (
            (analyst_target / current_price) - 1
        ) * 100

    return_on_equity = info.get("returnOnEquity")
    return_on_assets = info.get("returnOnAssets")
    profit_margin = info.get("profitMargins")
    operating_margin = info.get("operatingMargins")
    debt_to_equity = info.get("debtToEquity")
    revenue_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    income_stmt = ticker_obj.income_stmt
    balance_sheet = ticker_obj.balance_sheet

    revenue_history = pd.Series(dtype=float)
    income_history = pd.Series(dtype=float)

    if (
        income_stmt is not None
        and not income_stmt.empty
    ):
        if "Total Revenue" in income_stmt.index:
            revenue_history = (
                income_stmt.loc["Total Revenue"]
                .dropna()
                .sort_index()
            )

        if "Net Income" in income_stmt.index:
            income_history = (
                income_stmt.loc["Net Income"]
                .dropna()
                .sort_index()
            )

    revenue_growth_history = pd.Series(dtype=float)
    income_growth_history = pd.Series(dtype=float)

    if len(revenue_history) >= 2:
        revenue_growth_history = (
            revenue_history
            .pct_change()
            .dropna()
            * 100
        )

    if len(income_history) >= 2:
        income_growth_history = (
            income_history
            .pct_change()
            .dropna()
            * 100
        )

    revenue_growth_annual = None

    if not revenue_growth_history.empty:
        revenue_growth_annual = (
            revenue_growth_history.iloc[-1]
        )

    earnings_growth_annual = None

    if not income_growth_history.empty:
        earnings_growth_annual = (
            income_growth_history.iloc[-1]
        )

    revenue_growth_manual = False
    revenue_growth_metadata = {}

    if revenue_growth_annual is None:
        revenue_growth_annual = _get_manual_override(
            ticker,
            "Umsatzwachstum Jahresabschluss",
        )

        if revenue_growth_annual is not None:
            revenue_growth_manual = True
            revenue_growth_metadata = _get_manual_override_metadata(
                ticker,
                "Umsatzwachstum Jahresabschluss",
            )

    earnings_growth_manual = False
    earnings_growth_metadata = {}

    if earnings_growth_annual is None:
        earnings_growth_annual = _get_manual_override(
            ticker,
            "Gewinnwachstum Jahresabschluss",
        )

        if earnings_growth_annual is not None:
            earnings_growth_manual = True
            earnings_growth_metadata = _get_manual_override_metadata(
                ticker,
                "Gewinnwachstum Jahresabschluss",
            )

    revenue_growth_median = None
    income_growth_median = None

    if not revenue_growth_history.empty:
        revenue_growth_median = (
            revenue_growth_history
            .tail(3)
            .median()
        )

    if not income_growth_history.empty:
        income_growth_median = (
            income_growth_history
            .tail(3)
            .median()
        )

    extreme_revenue_jump = False
    income_sign_change = False

    if not revenue_growth_history.empty:
        extreme_revenue_jump = (
            (revenue_growth_history >= 60).any()
            or (revenue_growth_history <= -35).any()
        )

    if not income_history.empty:
        income_sign_change = (
            (income_history > 0).any()
            and (income_history <= 0).any()
        )

    growth_history_reliable = not (
        extreme_revenue_jump
        or income_sign_change
    )

    positive_revenue_years = None

    if not revenue_growth_history.empty:
        positive_revenue_years = int(
            (revenue_growth_history.tail(3) > 0).sum()
        )

    positive_income_years = None

    if not income_growth_history.empty:
        positive_income_years = int(
            (income_growth_history.tail(3) > 0).sum()
        )

    operating_cashflow = info.get("operatingCashflow")
    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    ebitda = info.get("ebitda")
    stockholders_equity = None

    if (
        balance_sheet is not None
        and not balance_sheet.empty
        and "Stockholders Equity" in balance_sheet.index
    ):
        equity_value = balance_sheet.loc["Stockholders Equity"].iloc[0]

        if not pd.isna(equity_value):
            stockholders_equity = float(equity_value)

    return_on_capital = None
    ebit = None
    interest_expense = None
    interest_coverage = None
    if (
        income_stmt is not None
        and not income_stmt.empty
        and balance_sheet is not None
        and not balance_sheet.empty
    ):
        operating_income = None
        pretax_income = None
        tax_provision = None
        tax_rate_for_calcs = None

        if "Operating Income" in income_stmt.index:
            operating_income = income_stmt.loc["Operating Income"].iloc[0]

        if "EBIT" in income_stmt.index:
            ebit = income_stmt.loc["EBIT"].iloc[0]

        if "Interest Expense" in income_stmt.index:
            interest_expense = income_stmt.loc["Interest Expense"].iloc[0]

        if "Pretax Income" in income_stmt.index:
            pretax_income = income_stmt.loc["Pretax Income"].iloc[0]

        if "Tax Provision" in income_stmt.index:
            tax_provision = income_stmt.loc["Tax Provision"].iloc[0]

        if "Tax Rate For Calcs" in income_stmt.index:
            tax_rate_for_calcs = income_stmt.loc["Tax Rate For Calcs"].iloc[0]

        interest_coverage = None

        if (
            ebit is not None
            and interest_expense not in (None, 0)
            and pd.notna(ebit)
            and pd.notna(interest_expense)
        ):
            interest_coverage = ebit / abs(interest_expense)

        tax_rate = None

        if (
            tax_provision is not None
            and not pd.isna(tax_provision)
            and pretax_income is not None
            and not pd.isna(pretax_income)
            and pretax_income != 0
        ):
            tax_rate = tax_provision / pretax_income
        elif (
            tax_rate_for_calcs is not None
            and not pd.isna(tax_rate_for_calcs)
        ):
            tax_rate = tax_rate_for_calcs

        if tax_rate is not None:
            tax_rate = max(0.0, min(float(tax_rate), 1.0))

        required_balance_rows = [
            "Total Debt",
            "Stockholders Equity",
            "Cash Cash Equivalents And Short Term Investments",
        ]

        roc_period = None
        roc_operating_income = None
        roc_tax_rate = None

        if "Operating Income" in income_stmt.index:
            for period in income_stmt.columns:
                period_operating_income = income_stmt.at[
                    "Operating Income",
                    period,
                ]

                if pd.isna(period_operating_income):
                    continue

                period_tax_rate = None

                if (
                    "Tax Provision" in income_stmt.index
                    and "Pretax Income" in income_stmt.index
                ):
                    period_tax_provision = income_stmt.at[
                        "Tax Provision",
                        period,
                    ]
                    period_pretax_income = income_stmt.at[
                        "Pretax Income",
                        period,
                    ]

                    if (
                        pd.notna(period_tax_provision)
                        and pd.notna(period_pretax_income)
                        and period_pretax_income != 0
                    ):
                        period_tax_rate = (
                            period_tax_provision
                            / period_pretax_income
                        )

                if (
                    period_tax_rate is None
                    and "Tax Rate For Calcs" in income_stmt.index
                ):
                    period_tax_rate_for_calcs = income_stmt.at[
                        "Tax Rate For Calcs",
                        period,
                    ]

                    if pd.notna(period_tax_rate_for_calcs):
                        period_tax_rate = period_tax_rate_for_calcs

                if period_tax_rate is None:
                    continue

                if period not in balance_sheet.columns:
                    continue

                balance_position = balance_sheet.columns.get_loc(period)

                if (
                    not isinstance(balance_position, int)
                    or balance_position + 1 >= balance_sheet.shape[1]
                ):
                    continue

                roc_period = period
                roc_operating_income = float(period_operating_income)
                roc_tax_rate = max(
                    0.0,
                    min(float(period_tax_rate), 1.0),
                )
                break

        if roc_period is not None:
            current_position = balance_sheet.columns.get_loc(roc_period)
            capital_positions = [
                current_position,
                current_position + 1,
            ]

            invested_capital_values = []
            average_invested_capital = None

            if all(
                row in balance_sheet.index
                for row in required_balance_rows
            ):
                for column_position in capital_positions:
                    debt = balance_sheet.loc[
                        "Total Debt"
                    ].iloc[column_position]
                    equity = balance_sheet.loc[
                        "Stockholders Equity"
                    ].iloc[column_position]
                    cash = balance_sheet.loc[
                        "Cash Cash Equivalents And Short Term Investments"
                    ].iloc[column_position]

                    if any(
                        pd.isna(value)
                        for value in [debt, equity, cash]
                    ):
                        invested_capital_values = []
                        break

                    invested_capital_values.append(
                        float(debt) + float(equity) - float(cash)
                    )

            if len(invested_capital_values) == 2:
                average_invested_capital = (
                    sum(invested_capital_values) / 2
                )

            if (
                average_invested_capital is None
                or average_invested_capital <= 0
            ):
                if "Invested Capital" in balance_sheet.index:
                    yahoo_invested_capital_values = [
                        balance_sheet.loc[
                            "Invested Capital"
                        ].iloc[column_position]
                        for column_position in capital_positions
                    ]

                    if not any(
                        pd.isna(value)
                        for value in yahoo_invested_capital_values
                    ):
                        yahoo_average_invested_capital = (
                            sum(
                                float(value)
                                for value
                                in yahoo_invested_capital_values
                            )
                            / 2
                        )

                        if yahoo_average_invested_capital > 0:
                            average_invested_capital = (
                                yahoo_average_invested_capital
                            )

            if (
                average_invested_capital is not None
                and average_invested_capital > 0
            ):
                nopat = (
                    roc_operating_income
                    * (1 - roc_tax_rate)
                )

                return_on_capital = (
                    nopat / average_invested_capital
                ) * 100

        capital_allocation_points = None

    cash_to_debt_ratio = None

    if (
        total_cash is not None
        and total_debt is not None
        and total_debt > 0
    ):
        cash_to_debt_ratio = total_cash / total_debt

    weak_debt_to_equity = (
        debt_to_equity is not None
        and debt_to_equity >= 100
    )

    critical_debt_to_equity = (
        debt_to_equity is not None
        and debt_to_equity > 200
    )

    weak_cash_to_debt = (
        cash_to_debt_ratio is not None
        and cash_to_debt_ratio < 0.20
    )

    critical_cash_to_debt = (
        cash_to_debt_ratio is not None
        and cash_to_debt_ratio < 0.10
    )

    capital_allocation_points = None

    if operating_cashflow is not None:

        if operating_cashflow > 0:

            if (
                critical_debt_to_equity
                or critical_cash_to_debt
            ):
                capital_allocation_points = 1

            elif (
                weak_debt_to_equity
                or weak_cash_to_debt
            ):
                capital_allocation_points = 2

            else:
                capital_allocation_points = 3

        else:

            if (
                weak_debt_to_equity
                or weak_cash_to_debt
            ):
                capital_allocation_points = 0

            else:
                capital_allocation_points = 1

    dividend_components = [
        (dividend_yield_points, 5),
        (payout_ratio_points, 3),
        (dividend_growth_points, 2),
        (dividend_continuity_points, 2),
        (capital_allocation_points, 3),
    ]

    dividend_available_points = sum(
        points
        for points, maximum in dividend_components
        if points is not None
    )

    dividend_available_maximum = sum(
        maximum
        for points, maximum in dividend_components
        if points is not None
    )

    dividend_strategy_score = None

    if (
        not is_non_dividend_payer
        and dividend_available_maximum > 0
    ):
        dividend_strategy_score = round(
            dividend_available_points
            / dividend_available_maximum
            * 15
        )

    dividend_strategy_score_raw = dividend_strategy_score

    if (
        dividend_strategy_score is not None
        and dividend_yield is not None
        and dividend_yield < 1.5
    ):
        dividend_strategy_score = min(
            dividend_strategy_score,
            9,
        )

    market_cap = info.get("marketCap")

    week_52_high = info.get("fiftyTwoWeekHigh")

    distance_to_52w_high = None

    if (
        current_price is not None
        and week_52_high is not None
        and week_52_high > 0
    ):
        distance_to_52w_high = (
            (current_price / week_52_high) - 1
        ) * 100

    if return_on_equity is not None:
        return_on_equity *= 100

    if return_on_assets is not None:
        return_on_assets *= 100

    if profit_margin is not None:
        profit_margin *= 100

    if operating_margin is not None:
        operating_margin *= 100

    if revenue_growth is not None:
        revenue_growth *= 100

    if earnings_growth is not None:
        earnings_growth *= 100

    momentum = load_momentum_metrics(ticker)

    history_5y = yf.Ticker(ticker).history(
        period="5y",
        interval="1wk",
        auto_adjust=True,
    )

    price_history_start = None
    price_history_end = None
    price_history_days = None

    if not history_5y.empty:
        valid_history = history_5y.dropna(
            subset=["Close"]
        )

        if not valid_history.empty:
            price_history_start = valid_history.index.min()
            price_history_end = valid_history.index.max()
            price_history_days = (
                price_history_end - price_history_start
            ).days

    # Ein 52W-Signal ist nur belastbar, wenn nahezu ein volles
    # Börsenjahr Kurshistorie vorhanden ist. Yahoo kann bei jungen
    # Listings bereits ein "52W High" liefern, obwohl tatsächlich
    # nur wenige Wochen oder Monate Kursdaten existieren.
    if (
        price_history_days is None
        or price_history_days < 350
    ):
        week_52_high = None
        distance_to_52w_high = None

    long_term_trend = analyze_trend_structure(
        history_5y,
        periods_per_year=52,
    )

    long_term_trend_score, long_term_trend_explanation = (
        calculate_long_term_trend_score(
            long_term_trend
        )
    )

    entry_confirmation = analyze_entry_confirmation(
        pressure_balance=momentum["Pressure Balance"],
        cm_macd_weekly=momentum["CM MACD Weekly"],
        cm_signal_weekly=momentum["CM Signal Weekly"],
        cm_histogram_weekly=momentum["CM Histogram Weekly"],
    )

    weekly_close = (
        history_5y["Close"]
        if not history_5y.empty and "Close" in history_5y.columns
        else None
    )
    support_30w = analyze_30w_support_reclaim(
        weekly_close
    )

    entry_setup = classify_entry_setup(
        long_term_trend,
        confirmation=entry_confirmation["confirmation"],
        positive_signals=entry_confirmation["positive_signals"],
        negative_signals=entry_confirmation["negative_signals"],
        pullback_pct=momentum["Pullback %"],
        recovery_pct=momentum["Recovery %"],
        distance_to_previous_52w_high_pct=momentum[
            "Abstand vorheriges 52W Hoch %"
        ],
        support_30w_signal=support_30w["signal"],
    )

    snapshot = {
        "Ticker": ticker,
        "Name": (
            info.get("longName")
            or info.get("shortName")
            or ticker
        ),
        "Website": info.get("website"),
        "Land": info.get("country"),
        "Börse": info.get("fullExchangeName"),
        "Sektor": info.get("sector"),
        "Branche": info.get("industry"),
        "Kurs": current_price,
        "Währung": info.get("currency"),
        "Dividendenrendite": dividend_yield,
        "Dividendenstrategie Status": (
            "Keine Dividende"
            if is_non_dividend_payer
            else "Bewertbar"
        ),
        "Dividendenrendite Punkte": dividend_yield_points,
        "Ausschüttungsquote": payout_ratio,
        "Ausschüttungsquote Punkte": payout_ratio_points,
        "Dividendenrendite 5J Ø": five_year_avg_dividend_yield,
        "Dividendenrate": dividend_rate,
        "Dividendenwachstum 3J": dividend_growth_3y,
        "Dividendenwachstum Punkte": dividend_growth_points,
        "Dividendenkontinuität Jahre": dividend_continuity_years,
        "Dividendenkürzung letzte 3J": dividend_cut_last_3y,
        "Dividendenkontinuität Punkte": dividend_continuity_points,
        "Dividenden jährlich": annual_dividends,
        "KGV": info.get("trailingPE"),
        "Forward KGV": forward_pe,
        "KGV GJ +0": pe_current_year,
        "KGV GJ +1": pe_next_year,
        "EPS GJ +0": eps_current_year,
        "EPS GJ +1": eps_next_year,
        "Geschäftsjahr +0": fiscal_year_current,
        "Geschäftsjahr +1": fiscal_year_next,
        "Analysten EPS GJ +0": analysts_current_year,
        "Analysten EPS GJ +1": analysts_next_year,
        "Forward KGV manuell": forward_pe_manual,
        "Forward KGV Metadaten": forward_pe_metadata,
        "Analystenziel": analyst_target,
        "Analystenziel manuell": analyst_target_manual,
        "Analystenziel Metadaten": analyst_target_metadata,
        "Analystenpotenzial": analyst_upside,
        "52W Hoch": week_52_high,
        "Abstand 52W Hoch": distance_to_52w_high,
        "Eigenkapitalrendite": return_on_equity,
        "Gesamtkapitalrendite": return_on_assets,
        "Kapitalrendite": return_on_capital,
        "Nettomarge": profit_margin,
        "Operative Marge": operating_margin,
        "Verschuldungsgrad": debt_to_equity,
        "Operativer Cashflow": operating_cashflow,
        "Gesamtliquidität": total_cash,
        "Gesamtverschuldung": total_debt,
        "EBITDA": ebitda,
        "Eigenkapital": stockholders_equity,
        "Zinsdeckung": interest_coverage,
        "Umsatzwachstum": revenue_growth,
        "Umsatzwachstum Jahresabschluss": revenue_growth_annual,
        "Umsatzwachstum manuell": revenue_growth_manual,
        "Umsatzwachstum Metadaten": revenue_growth_metadata,
        "Gewinnwachstum": earnings_growth,
        "Gewinnwachstum Jahresabschluss": earnings_growth_annual,
        "Gewinnwachstum manuell": earnings_growth_manual,
        "Gewinnwachstum Metadaten": earnings_growth_metadata,
        "Umsatzwachstum Median 3J": revenue_growth_median,
        "Gewinnwachstum Median 3J": income_growth_median,
        "Extremer Umsatzsprung": extreme_revenue_jump,
        "Gewinn Vorzeichenwechsel": income_sign_change,
        "Wachstumshistorie belastbar": growth_history_reliable,
        "Positive Umsatzjahre": positive_revenue_years,
        "Positive Gewinnjahre": positive_income_years,
        "Kapitalallokation Punkte": capital_allocation_points,
        "Dividendenstrategie Score vor Begrenzung": dividend_strategy_score_raw,
        "Dividendenstrategie Score": dividend_strategy_score,
        "Marktkapitalisierung": market_cap,
        "Kurshistorie Start": price_history_start,
        "Kurshistorie Ende": price_history_end,
        "Kurshistorie Tage": price_history_days,
        "Momentum 3M": momentum["Momentum 3M"],
        "Momentum 6M": momentum["Momentum 6M"],
        "Momentum 12M": momentum["Momentum 12M"],
        "RSI 14": momentum["RSI 14"],
        "Pressure Balance": momentum["Pressure Balance"],
        "Vorheriges 52W Hoch": momentum["Vorheriges 52W Hoch"],
        "Abstand vorheriges 52W Hoch %": momentum[
            "Abstand vorheriges 52W Hoch %"
        ],
        "Pullback Hoch": momentum["Pullback Hoch"],
        "Pullback Tief": momentum["Pullback Tief"],
        "Pullback %": momentum["Pullback %"],
        "Recovery %": momentum["Recovery %"],
        "Abstand Pullback-Hoch %": momentum[
            "Abstand Pullback-Hoch %"
        ],
        "Tage seit Pullback-Tief": momentum[
            "Tage seit Pullback-Tief"
        ],
        "CM MACD": momentum["CM MACD"],
        "CM Signal": momentum["CM Signal"],
        "CM Histogram": momentum["CM Histogram"],
        "Langfristiger Trend": long_term_trend["direction"],
        "Trendkanal Position": long_term_trend["position"],
        "Trendkanal Position Normalisiert": long_term_trend["normalized_position"],
        "Trendkanal Historie": long_term_trend[
            "channel_position_history"
        ],
        "Entry Setup": entry_setup["setup"],
        "Entry Setup Erklärung": entry_setup["detail"],
        "30W Signal": support_30w["signal"],
        "30W Test Wochen": support_30w["test_weeks_ago"],
        "30W Test Abstand %": support_30w["test_distance_pct"],
        "30W Slope Test %": support_30w["sma30_slope_at_test_pct"],
        "30W Abstand aktuell %": support_30w["current_distance_pct"],
        "30W Bewegung seit Test %": support_30w["move_since_test_pct"],
        "Entry Confirmation": entry_confirmation["confirmation"],
        "Entry Confirmation Positive": entry_confirmation[
            "positive_signals"
        ],
        "Entry Confirmation Negative": entry_confirmation[
            "negative_signals"
        ],
        "Entry Pressure Signal": entry_confirmation["pressure"],
        "Entry MACD Direction": entry_confirmation["macd_direction"],
        "Entry Histogram Direction": entry_confirmation[
            "histogram_direction"
        ],
        "Entry MACD Above Signal": entry_confirmation[
            "macd_above_signal"
        ],
        "Langfristiger Trend Status": long_term_trend["status"],
        "Langfristiger Trend Confidence": long_term_trend["confidence"],
        "Langfristiger Trend Score": long_term_trend_score,
        "Langfristiger Trend Erklärung": long_term_trend_explanation,
        "CM MACD Weekly": momentum["CM MACD Weekly"],
        "CM Signal Weekly": momentum["CM Signal Weekly"],
        "CM Histogram Weekly": momentum["CM Histogram Weekly"],        
    }

    snapshot = apply_research_adjustments(
        snapshot,
        ticker,
    )

    real_estate_quality = None
    real_estate_quality_data = None

    is_real_estate = snapshot.get("Sektor") == "Real Estate"

    if ticker in REAL_ESTATE_DATA_LOADERS:
        real_estate_data = load_real_estate_quality_data(ticker)
        real_estate_quality_data = real_estate_data.to_dict()

        real_estate_quality = calculate_real_estate_quality_score(
            growth_pct=real_estate_data.earnings_growth_pct,
            portfolio_growth_pct=(
                real_estate_data.portfolio_growth_pct
            ),
            occupancy_pct=real_estate_data.occupancy_pct,
            vacancy_pct=real_estate_data.vacancy_pct,
            ltv_pct=real_estate_data.ltv_pct,
            net_debt_ebitda=real_estate_data.net_debt_ebitda,
            coverage=real_estate_data.coverage_ratio,
        )

        quantitative_quality = real_estate_quality["score"]
    elif is_real_estate:
        quantitative_quality = None
    else:
        quantitative_quality = calculate_quality_score(snapshot)

    qualitative_quality_ratings = (
        get_qualitative_quality_ratings(ticker)
    )

    qualitative_quality_details = (
        get_qualitative_quality_details(ticker)
    )

    qualitative_quality = (
        calculate_qualitative_quality_score(
            qualitative_quality_ratings
        )
    )

    basis_quality = calculate_basis_quality_score(
        quantitative_quality,
        qualitative_quality["score"],
    )

    snapshot["Quantitative Quality"] = quantitative_quality
    snapshot["Real Estate Quality"] = real_estate_quality
    snapshot["Real Estate Quality Data"] = real_estate_quality_data

    snapshot["Kaufchance"] = calculate_opportunity_score(
        snapshot
    )
    snapshot["Opportunity Breakdown"] = (
        calculate_opportunity_breakdown(snapshot)
    )

    snapshot["Qualitative Quality"] = qualitative_quality["score"]
    snapshot["Qualitative Quality Details"] = qualitative_quality
    snapshot["Qualitative Quality Factor Details"] = qualitative_quality_details
    snapshot["Basis Quality"] = basis_quality
    snapshot["Unternehmensqualität"] = (
        basis_quality
        if basis_quality is not None
        else quantitative_quality
    )

    if is_real_estate and real_estate_quality is None:
        snapshot["Quality Breakdown"] = {}
    else:
        snapshot["Quality Breakdown"] = (
            calculate_quality_breakdown(snapshot)
        )

    return snapshot


def load_price_history(
    ticker: str,
    period: str = "6mo",
) -> pd.DataFrame:
    try:
        history = yf.Ticker(ticker).history(
            period=period,
            auto_adjust=True,
        )
    except Exception:
        return pd.DataFrame(
            columns=["Datum", "Schlusskurs"]
        )

    if history.empty or "Close" not in history.columns:
        return pd.DataFrame(
            columns=["Datum", "Schlusskurs"]
        )

    price_history = history.reset_index()

    date_column = price_history.columns[0]

    price_history = price_history[
        [date_column, "Close"]
    ].copy()

    price_history.columns = [
        "Datum",
        "Schlusskurs",
    ]

    price_history["Datum"] = pd.to_datetime(
        price_history["Datum"]
    )

    price_history["Schlusskurs"] = pd.to_numeric(
        price_history["Schlusskurs"],
        errors="coerce",
    )

    return price_history.dropna(
        subset=["Datum", "Schlusskurs"]
    )