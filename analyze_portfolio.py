"""
Portfolio-Analyse-Modul für den Investment Coach.

Berechnet Kennzahlen, erkennt thematische Überschneidungen
und generiert dynamische UI-Elemente (Highlights, Hebel, Risiken).
"""


# ---------- Thematische Zuordnung ----------
# Jede Position kann anteilig mehreren Themen zugeordnet werden.
# Die Werte sind Schätzungen für typische ETF-/Positionstypen.

THEME_MAP = {
    "msci world etf": {"us": 0.70, "tech": 0.25, "europe": 0.15, "em": 0.05},
    "nasdaq etf": {"us": 0.98, "tech": 0.85},
    "emerging markets etf": {"em": 1.0, "asia": 0.70},
    "einzelaktien tech": {"us": 0.80, "tech": 1.0},
    "bitcoin": {"crypto": 1.0},
    "gold etf": {"rohstoffe": 1.0},
    "gold": {"rohstoffe": 1.0},
    "anleihen etf": {"anleihen": 1.0, "defensiv": 1.0},
    "immobilien etf": {"immobilien": 1.0},
}


def _get_theme_exposure(positions):
    """Berechne das gewichtete Themen-Exposure über alle Positionen."""
    themes = {}
    unmapped = []

    for pos in positions:
        name_lower = pos["name"].lower().strip()
        weight = pos["weight"]

        mapping = THEME_MAP.get(name_lower)

        if mapping is None:
            # Versuche Teilmatch
            mapping = _fuzzy_match_theme(name_lower)

        if mapping:
            for theme, factor in mapping.items():
                themes[theme] = themes.get(theme, 0) + round(weight * factor, 1)
        else:
            unmapped.append(pos["name"])

    return themes, unmapped


def _fuzzy_match_theme(name):
    """Einfacher Keyword-basierter Fallback für unbekannte Positionen."""
    result = {}

    tech_keywords = ["tech", "nasdaq", "technology", "semiconductor", "software", "ai "]
    us_keywords = ["us", "s&p", "dow", "nasdaq", "america"]
    em_keywords = ["emerging", "schwellenl"]
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "krypto"]
    bond_keywords = ["anleihe", "bond", "renten", "fixed income"]
    gold_keywords = ["gold", "rohstoff", "commodity"]

    for kw in tech_keywords:
        if kw in name:
            result["tech"] = result.get("tech", 0.8)
            break

    for kw in us_keywords:
        if kw in name:
            result["us"] = result.get("us", 0.8)
            break

    for kw in em_keywords:
        if kw in name:
            result["em"] = result.get("em", 0.9)
            break

    for kw in crypto_keywords:
        if kw in name:
            result["crypto"] = result.get("crypto", 1.0)
            break

    for kw in bond_keywords:
        if kw in name:
            result["anleihen"] = result.get("anleihen", 1.0)
            result["defensiv"] = result.get("defensiv", 1.0)
            break

    for kw in gold_keywords:
        if kw in name:
            result["rohstoffe"] = result.get("rohstoffe", 1.0)
            break

    return result if result else None


def analyze_portfolio(data):
    """Hauptfunktion: Portfolio analysieren und alle Kennzahlen zurückgeben."""
    total = data["total_value"]
    cash = data["cash"]
    positions = data["positions"]

    # --- Basiskennzahlen ---
    cash_ratio = round(cash / total * 100, 1)

    sorted_positions = sorted(positions, key=lambda x: x["weight"], reverse=True)
    top3_weight = sum(p["weight"] for p in sorted_positions[:3])

    biggest_position = sorted_positions[0]["name"] if sorted_positions else "–"
    biggest_weight = sorted_positions[0]["weight"] if sorted_positions else 0

    num_positions = len(positions)

    # --- Themen-Exposure ---
    themes, unmapped_positions = _get_theme_exposure(positions)

    us_exposure = round(themes.get("us", 0), 1)
    tech_exposure = round(themes.get("tech", 0), 1)
    em_exposure = round(themes.get("em", 0), 1)

    # --- Bewertungen ---
    position_names = [p["name"].lower() for p in positions]

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

    has_unknown_bucket = any("sonstige" in name for name in position_names)
    has_tech_overlap = tech_exposure >= 40
    has_us_concentration = us_exposure >= 60

    # --- Dynamischer Highlight-Block ---
    if has_tech_overlap:
        highlight_title = f"Geschätztes Tech-Exposure: ~{tech_exposure}%"
        highlight_text = (
            "Durch Überschneidungen zwischen MSCI World, Nasdaq und Tech-Einzelaktien "
            "ist das reale Tech-Exposure deutlich höher als die Einzelgewichte vermuten lassen."
        )
    elif top3_weight >= 70:
        highlight_title = "Hohe Konzentration auf wenige Bausteine"
        highlight_text = (
            "Die Top-3-Positionen dominieren das Portfolio stark. "
            "Dadurch ist die tatsächliche Diversifikation geringer, als sie auf den ersten Blick wirkt."
        )
    elif cash_ratio >= 20:
        highlight_title = "Hoher Cash-Anteil"
        highlight_text = (
            "Ein spürbarer Teil des Vermögens ist aktuell nicht investiert. "
            "Das erhöht die Flexibilität, kann aber langfristig den Vermögensaufbau bremsen."
        )
    elif has_unknown_bucket:
        highlight_title = "Unklare Rolle des 'Sonstige'-Blocks"
        highlight_text = (
            "Ein Teil des Portfolios ist aktuell nicht sauber einordenbar. "
            "Gerade dieser Block kann Diversifikation bringen oder Risiken unbemerkt verstärken."
        )
    else:
        highlight_title = "Solide Grundstruktur mit Prüfbedarf im Detail"
        highlight_text = (
            "Das Portfolio wirkt grundsätzlich nachvollziehbar aufgebaut. "
            "Die spannendsten Hebel liegen in Feingewichtung, Klarheit und bewusster Strategie."
        )

    # --- Wichtigster Hebel ---
    if has_tech_overlap:
        main_lever = f"Tech-Klumpenrisiko entschärfen (geschätzt ~{tech_exposure}% Tech-Exposure)"
    elif top3_weight >= 70:
        main_lever = "Konzentrationsrisiko reduzieren oder bewusst absichern"
    elif cash_ratio >= 20:
        main_lever = "Cash-Rolle sauber definieren: Reserve, Notgroschen oder Warteposition"
    elif has_unknown_bucket:
        main_lever = "'Sonstige' konkret aufschlüsseln und strategisch einordnen"
    else:
        main_lever = "Portfolio-Logik schärfen und Zielbild klarer definieren"

    # --- Risikoeinschätzung ---
    if has_tech_overlap and has_us_concentration:
        risk_summary = (
            f"Starkes Klumpenrisiko: ~{us_exposure}% US-Exposure, "
            f"~{tech_exposure}% Tech-Exposure durch Überschneidungen"
        )
    elif has_tech_overlap:
        risk_summary = f"Erhöhtes Tech-Klumpenrisiko (~{tech_exposure}% effektives Exposure)"
    elif top3_weight >= 70:
        risk_summary = "Erhöhte Konzentration auf wenige Positionen"
    elif cash_ratio >= 20:
        risk_summary = "Niedrigeres Marktrisiko, aber höhere Opportunitätskosten"
    else:
        risk_summary = "Moderates Gesamtrisiko mit Fokus auf Feintuning"

    # --- Nächste sinnvolle Frage ---
    if has_unknown_bucket:
        next_question = "Was steckt konkret in 'Sonstige'?"
    elif has_tech_overlap:
        next_question = "Ist das hohe Tech-Exposure eine bewusste Überzeugung oder eher zufällig entstanden?"
    elif cash_ratio >= 20:
        next_question = "Ist der Cash-Anteil bewusst geplant oder eher historisch gewachsen?"
    elif top3_weight >= 70:
        next_question = "Ist die Konzentration auf wenige Positionen eine bewusste Entscheidung?"
    else:
        next_question = "Welche Rolle sollen die größten Positionen langfristig spielen?"

    return {
        # Basiskennzahlen
        "cash_ratio": cash_ratio,
        "top3_weight": top3_weight,
        "num_positions": num_positions,
        "biggest_position": biggest_position,
        "biggest_weight": biggest_weight,
        # Themen-Exposure
        "us_exposure": us_exposure,
        "tech_exposure": tech_exposure,
        "em_exposure": em_exposure,
        "themes": themes,
        "unmapped_positions": unmapped_positions,
        # Bewertungen
        "concentration_level": concentration_level,
        "cash_assessment": cash_assessment,
        "has_unknown_bucket": has_unknown_bucket,
        "has_tech_overlap": has_tech_overlap,
        "has_us_concentration": has_us_concentration,
        # UI-Elemente
        "highlight_title": highlight_title,
        "highlight_text": highlight_text,
        "main_lever": main_lever,
        "risk_summary": risk_summary,
        "next_question": next_question,
    }
