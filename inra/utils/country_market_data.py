"""Datenebene für die InRA-Länderansichten."""

from functools import lru_cache
from pathlib import Path

import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


INDEX_CONSTITUENTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "index_constituents"
)


GERMANY_INDICES = {
    "DAX": {
        "name": "DAX",
        "ticker": "^GDAXI",
        "members": 40,
        "url": "https://en.wikipedia.org/wiki/DAX",
        "slug": "dax",
    },
    "MDAX": {
        "name": "MDAX",
        "ticker": "^MDAXI",
        "members": 50,
        "url": "https://www.onvista.de/index/einzelwerte/MDAX-Index-323547",
        "source": "onvista",
        "slug": "mdax",
    },
    "SDAX": {
        "name": "SDAX",
        "ticker": "^SDAXI",
        "members": 70,
        "url": "https://www.onvista.de/index/einzelwerte/SDAX-Index-324724",
        "source": "onvista",
        "slug": "sdax",
    },
}


FRANCE_INDICES = {
    "CAC 40": {
        "name": "CAC 40",
        "ticker": "^FCHI",
        "members": 40,
        "slug": "cac_40",
    },
}


SWITZERLAND_INDICES = {
    "SMI": {
        "name": "SMI",
        "ticker": "^SSMI",
        "members": 20,
        "slug": "smi",
    },
}


UK_INDICES = {
    "FTSE 100": {
        "name": "FTSE 100",
        "ticker": "^FTSE",
        "members": 100,
        "slug": "ftse_100",
    },
}


NETHERLANDS_INDICES = {
    "AEX": {
        "name": "AEX",
        "ticker": "^AEX",
        "members": 25,
        "slug": "aex",
    },
}


NORDIC_INDICES = {
    "NASDAQ OMX Nordic 120": {
        "name": "NASDAQ OMX Nordic 120",
        "ticker": "^NOMXN120",
        "members": 120,
        "slug": "nordic_120",
    },
}


CANADA_INDICES = {
    "S&P/TSX 60": {
        "name": "S&P/TSX 60",
        "ticker": "XIU.TO",
        "members": 60,
        "slug": "tsx_60",
    },
}


SPAIN_INDICES = {
    "IBEX 35": {
        "name": "IBEX 35",
        "ticker": "^IBEX",
        "members": 35,
        "slug": "ibex_35",
    },
}


ITALY_INDICES = {
    "FTSE MIB": {
        "name": "FTSE MIB",
        "ticker": "FTSEMIB.MI",
        "members": 40,
        "slug": "ftse_mib",
    },
}


JAPAN_INDICES = {
    "Nikkei 225": {
        "name": "Nikkei 225",
        "ticker": "^N225",
        "members": 225,
        "slug": "nikkei_225",
    },
}


USA_INDICES = {
    "Dow Jones": {
        "name": "Dow Jones",
        "ticker": "^DJI",
        "members": 30,
        "slug": "dow_jones",
    },
    "Nasdaq 100": {
        "name": "Nasdaq 100",
        "ticker": "^NDX",
        "members": 101,
        "slug": "nasdaq_100",
    },
}


COUNTRY_MARKETS = {
    "Germany": {
        "name": "Deutschland",
        "flag": "🇩🇪",
        "indices": GERMANY_INDICES,
    },
    "USA": {
        "name": "USA",
        "flag": "🇺🇸",
        "indices": USA_INDICES,
    },
    "France": {
        "name": "Frankreich",
        "flag": "🇫🇷",
        "indices": FRANCE_INDICES,
    },
    "Switzerland": {
        "name": "Schweiz",
        "flag": "🇨🇭",
        "indices": SWITZERLAND_INDICES,
    },
    "UK": {
        "name": "Großbritannien",
        "flag": "🇬🇧",
        "indices": UK_INDICES,
    },
    "Netherlands": {
        "name": "Niederlande",
        "flag": "🇳🇱",
        "indices": NETHERLANDS_INDICES,
    },
    "Nordics": {
        "name": "Skandinavien",
        "flag": "🇸🇪 🇩🇰 🇫🇮 🇳🇴",
        "indices": NORDIC_INDICES,
    },
    "Canada": {
        "name": "Kanada",
        "flag": "🇨🇦",
        "indices": CANADA_INDICES,
    },
    "Spain": {
        "name": "Spanien",
        "flag": "🇪🇸",
        "indices": SPAIN_INDICES,
    },
    "Italy": {
        "name": "Italien",
        "flag": "🇮🇹",
        "indices": ITALY_INDICES,
    },
    "Japan": {
        "name": "Japan",
        "flag": "🇯🇵",
        "indices": JAPAN_INDICES,
    },
}


def _get_index_config(index_name: str) -> dict:
    """Liefert die Konfiguration eines unterstützten Index."""

    normalized = index_name.casefold()

    for indices in (
        GERMANY_INDICES,
        USA_INDICES,
        FRANCE_INDICES,
        SWITZERLAND_INDICES,
        UK_INDICES,
        JAPAN_INDICES,
        NETHERLANDS_INDICES,
        NORDIC_INDICES,
        CANADA_INDICES,
        SPAIN_INDICES,
        ITALY_INDICES,
    ):
        for name, config in indices.items():
            if name.casefold() == normalized:
                return config

    raise ValueError(
        f"Unbekannter Index: {index_name}"
    )


def _constituents_path(index_name: str) -> Path:
    config = _get_index_config(index_name)
    return INDEX_CONSTITUENTS_DIR / f"{config['slug']}.csv"


def _snapshot_path(index_name: str) -> Path:
    config = _get_index_config(index_name)
    return (
        INDEX_CONSTITUENTS_DIR
        / f"{config['slug']}_market_snapshot.csv"
    )


def _inra_update_timestamp_path(
    index_name: str,
) -> Path:
    config = _get_index_config(index_name)
    return (
        INDEX_CONSTITUENTS_DIR
        / f"{config['slug']}_inra_update.txt"
    )


def get_index_inra_update_timestamp(
    index_name: str,
):
    path = _inra_update_timestamp_path(index_name)

    if not path.exists():
        return None

    value = path.read_text().strip()
    return value or None


def save_index_inra_update_timestamp(
    index_name: str,
    value: str,
) -> None:
    INDEX_CONSTITUENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    _inra_update_timestamp_path(
        index_name
    ).write_text(value)


def _extract_constituents(
    index_name: str,
    html: str,
) -> pd.DataFrame:
    """
    Extrahiert Mitglieder aus der Wikipedia-Seite.

    Die Tabellen unterscheiden sich zwischen DAX, MDAX und SDAX
    leicht. Deshalb werden Ticker- und Unternehmensspalte anhand
    ihrer Überschriften bestimmt.
    """

    config = _get_index_config(index_name)
    expected_members = config["members"]

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    ticker_headers = {
        "ticker",
        "ticker symbol",
        "symbol",
        "börsenkürzel",
        "kürzel",
    }

    company_headers = {
        "company",
        "company name",
        "name",
        "unternehmen",
    }

    candidates = []

    for table in soup.find_all("table"):
        first_row = table.find("tr")

        if first_row is None:
            continue

        headers = [
            cell.get_text(" ", strip=True)
            for cell in first_row.find_all(["th", "td"])
        ]

        normalized_headers = [
            header.casefold().strip()
            for header in headers
        ]

        ticker_index = next(
            (
                i
                for i, header in enumerate(normalized_headers)
                if header in ticker_headers
                or "ticker" in header
                or "börsenkürzel" in header
                or header == "symbol"
            ),
            None,
        )

        company_index = next(
            (
                i
                for i, header in enumerate(normalized_headers)
                if header in company_headers
                or header.startswith("company")
            ),
            None,
        )

        if (
            ticker_index is None
            or company_index is None
        ):
            continue

        rows = []

        for row in table.find_all("tr")[1:]:
            cells = [
                cell.get_text(" ", strip=True)
                for cell in row.find_all(["th", "td"])
            ]

            required_index = max(
                ticker_index,
                company_index,
            )

            if len(cells) <= required_index:
                continue

            ticker = cells[ticker_index].strip()
            company = cells[company_index].strip()

            if not ticker or not company:
                continue

            # Wikipedia liefert bei MDAX/SDAX überwiegend
            # deutsche Börsenkürzel ohne Yahoo-Xetra-Suffix.
            # Bereits qualifizierte Ticker (z. B. AIR.PA)
            # bleiben unverändert.
            if "." not in ticker:
                ticker = f"{ticker}.DE"

            rows.append(
                {
                    "Ticker": ticker,
                    "Name": company,
                }
            )

        members = (
            pd.DataFrame(rows)
            .drop_duplicates(
                subset=["Ticker"],
                keep="first",
            )
            .reset_index(drop=True)
        )

        if not members.empty:
            candidates.append(members)

        if len(members) == expected_members:
            return members

    sizes = sorted(
        {
            len(candidate)
            for candidate in candidates
        }
    )

    raise ValueError(
        f"Die {index_name}-Mitglieder konnten nicht vollständig "
        f"geladen werden. Erwartet: {expected_members}; "
        f"gefundene Kandidatengrößen: {sizes or 'keine'}."
    )


def _extract_onvista_page(
    html: str,
) -> pd.DataFrame:
    """Extrahiert die auf einer Onvista-Seite sichtbaren Indexmitglieder."""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    rows = []

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            first_cell = row.find(["th", "td"])

            if first_cell is None:
                continue

            first = first_cell.get_text(
                " ",
                strip=True,
            )

            parts = first.rsplit(" ", 1)

            if len(parts) != 2:
                continue

            name, wkn = parts

            if name.endswith(" WKN"):
                name = name[:-4].strip()

            if (
                len(wkn) != 6
                or not wkn.isalnum()
                or not name.strip()
            ):
                continue

            link = first_cell.find(
                "a",
                href=True,
            )

            isin = None

            if link is not None:
                href = link["href"]

                match = re.search(
                    r"-([A-Z]{2}[A-Z0-9]{9}[0-9])(?:$|[/?#])",
                    href,
                )

                if match:
                    isin = match.group(1)

            rows.append(
                {
                    "Name": name.strip(),
                    "WKN": wkn.upper(),
                    "ISIN": isin,
                }
            )

    return (
        pd.DataFrame(rows)
        .drop_duplicates(
            subset=["WKN"],
            keep="first",
        )
        .reset_index(drop=True)
    )


SDAX_YAHOO_TICKER_BY_WKN = {
    "554550": "1U1.DE",
    "510300": "ADV.DE",
    "A41YHG": "ACT0.DE",
    "A4214T": "1AST.DE",
    "510440": "AOF.DE",
    "510200": "BSL.DE",
    "A2H5Z1": "BFSA.DE",
    "541910": "COK.DE",
    "531370": "AFX.DE",
    "540390": "CWC.DE",
    "A2GS5D": "DMP.DE",
    "A1TNUT": "DBAN.DE",
    "748020": "DEQ.DE",
    "801900": "PBB.DE",
    "BEAU1Y": "DOU.DE",
    "555063": "DRW3.DE",
    "556520": "DUE.DE",
    "565970": "EUZ.DE",
    "A40ESU": "EIN.DE",
    "531350": "EKT.DE",
    "566480": "EVT.DE",
    "577220": "FIE.DE",
    "A255F1": "VH2.DE",
    "580060": "GFT.DE",
    "A1JXCV": "GYC.DE",
    "A161N3": "GLJ.DE",
    "A3H233": "HABA.DE",
    "731400": "HDD.DE",
    "A16140": "HFG.DE",
    "608340": "HBH.DE",
    "A1PHFF": "BOSS.DE",
    "549336": "HYQ.DE",
    "620010": "INH.DE",
    "575980": "IXX.DE",
    "JST400": "JST.DE",
    "621993": "JUN3.DE",
    "A0X9EJ": "KTN.DE",
    "629203": "KSB3.DE",
    "707400": "KWS.DE",
    "645000": "LPK.DE",
    "A0ETBQ": "MBB.DE",
    "A1MMCC": "ILM1.DE",
    "656990": "MLP.DE",
    "A2NB65": "MUX.DE",
    "A3H220": "NA9.DE",
    "A1H8BV": "NOEJ.DE",
    "593612": "OHB.DE",
    "BCK222": "OBCK.DE",
    "PAT1AG": "PAT.DE",
    "A0JBPG": "PNE3.DE",
    "746100": "TPE.DE",
    "A2AR94": "RDC.DE",
    "SAFH00": "SFQ.DE",
    "A3ENQ5": "1SXP.DE",
    "727650": "YSN.DE",
    "756857": "F3C.DE",
    "A2DGX9": "SLYG.DE",
    "723132": "SIX2.DE",
    "A0DJ6J": "S92.DE",
    "SPG100": "SPG.DE",
    "STAB1L": "STM.DE",
    "727413": "STO3.DE",
    "729700": "SZU.DE",
    "A2YN90": "TMV.DE",
    "A3CM2W": "TNIE.DE",
    "A0JL9W": "VBK.DE",
    "VNC001": "V1NC.DE",
    "766710": "VOS.DE",
    "805100": "WUW.DE",
    "WACK01": "WAC.DE",
}


SDAX_ONVISTA_PAGE_2 = [
    ("PVA TePla", "746100"),
    ("Redcare Pharmacy", "A2AR94"),
    ("SAF-HOLLAND", "SAFH00"),
    ("SCHOTT Pharma", "A3ENQ5"),
    ("secunet Security Networks", "727650"),
    ("SFC Energy", "756857"),
    ("Shelly Group", "A2DGX9"),
    ("Sixt (Stammaktie)", "723132"),
    ("SMA Solar", "A0DJ6J"),
    ("Springer Nature", "SPG100"),
    ("Stabilus", "STAB1L"),
    ("Sto", "727413"),
    ("Südzucker", "729700"),
    ("TeamViewer", "A2YN90"),
    ("Tonies", "A3CM2W"),
    ("Verbio", "A0JL9W"),
    ("Vincorion", "VNC001"),
    ("Vossloh", "766710"),
    ("W&W (Wüstenrot & Württembergische)", "805100"),
    ("Wacker Neuson", "WACK01"),
]


def _extract_onvista_constituents(
    index_name: str,
    html_pages,
) -> pd.DataFrame:
    """Führt die Onvista-Seiten eines Index zusammen."""

    config = _get_index_config(index_name)
    expected_members = config["members"]

    if isinstance(html_pages, str):
        html_pages = [html_pages]

    frames = [
        _extract_onvista_page(html)
        for html in html_pages
    ]

    frames = [
        frame
        for frame in frames
        if not frame.empty
    ]

    if not frames:
        raise ValueError(
            f"Keine {index_name}-Mitglieder von Onvista gefunden."
        )

    members = (
        pd.concat(
            frames,
            ignore_index=True,
        )
        .drop_duplicates(
            subset=["WKN"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    if (
        index_name.upper() == "SDAX"
        and len(members) == 50
    ):
        fallback = pd.DataFrame(
            SDAX_ONVISTA_PAGE_2,
            columns=["Name", "WKN"],
        )

        members = pd.concat(
            [members, fallback],
            ignore_index=True,
        ).drop_duplicates(
            subset=["WKN"],
            keep="first",
        ).reset_index(drop=True)

    if len(members) != expected_members:
        raise ValueError(
            f"Die {index_name}-Mitglieder konnten von Onvista "
            f"nicht vollständig geladen werden. "
            f"Erwartet: {expected_members}; "
            f"gefunden: {len(members)}."
        )

    if index_name.upper() == "SDAX":
        members["Ticker"] = members["WKN"].map(
            SDAX_YAHOO_TICKER_BY_WKN
        )

        missing_tickers = members.loc[
            members["Ticker"].isna(),
            ["Name", "WKN"],
        ]

        if not missing_tickers.empty:
            missing_text = ", ".join(
                f"{row.Name} ({row.WKN})"
                for row in missing_tickers.itertuples()
            )
            raise ValueError(
                "Für folgende SDAX-Mitglieder fehlt die "
                f"Yahoo-Ticker-Zuordnung: {missing_text}"
            )

    return members

    members["Name"] = members["Name"].str.replace(
        r"\\s+WKN$",
        "",
        regex=True,
    )

    if index_name.upper() == "MDAX":
        ticker_by_wkn = {
            "A0WMPJ": "AIXA.DE",
            "A2DW8Z": "AT1.DE",
            "AUM0V1": "AMV0.DE",
            "676650": "NDA.DE",
            "A2LQ88": "AG1.DE",
            "515870": "BC8.DE",
            "590900": "GBF.DE",
            "547030": "EVD.DE",
            "A2E4K4": "DHER.DE",
            "823212": "LHA.DE",
            "EVNK01": "EVK.DE",
            "566480": "EVT.DE",
            "577330": "FRA.DE",
            "A0Z2ZZ": "FNTN.DE",
            "578580": "FRE.DE",
            "A3E5D6": "FPE3.DE",
            "660200": "G1A.DE",
            "A0LD6E": "GXI.DE",
            "A13SX2": "HLE.DE",
            "A16140": "HFG.DE",
            "HAG000": "HAG.DE",
            "607000": "HOT.DE",
            "A1PHFF": "BOSS.DE",
            "A3E00M": "IOS.DE",
            "A2NB60": "JEN.DE",
            "621993": "JUN3.DE",
            "KSAG88": "SDF.DE",
            "KGX888": "KGX.DE",
            "KBX100": "KBX.DE",
            "633500": "KRN.DE",
            "547040": "LXS.DE",
            "630500": "DEZ.DE",
            "DWS100": "DWS.DE",
            "567710": "ELG.DE",
            "FTG111": "FTK.DE",
            "LEG111": "LEG.DE",
            "645290": "NEM.DE",
            "A0D655": "NDX1.DE",
            "PAG911": "P911.DE",
            "PAH003": "PAH3.DE",
            "696960": "PUM.DE",
            "701080": "RAA.DE",
            "A2AR94": "RDC.DE",
            "RENK73": "R3NK.DE",
            "861149": "RRTL.DE",
            "620200": "SZG.DE",
            "A12DM8": "G24.DE",
            "716563": "SRT3.DE",
            "SHA010": "SHA0.DE",
            "WAF300": "WAF.DE",
            "A113Q5": "STM.DE",
            "749399": "SAX.DE",
            "A1K023": "SMHN.DE",
            "830350": "TEG.DE",
            "TLX100": "TLX.DE",
            "A2YN90": "TMV.DE",
            "750000": "TKA.DE",
            "TKMS00": "TKMS.DE",
            "TRAT0N": "8TRA.DE",
            "TUAG50": "TUI1.DE",
            "508903": "UTDI.DE",
            "WCH888": "WCH.DE",
        }

        members["Ticker"] = members["WKN"].map(
            ticker_by_wkn
        )

        missing = members.loc[
            members["Ticker"].isna(),
            ["Name", "WKN"],
        ]

        if not missing.empty:
            raise ValueError(
                "Für folgende MDAX-Mitglieder fehlt "
                "die Yahoo-Ticker-Zuordnung: "
                + ", ".join(
                    missing["Name"].tolist()
                )
            )

        members = members[
            ["Ticker", "Name", "WKN", "ISIN"]
        ]

    return members


@lru_cache(maxsize=3)
def load_index_constituents(
    index_name: str,
) -> pd.DataFrame:
    """Lädt die aktuellen Mitglieder eines deutschen Index."""

    config = _get_index_config(index_name)

    response = requests.get(
        config["url"],
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    if config.get("source") == "onvista":
        html_pages = [
            response.text,
        ]

        if index_name.upper() == "SDAX":
            page_two_urls = [
                f"{config['url']}?page=2",
                f"{config['url']}?page=1",
            ]

            first_page = _extract_onvista_page(
                response.text
            )

            for page_two_url in page_two_urls:
                page_two_response = requests.get(
                    page_two_url,
                    timeout=30,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    },
                )
                page_two_response.raise_for_status()

                second_page = _extract_onvista_page(
                    page_two_response.text
                )

                combined_count = len(
                    pd.concat(
                        [
                            first_page,
                            second_page,
                        ],
                        ignore_index=True,
                    ).drop_duplicates(
                        subset=["WKN"]
                    )
                )

                if combined_count == config["members"]:
                    html_pages.append(
                        page_two_response.text
                    )
                    break

        return _extract_onvista_constituents(
            index_name,
            html_pages,
        )

    return _extract_constituents(
        index_name,
        response.text,
    )


def update_index_constituents(
    index_name: str,
) -> pd.DataFrame:
    """Aktualisiert den lokalen Mitglieder-Cache eines Index."""

    load_index_constituents.cache_clear()

    members = load_index_constituents(
        index_name
    ).copy()

    INDEX_CONSTITUENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    members.to_csv(
        _constituents_path(index_name),
        index=False,
    )

    return members


def get_index_constituents(
    index_name: str,
) -> pd.DataFrame:
    """Liest Indexmitglieder aus dem lokalen Cache."""

    config = _get_index_config(index_name)
    path = _constituents_path(index_name)

    if not path.exists():
        raise FileNotFoundError(
            f"Lokaler {index_name}-Mitglieder-Cache fehlt. "
            "Bitte zunächst aktualisieren."
        )

    members = pd.read_csv(path)

    required_columns = {
        "Ticker",
        "Name",
    }

    if not required_columns.issubset(
        members.columns
    ):
        raise ValueError(
            f"{index_name}-Mitglieder-Cache hat "
            "ein ungültiges Format."
        )

    if len(members) != config["members"]:
        raise ValueError(
            f"{index_name}-Mitglieder-Cache enthält nicht "
            f"{config['members']} Titel."
        )

    return members


def _performance_since(
    series: pd.Series,
    months: int = 0,
    years: int = 0,
):
    """Performance seit einem Kalenderstichtag."""

    series = series.dropna()

    if series.empty:
        return None

    end_date = series.index[-1]
    target_date = (
        end_date
        - pd.DateOffset(
            months=months,
            years=years,
        )
    )

    eligible = series[
        series.index <= target_date
    ]

    if eligible.empty:
        return None

    start_price = float(eligible.iloc[-1])
    end_price = float(series.iloc[-1])

    if start_price <= 0:
        return None

    return (
        end_price / start_price - 1
    ) * 100.0


def build_index_market_snapshot(
    index_name: str,
) -> pd.DataFrame:
    """Erzeugt den Markt-Snapshot aller Indexmitglieder."""

    import yfinance as yf

    members = get_index_constituents(
        index_name
    ).copy()

    tickers = members["Ticker"].tolist()

    prices = yf.download(
        tickers,
        period="max",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if prices.empty or "Close" not in prices:
        raise ValueError(
            f"{index_name}-Kurshistorien konnten "
            "nicht geladen werden."
        )

    close = prices["Close"]
    rows = []

    for _, member in members.iterrows():
        ticker = member["Ticker"]
        name = member["Name"]

        series = (
            close[ticker].dropna()
            if ticker in close.columns
            else pd.Series(dtype=float)
        )

        market_cap = None
        currency = None

        try:
            fast_info = yf.Ticker(ticker).fast_info
            market_cap = fast_info.get("marketCap")
            currency = fast_info.get("currency")
        except Exception:
            pass

        if series.empty:
            max_performance = None
            history_start = None
        else:
            first_price = float(series.iloc[0])
            last_price = float(series.iloc[-1])

            max_performance = (
                (last_price / first_price - 1) * 100.0
                if first_price > 0
                else None
            )

            history_start = series.index[0].date()

        rows.append(
            {
                "Ticker": ticker,
                "Name": name,
                "Marktkapitalisierung": market_cap,
                "Währung": currency,
                "1M": _performance_since(
                    series,
                    months=1,
                ),
                "3M": _performance_since(
                    series,
                    months=3,
                ),
                "6M": _performance_since(
                    series,
                    months=6,
                ),
                "1J": _performance_since(
                    series,
                    years=1,
                ),
                "3J": _performance_since(
                    series,
                    years=3,
                ),
                "5J": _performance_since(
                    series,
                    years=5,
                ),
                "Max": max_performance,
                "Historie seit": history_start,
            }
        )

    return pd.DataFrame(rows)


def update_index_market_snapshot(
    index_name: str,
) -> pd.DataFrame:
    """Aktualisiert den lokalen Markt-Snapshot eines Index."""

    snapshot = build_index_market_snapshot(
        index_name
    )

    INDEX_CONSTITUENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot.to_csv(
        _snapshot_path(index_name),
        index=False,
    )

    return snapshot


def get_index_market_snapshot(
    index_name: str,
) -> pd.DataFrame:
    """Liest einen Markt-Snapshot aus dem lokalen Cache."""

    config = _get_index_config(index_name)
    path = _snapshot_path(index_name)

    if not path.exists():
        raise FileNotFoundError(
            f"Lokaler {index_name}-Markt-Snapshot fehlt. "
            "Bitte zunächst aktualisieren."
        )

    snapshot = pd.read_csv(path)

    required_columns = {
        "Ticker",
        "Name",
        "Marktkapitalisierung",
        "Währung",
        "1M",
        "3M",
        "6M",
        "1J",
        "3J",
        "5J",
        "Max",
        "Historie seit",
    }

    if not required_columns.issubset(
        snapshot.columns
    ):
        raise ValueError(
            f"{index_name}-Markt-Snapshot hat "
            "ein ungültiges Format."
        )

    if len(snapshot) != config["members"]:
        raise ValueError(
            f"{index_name}-Markt-Snapshot enthält nicht "
            f"{config['members']} Titel."
        )

    return snapshot


# ------------------------------------------------------------------
# Rückwärtskompatibilität für bestehenden DAX-Code
# ------------------------------------------------------------------

def update_dax_constituents() -> pd.DataFrame:
    return update_index_constituents("DAX")


def get_dax_constituents() -> pd.DataFrame:
    return get_index_constituents("DAX")


def build_dax_market_snapshot() -> pd.DataFrame:
    return build_index_market_snapshot("DAX")


def update_dax_market_snapshot() -> pd.DataFrame:
    return update_index_market_snapshot("DAX")


def get_dax_market_snapshot() -> pd.DataFrame:
    return get_index_market_snapshot("DAX")


def get_ticker_index_memberships(
    ticker: str,
) -> list[dict]:
    """Ermittelt Indexzugehörigkeiten aus den lokalen Mitglieder-Caches."""

    memberships = []

    markets = (
        ("germany", GERMANY_INDICES),
        ("usa", USA_INDICES),
        ("france", FRANCE_INDICES),
        ("switzerland", SWITZERLAND_INDICES),
        ("uk", UK_INDICES),
        ("japan", JAPAN_INDICES),
        ("netherlands", NETHERLANDS_INDICES),
        ("nordics", NORDIC_INDICES),
    )

    for country_key, indices in markets:
        for index_name, config in indices.items():
            path = (
                INDEX_CONSTITUENTS_DIR
                / f"{config['slug']}.csv"
            )

            if not path.exists():
                continue

            try:
                members = pd.read_csv(
                    path,
                    usecols=["Ticker"],
                )
            except (ValueError, pd.errors.EmptyDataError):
                continue

            member_tickers = (
                members["Ticker"]
                .dropna()
                .astype(str)
                .str.casefold()
            )

            if ticker.casefold() in set(member_tickers):
                memberships.append(
                    {
                        "country": country_key,
                        "index": index_name,
                    }
                )

    return memberships


def update_missing_index_inra_scores(
    index_name: str,
    progress_callback=None,
) -> dict:
    """
    Ergänzt fehlende quantitative InRA-Daten eines Index.

    Verwendet ausschließlich load_company_snapshot().
    Kein Current Intelligence, keine qualitative KI-Recherche.
    """
    from utils.data_loader import (
        BENCHMARK_CACHE_PATH,
        load_benchmark_cache,
    )
    from utils.market_data import load_company_snapshot

    members = get_index_constituents(index_name)
    cache = load_benchmark_cache()

    existing = set()

    if (
        not cache.empty
        and "Ticker" in cache.columns
    ):
        existing = set(
            cache["Ticker"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
        )

    tickers = (
        members["Ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .tolist()
    )

    missing_tickers = [
        ticker
        for ticker in tickers
        if ticker not in existing
    ]

    total = len(missing_tickers)

    if total == 0:
        return {
            "total": 0,
            "updated": 0,
            "failed": [],
        }

    results = []
    failed = []

    for position, ticker in enumerate(
        missing_tickers,
        start=1,
    ):
        if progress_callback is not None:
            progress_callback(
                (position - 1) / total,
                f"{position}/{total} · {ticker} wird quantitativ bewertet …",
            )

        try:
            data = load_company_snapshot(ticker)
            results.append(data)

        except Exception as error:
            failed.append(
                {
                    "ticker": ticker,
                    "error": str(error),
                }
            )

    if results:
        new_rows = pd.DataFrame(results)

        if cache.empty:
            updated_cache = new_rows
        else:
            updated_cache = pd.concat(
                [
                    cache,
                    new_rows,
                ],
                ignore_index=True,
            )

        updated_cache.to_csv(
            BENCHMARK_CACHE_PATH,
            index=False,
        )

    if progress_callback is not None:
        progress_callback(
            1.0,
            "Quantitative InRA-Bewertungen aktualisiert.",
        )

    return {
        "total": total,
        "updated": len(results),
        "failed": failed,
    }
