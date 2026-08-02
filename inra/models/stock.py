from dataclasses import dataclass


@dataclass
class Stock:
    name: str
    ticker: str
    country: str = ""
    sector: str = ""
    industry: str = ""