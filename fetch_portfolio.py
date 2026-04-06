"""
Portfolio-Daten laden: entweder von der Scalable CLI oder aus einer lokalen JSON-Datei.

Nutzung:
    from fetch_portfolio import load_portfolio

    data = load_portfolio()
    # → {"total_value": ..., "cash": ..., "positions": [...]}

Sobald die Scalable CLI freigeschaltet ist:
    data = load_portfolio(source="cli")
"""

import json
import subprocess
import os


# ---------- Konfiguration ----------

SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), "sample_data.json")


def load_portfolio(source="auto"):
    """
    Lade Portfolio-Daten.

    source:
        "auto"   → versucht CLI, fällt auf sample_data.json zurück
        "cli"    → nur CLI (wirft Fehler, wenn CLI nicht verfügbar)
        "file"   → nur aus sample_data.json
        Dateipfad→ aus beliebiger JSON-Datei
    """
    if source == "file":
        return _load_from_file(SAMPLE_DATA_PATH)

    if source == "auto":
        if _cli_available():
            try:
                return _load_from_cli()
            except Exception as e:
                print(f"[fetch_portfolio] CLI fehlgeschlagen, nutze Datei: {e}")
                return _load_from_file(SAMPLE_DATA_PATH)
        else:
            return _load_from_file(SAMPLE_DATA_PATH)

    if source == "cli":
        return _load_from_cli()

    # Beliebiger Dateipfad
    if os.path.isfile(source):
        return _load_from_file(source)

    raise ValueError(f"Unbekannte Quelle: {source}")


# ---------- CLI ----------

def _cli_available():
    """Prüfe, ob die Scalable CLI installiert und eingeloggt ist."""
    try:
        result = subprocess.run(
            ["sc", "whoami"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _load_from_cli():
    """
    Lade Portfolio-Daten über die Scalable CLI.

    Ruft `sc broker overview --json` und `sc broker holdings --json` auf
    und transformiert das Ergebnis in das Coach-Format.
    """
    overview = _run_cli_command(["sc", "broker", "overview", "--json"])
    holdings = _run_cli_command(["sc", "broker", "holdings", "--json"])

    return _transform_cli_data(overview, holdings)


def _run_cli_command(cmd):
    """Führe einen CLI-Befehl aus und parse das JSON-Ergebnis."""
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"CLI-Befehl fehlgeschlagen: {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )

    return json.loads(result.stdout)


def _transform_cli_data(overview, holdings):
    """
    Transformiere CLI-Output in das Coach-Format.

    WICHTIG: Die genaue Struktur des CLI-Outputs ist noch nicht bekannt,
    da die Beta-Freischaltung aussteht. Die Feldnamen unten sind
    Platzhalter basierend auf der README-Dokumentation.

    Sobald du echten CLI-Output hast, passe die Feldnamen hier an.
    Tipp: Lauf `sc broker overview --json` und `sc broker holdings --json`
    und schau dir die Struktur an. Dann ersetzt du die Platzhalter.
    """

    # --- Gesamtwert und Cash ---
    # PLATZHALTER – an echten CLI-Output anpassen:
    total_value = overview.get("total_value") or overview.get("portfolio_value") or 0
    cash = overview.get("cash") or overview.get("cash_balance") or 0

    # --- Positionen ---
    # PLATZHALTER – an echten CLI-Output anpassen:
    raw_positions = holdings if isinstance(holdings, list) else holdings.get("positions", [])

    positions = []
    invested_value = total_value - cash if total_value > 0 else 1  # Division by zero vermeiden

    for item in raw_positions:
        # PLATZHALTER – Feldnamen anpassen:
        name = item.get("name") or item.get("instrument_name") or item.get("title") or "Unbekannt"
        value = item.get("value") or item.get("current_value") or item.get("market_value") or 0

        weight = round((value / total_value) * 100, 1) if total_value > 0 else 0

        positions.append({
            "name": name,
            "weight": weight,
        })

    return {
        "total_value": total_value,
        "cash": cash,
        "positions": positions,
    }


# ---------- Datei ----------

def _load_from_file(path):
    """Lade Portfolio-Daten aus einer JSON-Datei."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- Standalone-Test ----------

if __name__ == "__main__":
    data = load_portfolio(source="auto")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nQuelle: {'CLI' if _cli_available() else 'Datei'}")
    print(f"Positionen: {len(data['positions'])}")
    print(f"Gesamtwert: {data['total_value']:,.0f} €")
