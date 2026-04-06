"""
analyze_portfolio.py (UPDATED für Phase 1)

Neue Features:
- Intelligente Kategorisierung (Name + ISIN + Type)
- Theme-Exposure-Aggregation
- OVERLAP-DETECTION
- Bessere UI-Elemente
"""

import json
from isin_mappings import get_isin_themes, CRYPTO_MAPPINGS

# ==================
# THEMATISCHE ZUORDNUNG
# ==================

# Fallback Name-basiert (für unbekannte Positionen)
THEME_MAP = {
    "msci world": {"us": 0.70, "tech": 0.25, "europe": 0.15, "em": 0.05},
    "msci world etf": {"us": 0.70, "tech": 0.25, "europe": 0.15, "em": 0.05},
    "vanguard ftse all-world": {"us": 0.62, "europe": 0.18, "em": 0.10, "tech": 0.20},
    "nasdaq": {"us": 0.98, "tech": 0.85},
    "nasdaq etf": {"us": 0.98, "tech": 0.85},
    "sp 500": {"us": 1.0, "tech": 0.30},
    "s&p 500": {"us": 1.0, "tech": 0.30},
    "emerging markets": {"em": 1.0, "asia": 0.70},
    "em etf": {"em": 1.0, "asia": 0.70},
    "bitcoin": {"crypto": 1.0},
    "ethereum": {"crypto": 1.0},
    "gold": {"rohstoffe": 1.0, "gold": 1.0},
    "gold etf": {"rohstoffe": 1.0, "gold": 1.0},
    "anleihen": {"anleihen": 1.0, "defensiv": 1.0},
    "bonds": {"anleihen": 1.0, "defensiv": 1.0},
    "immobilien": {"immobilien": 1.0},
    "real estate": {"immobilien": 1.0},
}


def _categorize_position(position_data):
    """
    Intelligente Kategorisierung einer Position.
    
    Input: {
        "name": "...",
        "isin": "IE00B4L5Y983",  # Optional
        "security_type": "ETF",   # Optional
        "weight": 13.5
    }
    
    Output: {theme: weight, ...}
    
    Priorität:
    1. ISIN-Lookup (genauest)
    2. Name in THEME_MAP
    3. Fuzzy-Match auf Keywords
    4. Fallback: {"unknown": 1.0}
    """
    
    name = position_data.get("name", "").strip()
    isin = position_data.get("isin", "").strip()
    security_type = position_data.get("security_type", "").upper()
    
    # TIER 1: ISIN-Lookup
    if isin:
        themes = get_isin_themes(isin)
        if themes:
            return themes
    
    # TIER 2: Exakter Name-Match
    name_lower = name.lower()
    if name_lower in THEME_MAP:
        return THEME_MAP[name_lower]
    
    # TIER 3: Security Type + Name Heuristic
    if security_type == "ETF":
        themes = _categorize_etf_by_name(name)
        if themes:
            return themes
    elif security_type == "STOCK":
        themes = _categorize_stock_by_name(name)
        if themes:
            return themes
    elif security_type == "CRYPTO":
        themes = _categorize_crypto_by_name(name)
        if themes:
            return themes
    
    # TIER 4: Fuzzy-Match mit Keywords
    themes = _fuzzy_match_theme(name)
    if themes:
        return themes
    
    # FALLBACK: Unknown
    return {"unknown": 1.0}


def _categorize_etf_by_name(name: str) -> dict:
    """
    ETF-spezifische Kategorisierung basierend auf Name.
    
    Beispiele:
    - "iShares MSCI World" → THEME_MAP["msci world"]
    - "Vanguard S&P 500" → THEME_MAP["s&p 500"]
    - "ARK Innovation" → {"tech": 0.9, "growth": 0.8}
    """
    name_lower = name.lower()
    
    # Partial matches
    if "msci world" in name_lower:
        return THEME_MAP["msci world"]
    if "vanguard" in name_lower and "world" in name_lower:
        return THEME_MAP["vanguard ftse all-world"]
    if "s&p 500" in name_lower or "sp500" in name_lower:
        return THEME_MAP["sp 500"]
    if "nasdaq" in name_lower:
        return THEME_MAP["nasdaq"]
    if "emerging" in name_lower or "schwellenl" in name_lower:
        return THEME_MAP["emerging markets"]
    if "gold" in name_lower:
        return THEME_MAP["gold etf"]
    if "anleihen" in name_lower or "bond" in name_lower:
        return THEME_MAP["anleihen"]
    if "immobilien" in name_lower or "real estate" in name_lower:
        return THEME_MAP["immobilien"]
    if "dividend" in name_lower:
        return {"dividend": 0.9, "defensiv": 0.5}
    if "ark" in name_lower:  # ARK Innovation Funds
        return {"tech": 0.9, "growth": 0.8, "innovation": 1.0}
    if "clean energy" in name_lower or "cleantech" in name_lower:
        return {"cleantech": 1.0, "energy": 0.8}
    
    return None


def _categorize_stock_by_name(name: str) -> dict:
    """Stock-spezifische Kategorisierung."""
    name_lower = name.lower()
    
    # Tech Megacap
    if name_lower in ["apple", "microsoft", "alphabet", "google", "meta", "nvidia", "tesla"]:
        return {"us": 1.0, "tech": 1.0, "megacap": 1.0}
    
    # European Tech
    if "asml" in name_lower:
        return {"europe": 1.0, "tech": 0.9, "semiconductor": 1.0}
    if "sap" in name_lower:
        return {"europe": 1.0, "tech": 0.9}
    
    # Financials
    if any(x in name_lower for x in ["bank", "berkshire", "jpmorgan", "goldman"]):
        return {"us": 0.8, "financials": 1.0}
    
    # Consumer
    if any(x in name_lower for x in ["coca", "pepsi", "nestle", "unilever", "procter"]):
        return {"consumer_staples": 1.0, "defensiv": 0.6}
    
    return None


def _categorize_crypto_by_name(name: str) -> dict:
    """Crypto-spezifische Kategorisierung."""
    name_lower = name.lower()
    
    if "bitcoin" in name_lower or "btc" in name_lower:
        return CRYPTO_MAPPINGS["bitcoin"]
    if "ethereum" in name_lower or "eth" in name_lower:
        return CRYPTO_MAPPINGS["ethereum"]
    
    return {"crypto": 1.0}


def _fuzzy_match_theme(name: str) -> dict:
    """
    Fallback: Keyword-basiertes Matching.
    
    Nutzt einfache Keywords um Position zu kategorisieren.
    """
    result = {}
    name_lower = name.lower()
    
    # Keywords für jedes Theme
    tech_keywords = ["tech", "nasdaq", "technology", "semiconductor", "software", "ai", "cloud", "semiconductor"]
    us_keywords = ["us", "usa", "united states", "s&p", "dow", "nasdaq", "spdr"]
    em_keywords = ["emerging", "schwellenländer", "em", "bric"]
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "krypto", "blockchain"]
    bond_keywords = ["anleihe", "bond", "renten", "fixed income", "treasuries"]
    gold_keywords = ["gold", "edelmetall", "rohstoff", "commodity"]
    dividend_keywords = ["dividend", "dividende"]
    
    # Check keywords
    for kw in tech_keywords:
        if kw in name_lower:
            result["tech"] = result.get("tech", 0) + 0.3
    
    for kw in us_keywords:
        if kw in name_lower:
            result["us"] = result.get("us", 0) + 0.3
    
    for kw in em_keywords:
        if kw in name_lower:
            result["em"] = result.get("em", 0) + 0.3
    
    for kw in crypto_keywords:
        if kw in name_lower:
            result["crypto"] = result.get("crypto", 0) + 0.4
    
    for kw in bond_keywords:
        if kw in name_lower:
            result["anleihen"] = 1.0
            result["defensiv"] = 0.8
            return result
    
    for kw in gold_keywords:
        if kw in name_lower:
            result["rohstoffe"] = 1.0
            result["gold"] = 1.0
            return result
    
    for kw in dividend_keywords:
        if kw in name_lower:
            result["dividend"] = 1.0
    
    # Normalisiere Gewichte
    if result:
        max_weight = max(result.values())
        return {k: min(v / max_weight, 1.0) for k, v in result.items()}
    
    return None


# ==================
# OVERLAP-DETECTION
# ==================

def _detect_overlaps(portfolio_data: dict, themes: dict) -> list:
    """
    Erkenne Überschneidungen zwischen Positionen.
    
    Beispiel:
    - MSCI World (70% US)
    - S&P 500 (100% US)
    - Apple (100% US)
    
    → Echtes US-Exposure ist ~85%, nicht 70+100+100
    
    Returns:
        list: [
            {
                "theme": "US",
                "positions": ["MSCI World", "S&P 500", "Apple"],
                "real_exposure": 85,
                "real_exposure_pct": "~85%",
                "recommendation": "..."
            },
            ...
        ]
    """
    overlaps = []
    
    # Für jedes Theme, das >15% Exposure hat
    for theme, total_exposure in sorted(themes.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True):
        
        if total_exposure < 15:  # Ignoriere kleine Themes
            continue
        
        # Finde alle Positionen die dieses Theme haben
        positions_with_theme = []
        
        for pos in portfolio_data['positions']:
            pos_themes = _categorize_position(pos)
            if theme in pos_themes:
                positions_with_theme.append({
                    "name": pos['name'],
                    "weight": pos['weight'],
                    "theme_weight": pos_themes[theme],
                    "contribution": pos['weight'] * pos_themes[theme]
                })
        
        # Wenn mehrere Positionen, könnte es Overlap sein
        if len(positions_with_theme) > 1:
            # Berechne "Real" Exposure (mit Overlap-Bereinigung)
            # Vereinfachte Formel: sqrt(sum of contributions)
            # Das berücksichtigt, dass nicht alles 100% überlappt
            
            overlap_indicator = sum(p['contribution'] for p in positions_with_theme)
            
            # Je mehr Positionen, desto weniger Overlap (Diversifikation)
            diversification_factor = 1.0 / (1.0 + len(positions_with_theme) * 0.1)
            real_exposure = overlap_indicator * diversification_factor
            
            # Nur als Overlap zählen wenn >2x gelistet
            if real_exposure < total_exposure * 0.7:
                positions_str = ", ".join([p['name'] for p in positions_with_theme[:3]])
                if len(positions_with_theme) > 3:
                    positions_str += f", +{len(positions_with_theme)-3} mehr"
                
                recommendation = _get_overlap_recommendation(
                    theme, 
                    real_exposure, 
                    len(positions_with_theme)
                )
                
                overlaps.append({
                    "theme": theme.upper(),
                    "positions": positions_str,
                    "real_exposure": round(real_exposure, 1),
                    "real_exposure_pct": f"~{round(real_exposure)}%",
                    "recommendation": recommendation
                })
    
    return overlaps


def _get_overlap_recommendation(theme: str, exposure: float, num_positions: int) -> str:
    """Generiere Empfehlungen basierend auf Overlap."""
    
    if exposure > 50:
        intensity = "sehr hoch"
    elif exposure > 35:
        intensity = "erhöht"
    else:
        intensity = "moderat"
    
    if theme.upper() == "US":
        return f"US-Exposure ist {intensity} ({exposure:.0f}%) – ist das bewusst oder Zufall? {num_positions} Positionen tragen dazu bei."
    elif theme.upper() == "TECH":
        return f"Tech-Exposure ist {intensity} ({exposure:.0f}%) – stark konzentriert auf wenige große Namen ({num_positions} Positionen)."
    elif theme.upper() == "CRYPTO":
        return f"Crypto-Exposure über {num_positions} Positionen verteilt – Klumpenrisiko beachten."
    else:
        return f"{theme} ist {intensity} ({exposure:.0f}%) verteilt auf {num_positions} Positionen."


# ==================
# MAIN ANALYZE FUNCTION (UPDATED)
# ==================

def analyze_portfolio(data):
    """
    Analysiere Portfolio mit Phase 1 Updates.
    
    Neue Felder:
    - themes: {theme: weight, ...} (Gesamt-Exposure)
    - overlaps: [...] (Erkannte Überschneidungen)
    - theme_details: [...] (Detail-Infos pro Theme)
    """
    
    total = data["total_value"]
    cash = data["cash"]
    positions = data["positions"]
    
    # --- BASISKENNZAHLEN (wie vorher) ---
    
    cash_ratio = round(cash / total * 100, 1) if total > 0 else 0
    sorted_positions = sorted(positions, key=lambda x: x.get("weight", 0), reverse=True)
    top3_weight = sum(p.get("weight", 0) for p in sorted_positions[:3])
    
    biggest_position = sorted_positions[0]["name"] if sorted_positions else "–"
    biggest_weight = sorted_positions[0].get("weight", 0) if sorted_positions else 0
    
    num_positions = len(positions)
    
    # --- NEUE THEME-LOGIK ---
    
    # 1. Kategorisiere alle Positionen
    position_themes = []
    for pos in positions:
        themes = _categorize_position(pos)
        position_themes.append({
            "position": pos,
            "themes": themes
        })
    
    # 2. Aggregiere Themes (gewichtet)
    themes = {}
    for pt in position_themes:
        pos_weight = pt['position'].get('weight', 0)
        for theme, theme_weight in pt['themes'].items():
            contribution = pos_weight * theme_weight
            themes[theme] = themes.get(theme, 0) + contribution
    
    # Runde auf 1 Dezimalstelle
    themes = {k: round(v, 1) for k, v in themes.items()}
    
    # 3. Erkenne Overlaps
    overlaps = _detect_overlaps(data, themes)
    
    # 4. Extrahiere wichtige Themes
    us_exposure = themes.get("us", 0)
    tech_exposure = themes.get("tech", 0)
    em_exposure = themes.get("em", 0)
    crypto_exposure = themes.get("crypto", 0)
    
    # --- BEWERTUNGEN (wie vorher, aber mit besseren Daten) ---
    
    concentration_level = "Niedrig"
    if top3_weight >= 70:
        concentration_level = "Hoch"
    elif top3_weight >= 50:
        concentration_level = "Mittel"
    
    if cash_ratio >= 20:
        cash_assessment = "Eher hoch"
    elif cash_ratio >= 10:
        cash_assessment = "Moderat"
    else:
        cash_assessment = "Niedrig"
    
    # --- DYNAMISCHE UI-ELEMENTE ---
    
    # Highlight basierend auf Overlaps
    if overlaps and overlaps[0]['real_exposure'] > 50:
        highlight_title = f"Großer Overlap in {overlaps[0]['theme']}: {overlaps[0]['real_exposure_pct']}"
        highlight_text = overlaps[0]['recommendation']
    elif tech_exposure >= 40:
        highlight_title = f"Geschätztes Tech-Exposure: ~{tech_exposure:.0f}%"
        highlight_text = (
            f"Durch Überschneidungen ist das echte Tech-Exposure ({tech_exposure:.0f}%) "
            "deutlich höher als die Einzelgewichte vermuten lassen."
        )
    elif top3_weight >= 70:
        highlight_title = "Hohe Konzentration auf wenige Bausteine"
        highlight_text = f"Top 3 dominieren mit {top3_weight:.0f}%. Gering divers."
    elif cash_ratio >= 20:
        highlight_title = "Hoher Cash-Anteil"
        highlight_text = f"{cash_ratio:.1f}% des Vermögens sind aktuell nicht investiert."
    else:
        highlight_title = "Solide Grundstruktur"
        highlight_text = "Portfolio wirkt nachvollziehbar aufgebaut. Schaue dir die Overlaps an."
    
    # Main Lever
    if overlaps and len(overlaps) > 0:
        main_lever = f"Overlap in {overlaps[0]['theme']} aufräumen – könnte einfach sein"
    elif tech_exposure >= 40:
        main_lever = f"Tech-Klumpenrisiko bewusst machen oder absichern (~{tech_exposure:.0f}%)"
    elif top3_weight >= 70:
        main_lever = "Konzentrationsrisiko reduzieren"
    elif cash_ratio >= 20:
        main_lever = "Cash-Rolle klären: Reserve, Gelegenheit oder Warteposition?"
    else:
        main_lever = "Portfolio-Logik schärfen und Zielbild definieren"
    
    # Risk Summary
    if overlaps:
        risk_summary = f"Overlap-Warnung: {overlaps[0]['theme']} zu konzentriert ({overlaps[0]['real_exposure_pct']})"
    elif tech_exposure >= 40 and us_exposure >= 60:
        risk_summary = f"Hohe Tech+US Konzentration ({tech_exposure:.0f}% Tech, {us_exposure:.0f}% US)"
    elif tech_exposure >= 40:
        risk_summary = f"Erhöhtes Tech-Klumpenrisiko (~{tech_exposure:.0f}%)"
    elif top3_weight >= 70:
        risk_summary = f"Hohe Konzentration auf Top 3 ({top3_weight:.0f}%)"
    else:
        risk_summary = "Moderates Gesamtrisiko mit Fokus auf Feintuning"
    
    # Next Question
    if overlaps:
        next_question = f"Warum hast du gleiche Themes in mehreren Positionen?"
    elif tech_exposure >= 40:
        next_question = "Ist das hohe Tech-Exposure eine bewusste Überzeugung?"
    elif cash_ratio >= 20:
        next_question = "Ist der Cash-Anteil geplant oder historisch gewachsen?"
    else:
        next_question = "Welche Rolle sollen deine größten Positionen langfristig spielen?"
    
    # --- RETURN COMPLETE ANALYSIS ---
    
    return {
        # Basiskennzahlen
        "cash_ratio": cash_ratio,
        "top3_weight": round(top3_weight, 1),
        "num_positions": num_positions,
        "biggest_position": biggest_position,
        "biggest_weight": round(biggest_weight, 1),
        
        # NEUE THEME-DATEN
        "us_exposure": round(us_exposure, 1),
        "tech_exposure": round(tech_exposure, 1),
        "em_exposure": round(em_exposure, 1),
        "crypto_exposure": round(crypto_exposure, 1),
        "themes": themes,  # ALL themes
        
        # NEUE OVERLAP-DATEN
        "overlaps": overlaps,  # List of detected overlaps
        
        # Bewertungen
        "concentration_level": concentration_level,
        "cash_assessment": cash_assessment,
        
        # UI-Elemente
        "highlight_title": highlight_title,
        "highlight_text": highlight_text,
        "main_lever": main_lever,
        "risk_summary": risk_summary,
        "next_question": next_question,
    }