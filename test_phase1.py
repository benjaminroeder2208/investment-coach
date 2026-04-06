"""
test_phase1.py
==============

Test Phase 1 Features:
- Theme Kategorisierung
- Overlap Detection
- Analyse Quality
"""

import json
from analyze_portfolio import analyze_portfolio

# Test-Portfolios
TEST_PORTFOLIOS = {
    "high_tech": {
        "name": "High Tech Enthusiast",
        "description": "MSCI + Nasdaq + Apple + Nvidia = 2x Tech+US",
        "total_value": 100000,
        "cash": 5000,
        "positions": [
            {
                "name": "iShares MSCI World",
                "weight": 15,
                "isin": "IE00B4L5Y983",
                "security_type": "ETF"
            },
            {
                "name": "Nasdaq 100 ETF",
                "weight": 12,
                "isin": "IE00B53SZB19",
                "security_type": "ETF"
            },
            {
                "name": "Apple Inc.",
                "weight": 8,
                "isin": "US0378331005",
                "security_type": "STOCK"
            },
            {
                "name": "Nvidia Corp.",
                "weight": 7,
                "isin": "US67066G1040",
                "security_type": "STOCK"
            },
            {
                "name": "Microsoft",
                "weight": 6,
                "isin": "US5949181045",
                "security_type": "STOCK"
            },
            {
                "name": "Vanguard FTSE All-World",
                "weight": 10,
                "isin": "IE00B1YFVD51",
                "security_type": "ETF"
            },
            {
                "name": "Cash",
                "weight": 5,
            }
        ]
    },
    
    "passive_investor": {
        "name": "Passive Investor",
        "description": "Nur ETFs, diversifiziert",
        "total_value": 100000,
        "cash": 10000,
        "positions": [
            {
                "name": "iShares MSCI World",
                "weight": 40,
                "isin": "IE00B4L5Y983",
                "security_type": "ETF"
            },
            {
                "name": "Emerging Markets ETF",
                "weight": 20,
                "isin": "IE00B0M63477",
                "security_type": "ETF"
            },
            {
                "name": "Anleihen ETF",
                "weight": 15,
                "isin": "IE00B1FZS045",
                "security_type": "ETF"
            },
            {
                "name": "Gold ETF",
                "weight": 5,
                "isin": "IE00B1FZS750",
                "security_type": "ETF"
            },
            {
                "name": "Cash",
                "weight": 10,
            }
        ]
    },
    
    "concentrated_bet": {
        "name": "Concentrated Bet",
        "description": "Top 3 sind 65%",
        "total_value": 100000,
        "cash": 5000,
        "positions": [
            {
                "name": "Apple",
                "weight": 25,
                "isin": "US0378331005",
                "security_type": "STOCK"
            },
            {
                "name": "Tesla Inc.",
                "weight": 20,
                "isin": "US88160R1014",
                "security_type": "STOCK"
            },
            {
                "name": "Nvidia",
                "weight": 20,
                "isin": "US67066G1040",
                "security_type": "STOCK"
            },
            {
                "name": "Cash",
                "weight": 5,
            }
        ]
    }
}

def test_portfolio(portfolio_dict):
    """Teste ein Portfolio und gib Analyse aus."""
    
    print(f"\n{'='*70}")
    print(f"📊 PORTFOLIO: {portfolio_dict['name']}")
    print(f"{'='*70}")
    print(f"Description: {portfolio_dict['description']}")
    
    # Analyse
    analysis = analyze_portfolio(portfolio_dict)
    
    # Output formatieren
    print(f"\n🎯 KENNZAHLEN:")
    print(f"  Total Value: €{portfolio_dict['total_value']:,}")
    print(f"  Cash: {analysis['cash_ratio']:.1f}%")
    print(f"  Positionen: {analysis['num_positions']}")
    print(f"  Top 3: {analysis['top3_weight']:.1f}%")
    
    print(f"\n🌍 THEME-EXPOSURE:")
    for theme, exposure in sorted(analysis['themes'].items(), 
                                  key=lambda x: x[1], 
                                  reverse=True):
        if exposure > 5:
            print(f"  • {theme.title():20s}: {exposure:6.1f}%")
    
    print(f"\n⚠️ OVERLAPS ERKANNT:")
    if analysis['overlaps']:
        for overlap in analysis['overlaps']:
            print(f"  • {overlap['theme']:10s}: {overlap['real_exposure_pct']:>6s} (Positionen: {overlap['positions']})")
            print(f"    → {overlap['recommendation']}")
    else:
        print(f"  Keine signifikanten Overlaps erkannt.")
    
    print(f"\n💡 INSIGHTS:")
    print(f"  Highlight: {analysis['highlight_title']}")
    print(f"  → {analysis['highlight_text']}")
    print(f"\n  Main Lever: {analysis['main_lever']}")
    print(f"  Risk: {analysis['risk_summary']}")
    print(f"  Next?: {analysis['next_question']}")
    
    return analysis


def main():
    """Teste alle Test-Portfolios."""
    
    for key, portfolio in TEST_PORTFOLIOS.items():
        test_portfolio(portfolio)
    
    print(f"\n{'='*70}")
    print(f"✅ ALLE TESTS ABGESCHLOSSEN")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()