"""
isin_mappings.py
================

Umfangreiche ISIN-zu-Theme-Mapping für ETFs und häufige Einzelaktien.

Format:
  ISIN → {theme: weight, ...}
  
Gewichte sind Prozentanteile (0-1.0):
  - "us": 0.70 bedeutet 70% US-Exposure
  - "tech": 0.25 bedeutet 25% Tech
"""

# ==================
# ETF ISINS (große, liquide ETFs)
# ==================

ETF_ISIN_MAPPINGS = {
    # MSCI WORLD FAMILY
    "IE00B4L5Y983": {  # iShares Core MSCI World UCITS ETF
        "us": 0.70,
        "europe": 0.15,
        "em": 0.05,
        "tech": 0.25,
        "healthcare": 0.12,
        "financials": 0.15,
    },
    "IE00EUNC4767": {  # iShares MSCI World UCITS ETF (Acc)
        "us": 0.70,
        "europe": 0.15,
        "em": 0.05,
        "tech": 0.25,
        "healthcare": 0.12,
        "financials": 0.15,
    },
    
    # S&P 500 / US LARGE CAP
    "IE00B0M63284": {  # iShares Core S&P 500 UCITS ETF
        "us": 1.0,
        "tech": 0.30,
        "healthcare": 0.13,
        "financials": 0.13,
    },
    "US0378331005": {  # SPDR S&P 500 ETF Trust (SPY)
        "us": 1.0,
        "tech": 0.30,
        "healthcare": 0.13,
        "financials": 0.13,
    },
    
    # NASDAQ / GROWTH / TECH
    "IE00B53SZB19": {  # iShares Nasdaq-100 UCITS ETF
        "us": 0.98,
        "tech": 0.85,
        "growth": 0.90,
    },
    "QQQ": {  # Invesco QQQ Trust (Nasdaq-100)
        "us": 0.98,
        "tech": 0.85,
        "growth": 0.90,
    },
    
    # EMERGING MARKETS
    "IE00B0M63477": {  # iShares MSCI EM UCITS ETF
        "em": 1.0,
        "asia": 0.70,
        "china": 0.40,
    },
    "IE00B27FSK26": {  # iShares Core MSCI EM IMI UCITS ETF
        "em": 1.0,
        "asia": 0.65,
    },
    
    # EUROPA
    "IE00B0M63623": {  # iShares Core DAX UCITS ETF
        "europe": 1.0,
        "germany": 1.0,
    },
    "IE00B1FZS798": {  # iShares STOXX Europe 600 UCITS ETF
        "europe": 1.0,
    },
    
    # ANLEIHEN
    "IE00B1FZS045": {  # iShares Core German Bonds UCITS ETF
        "anleihen": 1.0,
        "defensiv": 0.8,
    },
    "IE00B1FZS798": {  # iShares Global Corp Bond UCITS ETF
        "anleihen": 1.0,
        "defensiv": 0.6,
    },
    
    # ROHSTOFFE & GOLD
    "IE00B1FZS750": {  # iShares Gold Trust
        "rohstoffe": 1.0,
        "gold": 1.0,
        "defensiv": 0.7,
    },
    "IE00B432G283": {  # iShares Global Clean Energy UCITS ETF
        "rohstoffe": 0.5,
        "cleantech": 1.0,
        "energy": 0.8,
    },
    
    # IMMOBILIEN
    "IE00B0M63507": {  # iShares Global Property Yield UCITS ETF
        "immobilien": 1.0,
        "defensiv": 0.6,
    },
    
    # DIVIDEND / VALUE
    "IE00B0M6CP18": {  # iShares Global Dividend ETF
        "us": 0.50,
        "europe": 0.30,
        "value": 0.8,
        "dividend": 1.0,
    },
    
    # CRYPTO (wenn vorhanden)
    "ISIN_BITCOIN_ETF": {
        "crypto": 1.0,
        "bitcoin": 1.0,
    },
    "ISIN_ETHEREUM_ETF": {
        "crypto": 1.0,
        "ethereum": 1.0,
    },
    
    # ALL-IN-ONE WORLD
    "IE00B1YFVD51": {  # Vanguard FTSE All-World UCITS ETF
        "us": 0.62,
        "europe": 0.18,
        "em": 0.10,
        "developed": 0.90,
        "tech": 0.20,
    },
}

# ==================
# EINZELAKTIEN (große, häufige Positionen)
# ==================

STOCK_ISIN_MAPPINGS = {
    # MEGA-CAP TECH (USA)
    "US0378331005": {  # Apple
        "us": 1.0,
        "tech": 1.0,
        "megacap": 1.0,
    },
    "US5949181045": {  # Microsoft
        "us": 1.0,
        "tech": 1.0,
        "megacap": 1.0,
        "enterprise_software": 1.0,
    },
    "US0311621009": {  # Alphabet (Google)
        "us": 1.0,
        "tech": 1.0,
        "megacap": 1.0,
        "advertising": 0.8,
    },
    "US1018724399": {  # Coca-Cola
        "us": 1.0,
        "consumer_staples": 1.0,
        "dividend": 0.9,
    },
    "US5949181045": {  # Microsoft
        "us": 1.0,
        "tech": 1.0,
        "megacap": 1.0,
    },
    
    # SEMICONDUCTOR / GROWTH TECH
    "US67066G1040": {  # Nvidia
        "us": 1.0,
        "tech": 1.0,
        "semiconductor": 1.0,
        "growth": 1.0,
    },
    "US4592001014": {  # Intel
        "us": 1.0,
        "tech": 0.8,
        "semiconductor": 1.0,
    },
    
    # EUROPÄISCHE STOCKS
    "NL0000235190": {  # ASML (Netherlands)
        "europe": 1.0,
        "netherlands": 1.0,
        "tech": 0.9,
        "semiconductor_equipment": 1.0,
    },
    "DE0005140008": {  # Deutsche Telekom
        "europe": 1.0,
        "germany": 1.0,
        "telecom": 1.0,
    },
    "CH0012221716": {  # Nestle (Switzerland)
        "europe": 0.5,
        "consumer_staples": 1.0,
        "dividend": 0.9,
    },
    
    # EMERGING MARKETS
    "CNE1000003X7": {  # Alibaba (China)
        "em": 1.0,
        "china": 1.0,
        "tech": 1.0,
        "ecommerce": 1.0,
    },
    "INE040A01024": {  # Reliance Industries (India)
        "em": 1.0,
        "asia": 1.0,
        "energy": 0.8,
    },
}

# ==================
# CRYPTO
# ==================

CRYPTO_MAPPINGS = {
    "bitcoin": {"crypto": 1.0, "bitcoin": 1.0},
    "btc": {"crypto": 1.0, "bitcoin": 1.0},
    "ethereum": {"crypto": 1.0, "ethereum": 1.0},
    "eth": {"crypto": 1.0, "ethereum": 1.0},
    "solana": {"crypto": 1.0, "solana": 1.0},
    "cardano": {"crypto": 1.0, "cardano": 1.0},
}

# ==================
# HELPER FUNCTION
# ==================

def get_isin_themes(isin: str) -> dict:
    """
    Lookup ISIN in mappings.
    
    Returns:
        dict: {theme: weight, ...} oder None
    """
    if not isin:
        return None
    
    isin_clean = isin.upper().strip()
    
    # Check ETF first
    if isin_clean in ETF_ISIN_MAPPINGS:
        return ETF_ISIN_MAPPINGS[isin_clean]
    
    # Check Stocks
    if isin_clean in STOCK_ISIN_MAPPINGS:
        return STOCK_ISIN_MAPPINGS[isin_clean]
    
    # Check Crypto
    if isin_clean.lower() in CRYPTO_MAPPINGS:
        return CRYPTO_MAPPINGS[isin_clean.lower()]
    
    return None