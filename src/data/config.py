TEST_TICKERS = ["AAPL", "KO", "MSFT", "ASML.AS", "MC.PA", "SAP.DE", "SHEL.L", "7203.T", "0700.HK", "INFY.NS"]

COUNTRY_TO_REGION = {
    # North America
    "United States": "us",
    "Canada": "us",
    # Europe
    "Netherlands": "europe",
    "Germany": "europe",
    "France": "europe",
    "United Kingdom": "europe",
    "Switzerland": "europe",
    "Sweden": "europe",
    "Norway": "europe",
    "Denmark": "europe",
    "Italy": "europe",
    "Spain": "europe",
    "Belgium": "europe",
    "Finland": "europe",
    "Ireland": "europe",
    "Portugal": "europe",
    "Austria": "europe",
    "Greece": "europe",
    "Luxembourg": "europe",
    "Czech Republic": "europe",
    "Hungary": "europe",
    # Japan
    "Japan": "japan",
    # APAC
    "Australia": "apac",
    "New Zealand": "apac",
    "Hong Kong": "apac",
    "Singapore": "apac",
    # Emerging
    "China": "em",
    "India": "em",
    "Brazil": "em",
    "South Korea": "em",
    "Taiwan": "em",
    "South Africa": "em",
    "Mexico": "em",
    "Indonesia": "em",
    "Thailand": "em",
    "Malaysia": "em",
    "Philippines": "em",
    "Chile": "em",
    "Colombia": "em",
    "Peru": "em",
    "Turkey": "em",
    "Russia": "em",
    "Poland": "em",
    "Egypt": "em",
    "Saudi Arabia": "em",
    "UAE": "em",
    "Qatar": "em",
}


YF_TO_OPENFIGI_EXCHANGE = {
    "NMS": "UW",   # NASDAQ Global Select
    "NYQ": "UN",   # NYSE
    "NGM": "UW",   # NASDAQ Global Market
    "NCM": "UR",   # NASDAQ Capital Market
    "BTS": "US",   # OTC
    "LSE": "LN",   # London Stock Exchange
    "GER": "GY",   # Xetra
    "PAR": "FP",   # Euronext Paris
    "AMS": "NA",   # Euronext Amsterdam
    "JPX": "JT",   # Tokyo Stock Exchange
    "OSA": "JP",   # Osaka
    "HKG": "HK",   # Hong Kong
    "NSI": "IS",   # NSE India
    "SHG": "CG",   # Shanghai
    "SHE": "CS",   # Shenzhen
    "ASX": "AN",   # Australian Securities Exchange
    "TSX": "CT",   # Toronto
}