import json
from dotenv import load_dotenv
from openai import OpenAI
from coach_prompt import SYSTEM_PROMPT

load_dotenv(override=True)

client = OpenAI()


def ask_coach(question, portfolio_data, analysis, history=None):
    """
    Stelle dem Coach eine Frage zum Portfolio.

    - question: Nutzerfrage als String
    - portfolio_data: dict mit total_value, cash, positions
    - analysis: dict aus analyze_portfolio()
    - history: bisherige Chat-Messages (optional)
    """
    if history is None:
        history = []

    # Letzte 4 Messages für Kontext (statt nur 2)
    # → damit der Coach auf Ziele/Zeithorizont eingehen kann
    trimmed_history = history[-4:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in trimmed_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Themen-Exposure aufbereiten für den Prompt
    themes_text = ""
    if analysis.get("themes"):
        theme_lines = []
        for theme, value in sorted(analysis["themes"].items(), key=lambda x: x[1], reverse=True):
            theme_lines.append(f"  {theme}: ~{value}%")
        themes_text = "Geschätztes Themen-Exposure:\n" + "\n".join(theme_lines)

    full_input = f"""
Portfoliodaten:
- Gesamtwert: {portfolio_data['total_value']:,.0f} €
- Cash: {portfolio_data['cash']:,.0f} €
- Positionen: {len(portfolio_data['positions'])}

Positionen:
{json.dumps(portfolio_data['positions'], indent=2, ensure_ascii=False)}

Abgeleitete Kennzahlen:
- Cash-Quote: {analysis['cash_ratio']}%
- Top-3-Gewichtung: {analysis['top3_weight']}%
- Konzentration: {analysis['concentration_level']}
- Größte Position: {analysis['biggest_position']} ({analysis['biggest_weight']}%)

{themes_text}

Frage:
{question}
"""

    messages.append({"role": "user", "content": full_input})

    response = client.responses.create(
        model="gpt-5-mini",
        input=messages
    )

    return response.output_text
