SECTOR_DE = {
    "Basic Materials": "Grundstoffe",
    "Communication Services": "Kommunikationsdienste",
    "Consumer Cyclical": "Zyklische Konsumgüter",
    "Consumer Defensive": "Basiskonsumgüter",
    "Energy": "Energie",
    "Financial Services": "Finanzdienstleistungen",
    "Healthcare": "Gesundheitswesen",
    "Industrials": "Industrie",
    "Real Estate": "Immobilien",
    "Technology": "Technologie",
    "Utilities": "Versorger",
}

INDUSTRY_DE = {
    "Beverages - Non-Alcoholic": "Alkoholfreie Getränke",
    "Software - Infrastructure": "Infrastruktursoftware",
    "Semiconductors": "Halbleiter",
    "Steel": "Stahl",
    "Specialty Industrial Machinery": "Spezialmaschinenbau",
    "Drug Manufacturers - General": "Pharmahersteller",
    "Aerospace & Defense": "Luft- und Raumfahrt & Verteidigung",
    "Electrical Equipment & Parts": "Elektroausrüstung & Komponenten",
    "Marine Shipping": "Seeschifffahrt",
    "Information Technology Services": "IT-Dienstleistungen",
    "REIT - Healthcare Facilities": "REIT – Gesundheitseinrichtungen",
    "Financial Data & Stock Exchanges": "Finanzdaten & Börsen",
    "Solar": "Solarenergie",
    "Oil & Gas E&P": "Öl- & Gasexploration",
    "Communication Equipment": "Kommunikationsausrüstung",
    "Telecom Services": "Telekommunikation",
    "Airlines": "Fluggesellschaften",
    "Engineering & Construction": "Ingenieurwesen & Bau",
}

COUNTRY_DE = {
    "United States": ("Vereinigte Staaten", "🇺🇸"),
    "Germany": ("Deutschland", "🇩🇪"),
    "France": ("Frankreich", "🇫🇷"),
    "United Kingdom": ("Vereinigtes Königreich", "🇬🇧"),
    "Switzerland": ("Schweiz", "🇨🇭"),
    "Austria": ("Österreich", "🇦🇹"),
    "Netherlands": ("Niederlande", "🇳🇱"),
    "Belgium": ("Belgien", "🇧🇪"),
    "Denmark": ("Dänemark", "🇩🇰"),
    "Sweden": ("Schweden", "🇸🇪"),
    "Norway": ("Norwegen", "🇳🇴"),
    "Finland": ("Finnland", "🇫🇮"),
    "Italy": ("Italien", "🇮🇹"),
    "Spain": ("Spanien", "🇪🇸"),
    "Portugal": ("Portugal", "🇵🇹"),
    "Ireland": ("Irland", "🇮🇪"),
    "Canada": ("Kanada", "🇨🇦"),
    "Mexico": ("Mexiko", "🇲🇽"),
    "Brazil": ("Brasilien", "🇧🇷"),
    "Australia": ("Australien", "🇦🇺"),
    "China": ("China", "🇨🇳"),
    "Hong Kong": ("Hongkong", "🇭🇰"),
    "Japan": ("Japan", "🇯🇵"),
    "Taiwan": ("Taiwan", "🇹🇼"),
    "South Korea": ("Südkorea", "🇰🇷"),
    "Singapore": ("Singapur", "🇸🇬"),
    "India": ("Indien", "🇮🇳"),
    "South Africa": ("Südafrika", "🇿🇦"),
}


def localize_sector(value):
    if not value:
        return "–"
    return SECTOR_DE.get(value, value)


def localize_industry(value):
    if not value:
        return "–"
    return INDUSTRY_DE.get(value, value)


def localize_country(value):
    if not value:
        return "–"

    localized = COUNTRY_DE.get(value)

    if localized is None:
        return value

    name, flag = localized
    return f"{flag} {name}"


def get_country_display(value):
    if not value:
        return {
            "name": "–",
            "flag": "",
        }

    localized = COUNTRY_DE.get(value)

    if localized is None:
        return {
            "name": value,
            "flag": "",
        }

    name, flag = localized

    return {
        "name": name,
        "flag": flag,
    }
