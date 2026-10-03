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
    "Insurance - Diversified": "Diversifizierte Versicherungen",
    "Internet Retail": "Onlinehandel",
    "Other Industrial Metals & Mining": "Industriemetalle & Bergbau",
    "Solar": "Solarenergie",
    "Oil & Gas E&P": "Öl- & Gasexploration",
    "Communication Equipment": "Kommunikationsausrüstung",
    "Telecom Services": "Telekommunikation",
    "Airlines": "Fluggesellschaften",
    "Engineering & Construction": "Ingenieurwesen & Bau",
    "Asset Management": "Vermögensverwaltung",
    "Auto Manufacturers": "Automobilhersteller",
    "Auto Parts": "Automobilzulieferer",
    "Banks - Diversified": "Diversifizierte Banken",
    "Banks - Regional": "Regionalbanken",
    "Building Materials": "Baustoffe",
    "Capital Markets": "Kapitalmärkte",
    "Chemicals": "Chemie",
    "Computer Hardware": "Computerhardware",
    "Consumer Electronics": "Unterhaltungselektronik",
    "Copper": "Kupfer",
    "Credit Services": "Kreditdienstleistungen",
    "Diagnostics & Research": "Diagnostik & Forschung",
    "Discount Stores": "Discount-Einzelhandel",
    "Drug Manufacturers - Specialty & Generic": "Spezial- & Generikapharma",
    "Electrical Equipment": "Elektroausrüstung",
    "Farm & Heavy Construction Machinery": "Land- & Baumaschinen",
    "Financial Exchanges & Data": "Finanzbörsen & Daten",
    "Footwear & Accessories": "Schuhe & Accessoires",
    "Gambling": "Glücksspiel",
    "Gold": "Gold",
    "Household & Personal Products": "Haushalts- & Körperpflegeprodukte",
    "Industrial Metals & Mining": "Industriemetalle & Bergbau",
    "Insurance - Reinsurance": "Rückversicherung",
    "Integrated Freight & Logistics": "Fracht & Logistik",
    "Internet Content & Information": "Internetinhalte & Informationsdienste",
    "Luxury Goods": "Luxusgüter",
    "Medical Care Facilities": "Gesundheitseinrichtungen",
    "Medical Devices": "Medizintechnik",
    "Medical Instruments & Supplies": "Medizinische Instrumente & Ausrüstung",
    "Oil & Gas Integrated": "Integrierte Öl- & Gasunternehmen",
    "Other Precious Metals & Mining": "Edelmetalle & Bergbau",
    "Packaged Foods": "Verpackte Lebensmittel",
    "REIT - Industrial": "REIT – Industrieimmobilien",
    "REIT - Retail": "REIT – Einzelhandelsimmobilien",
    "REIT - Specialty": "REIT – Spezialimmobilien",
    "Railroads": "Eisenbahnen",
    "Real Estate Services": "Immobiliendienstleistungen",
    "Restaurants": "Restaurants",
    "Semiconductor Equipment": "Halbleiterausrüstung",
    "Semiconductor Equipment & Materials": "Halbleiterausrüstung & Materialien",
    "Software": "Software",
    "Software - Application": "Anwendungssoftware",
    "Software Infrastructure": "Infrastruktursoftware",
    "Specialty Business Services": "Spezialisierte Unternehmensdienstleistungen",
    "Specialty Chemicals": "Spezialchemie",
    "Thermal Coal": "Kraftwerkskohle",
    "Travel Services": "Reisedienstleistungen",
    "Uranium": "Uran",
    "Utilities - Diversified": "Diversifizierte Versorger",
    "Utilities - Independent Power Producers": "Unabhängige Stromerzeuger",
    "Utilities - Regulated Electric": "Regulierte Stromversorger",
    "Utilities - Renewable": "Erneuerbare Energien",
    "Waste Management": "Abfallwirtschaft",
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
