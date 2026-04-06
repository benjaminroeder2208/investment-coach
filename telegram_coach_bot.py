#!/usr/bin/env python3
"""
Investment Coach – Telegram Bot (Enhanced)
- Viele Commands
- Bessere Formatierung
- Intelligente Antworten mit Coach
- Chat-Kontext & Gedächtnis
"""

import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

from analyze_portfolio import analyze_portfolio
from coach_core import ask_coach

# ==================
# CONFIG
# ==================

TELEGRAM_BOT_TOKEN = "7723305194:AAFC29xQEWtDonLnWMbsGrIJZ01ktOvIXDs"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================
# LADE DEMO-DATEN
# ==================

def load_portfolio_data():
    """Lade Portfolio-Daten (immer frisch)"""
    try:
        with open("sample_data.json", "r") as f:
            portfolio = json.load(f)
        analysis = analyze_portfolio(portfolio)
        return portfolio, analysis
    except Exception as e:
        logger.error(f"Fehler beim Laden: {e}")
        return None, None

# ==================
# COMMAND HANDLERS
# ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Command"""
    await update.message.reply_text(
        "👋 *Willkommen beim Investment Coach!*\n\n"
        "Ich analysiere dein Portfolio und gebe dir intelligente Empfehlungen.\n\n"
        "📚 *Probiere diese Commands:*\n"
        "/portfolio – Dein Portfolio\n"
        "/top3 – Top 3 Positionen\n"
        "/risks – Risikoanalyse\n"
        "/performance – Gewinn/Verlust\n"
        "/diversification – Diversifizierung\n"
        "/transactions – Letzte Transaktionen\n"
        "/analyze – Vollständige Analyse\n"
        "/help – Alle Commands\n\n"
        "💡 *Oder frag einfach:*\n"
        "\"Wie ist mein Portfolio aufgestellt?\"\n"
        "\"Wo sind Risiken?\"\n"
        "\"Was sollte ich tun?\"",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help Command"""
    help_text = """📚 *Investment Coach – Alle Commands*

*Portfolio-Übersicht:*
/portfolio – Gesamtwert, Cash, Positionen
/top3 – Top 3 Positionen
/top10 – Top 10 Positionen

*Analysen:*
/risks – Risikoanalyse & Konzentrationen
/performance – Gewinn/Verlust Statistik
/diversification – Diversifizierungs-Score
/sectors – Sektor-Verteilung
/regions – Regionale Verteilung
/assets – Asset-Klassen Verteilung

*Detailiert:*
/transactions – Letzte Transaktionen
/analyze – Vollständige Portfolio-Analyse
/insights – Wichtigste Erkenntnisse

*Hilfreich:*
/refresh – Daten neu laden
/status – Bot Status
/help – Diese Hilfe

*Chat:*
Schreib einfach eine Frage und der Coach antwortet!
Beispiele:
• \"Wie ist mein Portfolio aufgestellt?\"
• \"Wo habe ich Risiken?\"
• \"Was sind die Top 3 Punkte?\"
• \"Sollte ich rebalancieren?\"
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Portfolio Overview"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio:
        await update.message.reply_text("❌ Fehler beim Laden des Portfolios")
        return
    
    cash_pct = (portfolio['cash'] / portfolio['total_value'] * 100) if portfolio['total_value'] > 0 else 0
    
    response = f"""📊 *Dein Portfolio*

💰 *Gesamtwert:* €{portfolio['total_value']:,.0f}
💸 *Cash:* €{portfolio['cash']:,.0f} ({cash_pct:.1f}%)
📈 *Positionen:* {analysis['num_positions']}

🏆 *Größte Position:*
{analysis['biggest_position']} ({analysis['biggest_weight']}%)

📊 *Konzentration:*
{analysis['concentration_level']}

⚠️ *Risiko-Einschätzung:*
{analysis['risk_summary']}

💡 *Wichtigster Hebel:*
{analysis['main_lever']}

_Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y %H:%M')}_
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def top3_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Top 3 Positionen"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not portfolio.get('positions'):
        await update.message.reply_text("❌ Keine Positionen gefunden")
        return
    
    top3 = portfolio['positions'][:3]
    
    response = "🏆 *Top 3 Positionen*\n\n"
    for i, pos in enumerate(top3, 1):
        response += f"{i}. {pos['name']}\n"
        response += f"   Gewichtung: {pos.get('weight', 0):.1f}%\n"
        response += f"   Wert: €{pos.get('valuation', 0):,.0f}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def top10_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Top 10 Positionen"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not portfolio.get('positions'):
        await update.message.reply_text("❌ Keine Positionen gefunden")
        return
    
    top10 = portfolio['positions'][:10]
    
    response = "🏆 *Top 10 Positionen*\n\n"
    for i, pos in enumerate(top10, 1):
        response += f"{i}. {pos['name']} – {pos.get('weight', 0):.1f}% (€{pos.get('valuation', 0):,.0f})\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def risks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Risikoanalyse"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not analysis:
        await update.message.reply_text("❌ Fehler beim Laden")
        return
    
    response = f"""⚠️ *Risikoanalyse*

📊 *Konzentration:*
{analysis['concentration_level']}

💡 *Größte Risiken:*
• Top Position: {analysis['biggest_position']} ({analysis['biggest_weight']}%)
• Sektor-Konzentration erkannt
• Cash-Quote: {analysis['cash_ratio']:.1f}%

🎯 *Empfehlung:*
{analysis['main_lever']}

📈 *Risk Score:*
{analysis['risk_summary']}
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Performance & Gewinn/Verlust"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or 'analytics' not in portfolio:
        await update.message.reply_text("❌ Keine Performance-Daten verfügbar")
        return
    
    analytics = portfolio.get('analytics', {})
    
    gains_losses = analytics.get('total_gains_losses', 0)
    performance_pct = analytics.get('performance_pct', 0)
    
    emoji = "📈" if gains_losses > 0 else "📉"
    
    response = f"""{emoji} *Performance & Gewinn/Verlust*

💰 *Aktueller Wert:* €{portfolio['total_value']:,.0f}
📊 *Gesamt investiert:* €{analytics.get('total_invested', 0):,.0f}

💸 *Gewinn/Verlust:* €{gains_losses:+,.0f}
📈 *Performance:* {performance_pct:+.2f}%

🏆 *Best Performer:*
{analytics.get('best_performer', 'N/A')} ({analytics.get('best_performer_pct', 0):+.2f}%)

❌ *Worst Performer:*
{analytics.get('worst_performer', 'N/A')} ({analytics.get('worst_performer_pct', 0):+.2f}%)

_Hinweis: Demo-Daten, nicht real_
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def diversification_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Diversifizierung"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or 'analytics' not in portfolio:
        await update.message.reply_text("❌ Keine Daten verfügbar")
        return
    
    analytics = portfolio.get('analytics', {})
    div_score = analytics.get('diversification_score', 0)
    
    # Interpret Score
    if div_score >= 8:
        rating = "Sehr gut ✅"
    elif div_score >= 6:
        rating = "Gut 👍"
    elif div_score >= 4:
        rating = "Mittel ⚠️"
    else:
        rating = "Schwach ❌"
    
    response = f"""📊 *Diversifizierung*

🎯 *Diversifizierungs-Score:* {div_score}/10 ({rating})

📈 *Top 3 Positionen:* {analytics.get('concentration_level', 'N/A')}

💡 *Analyse:*
• Du hast {analysis['num_positions']} verschiedene Positionen
• Cash-Quote: {analysis['cash_ratio']:.1f}%
• Sektor-Diversifizierung: Gut verteilt

✅ *Empfehlungen:*
• Diversifizierung ist solid
• Könnte noch erweitert werden
• Cash-Position ist angemessen
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Letzte Transaktionen"""
    portfolio, _ = load_portfolio_data()
    
    if not portfolio or not portfolio.get('transactions'):
        await update.message.reply_text("❌ Keine Transaktionen verfügbar")
        return
    
    transactions = portfolio['transactions'][-5:]  # Letzte 5
    
    response = "💱 *Letzte 5 Transaktionen*\n\n"
    for tx in reversed(transactions):
        response += f"📅 {tx['date']}\n"
        response += f"   {tx['name']}\n"
        response += f"   {tx['type']}: {tx['quantity']:.0f} @ €{tx['price']:.2f}\n"
        response += f"   Total: €{tx['total']:,.0f}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Vollständige Analyse"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not analysis:
        await update.message.reply_text("❌ Fehler beim Laden")
        return
    
    await update.message.chat.send_action("typing")
    
    # Frage an Coach
    question = "Gib mir eine kurze, strukturierte Analyse meines Portfolios mit den 3 wichtigsten Punkten und Empfehlungen."
    
    try:
        coach_response = ask_coach(
            question=question,
            portfolio_data=portfolio,
            analysis=analysis,
            history=[]
        )
        
        response = f"""📊 *Vollständige Portfolio-Analyse*

{coach_response}

_Basierend auf aktuellen Demo-Daten_
"""
        
        if len(response) <= 4096:
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            # Split wenn zu lang
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i:i+4096], parse_mode="Markdown")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {e}")

async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Wichtigste Erkenntnisse"""
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not analysis:
        await update.message.reply_text("❌ Fehler beim Laden")
        return
    
    response = f"""💡 *Wichtigste Erkenntnisse*

🔥 *Highlight:*
{analysis.get('highlight_title', 'N/A')}
{analysis.get('highlight_text', 'N/A')}

🎯 *Wichtigster Hebel:*
{analysis.get('main_lever', 'N/A')}

⚠️ *Risiko-Einschätzung:*
{analysis.get('risk_summary', 'N/A')}

❓ *Nächste Frage:*
{analysis.get('next_question', 'N/A')}
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daten neu laden"""
    try:
        portfolio, analysis = load_portfolio_data()
        if portfolio and analysis:
            await update.message.reply_text("✅ Daten neu geladen!")
        else:
            await update.message.reply_text("❌ Fehler beim Laden")
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {e}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot Status"""
    portfolio, analysis = load_portfolio_data()
    
    status = "✅ Online" if portfolio and analysis else "❌ Fehler"
    
    response = f"""🤖 *Bot Status*

Status: {status}
Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Version: v2.0 (Enhanced)

📊 Portfolio geladen: {'✅' if portfolio else '❌'}
📈 Analyse verfügbar: {'✅' if analysis else '❌'}
"""
    await update.message.reply_text(response, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle normale Nachrichten - frag den Coach"""
    user_message = update.message.text
    
    portfolio, analysis = load_portfolio_data()
    
    if not portfolio or not analysis:
        await update.message.reply_text("❌ Portfolio-Daten nicht verfügbar")
        return
    
    # Chat-Historie speichern (einfach)
    if not hasattr(context.user_data, 'history'):
        context.user_data['history'] = []
    
    await update.message.chat.send_action("typing")
    
    try:
        # Frage an Coach mit Historie
        response = ask_coach(
            question=user_message,
            portfolio_data=portfolio,
            analysis=analysis,
            history=context.user_data.get('history', [])
        )
        
        # Speichere in Historie
        context.user_data['history'] = context.user_data.get('history', []) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
        
        # Keep nur letzte 10 Nachrichten
        if len(context.user_data['history']) > 20:
            context.user_data['history'] = context.user_data['history'][-20:]
        
        # Sende Antwort
        if len(response) <= 4096:
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            # Split wenn zu lang
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i:i+4096], parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Fehler: {e}")

# ==================
# MAIN
# ==================

def main() -> None:
    print("=" * 60)
    print("🚀 Investment Coach – Enhanced Telegram Bot GESTARTET")
    print("=" * 60)
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("portfolio", portfolio_command))
    application.add_handler(CommandHandler("top3", top3_command))
    application.add_handler(CommandHandler("top10", top10_command))
    application.add_handler(CommandHandler("risks", risks_command))
    application.add_handler(CommandHandler("performance", performance_command))
    application.add_handler(CommandHandler("diversification", diversification_command))
    application.add_handler(CommandHandler("transactions", transactions_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("insights", insights_command))
    application.add_handler(CommandHandler("refresh", refresh_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("⏳ Bot läuft...")
    application.run_polling()

if __name__ == '__main__':
    main()