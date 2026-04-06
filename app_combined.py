#!/usr/bin/env python3
"""
Investment Coach – Streamlit UI mit Demo/Live-Schalter
+ Datenrefresh + Transaktions-Tab
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import subprocess

from analyze_portfolio import analyze_portfolio
from coach_core import ask_coach

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# ===== AUTHENTICATION =====
def check_password():
    """Returns `True` if the user had a correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("APP_PASSWORD", "investment-coach-2024"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("## 🔐 Login erforderlich")
    st.text_input(
        "Passwort:", type="password", on_change=password_entered, key="password"
    )
    if st.session_state.get("password_correct") is False:
        st.error("😕 Passwort falsch")
    return False

if not check_password():
    st.stop()

# ===== APP CONTENT STARTS HERE =====

# ==================
# CONFIG
# ==================

st.set_page_config(
    page_title="Investment Coach",
    page_icon="📈",
    layout="wide"
)

# ==================
# STYLING
# ==================

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

[data-testid="stMetric"] {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 14px;
    border-radius: 14px;
}

.insight-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 14px;
}

.highlight-card {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 16px;
}

.success-card {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 16px;
}

.demo-card {
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 16px;
}

.small-label {
    font-size: 0.85rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.big-text {
    font-size: 1.05rem;
    font-weight: 600;
    color: #111827;
}

.helper-text {
    color: #4b5563;
    font-size: 0.95rem;
}

.section-title {
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
    font-size: 1.1rem;
    font-weight: 700;
}

.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    border: 1px solid #e5e7eb;
    background: #f8fafc;
    color: #111827;
    margin-right: 8px;
    margin-bottom: 8px;
}

.badge-high {
    background: #fef2f2;
    border-color: #fecaca;
    color: #991b1b;
}

.badge-medium {
    background: #fffbeb;
    border-color: #fde68a;
    color: #92400e;
}

.badge-low {
    background: #ecfdf5;
    border-color: #a7f3d0;
    color: #065f46;
}

.badge-live {
    background: #dbeafe;
    border-color: #7dd3fc;
    color: #0c4a6e;
}

.badge-demo {
    background: #fef3c7;
    border-color: #fcd34d;
    color: #78350f;
}

.gain {
    color: #059669;
    font-weight: 600;
}

.loss {
    color: #dc2626;
    font-weight: 600;
}

.neutral {
    color: #6b7280;
}
</style>
""", unsafe_allow_html=True)

# ==================
# SESSION STATE
# ==================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "data_source" not in st.session_state:
    st.session_state.data_source = "demo"

if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = None

# ==================
# FUNCTIONS
# ==================

def load_demo_data():
    """Lade Demo-Daten aus sample_data.json - IMMER frisch!"""
    try:
        with open("sample_data.json", "r") as f:
            data = json.load(f)
        
        # Stelle sicher dass total_value und cash richtig sind
        if "total_value" not in data or data["total_value"] == 0:
            data["total_value"] = sum(p.get("valuation", 0) for p in data.get("positions", [])) + data.get("cash", 0)
        
        if "cash" not in data:
            data["cash"] = 0
        
        data["source"] = "Demo-Portfolio"
        data["timestamp"] = datetime.now().isoformat()
        
        return data
    except Exception as e:
        st.error(f"❌ Fehler beim Laden von sample_data.json: {e}")
        return None


def load_scalable_data():
    """Lade echte Scalable-Daten aus JSON-Dateien + Transaktionen"""
    try:
        with open("portfolio_live.json", "r") as f:
            overview_data = json.load(f)
        
        with open("portfolio_holdings.json", "r") as f:
            holdings_data = json.load(f)
        
        # Versuche auch Transaktionen zu laden
        transactions = []
        try:
            with open("portfolio_transactions.json", "r") as f:
                tx_data = json.load(f)
                tx_items = tx_data.get("data", {}).get("result", {}).get("items", [])
                
                # Extrahiere nur die SECURITY_TRANSACTION Einträge (keine Cash-Transaktionen)
                for tx in tx_items:
                    if tx.get("type") == "SECURITY_TRANSACTION":
                        transactions.append({
                            "date": tx.get("last_event_datetime", "").split("T")[0],
                            "ticker": tx.get("description", "Unknown"),
                            "name": tx.get("description", "Unknown"),
                            "type": tx.get("side", "").upper(),
                            "quantity": abs(tx.get("quantity", 0)),
                            "price": abs(tx.get("amount", 0)) / max(tx.get("quantity", 1), 1),
                            "total": abs(tx.get("amount", 0)),
                            "notes": f"{tx.get('security_transaction_type', '')}"
                        })
        except FileNotFoundError:
            pass
        
        # Extrahiere Portfolio-Daten
        overview = overview_data.get("data", {}).get("result", {})
        holdings = holdings_data.get("data", {}).get("result", {})
        
        total_value = overview.get("valuation", {}).get("total", 0)
        securities_value = overview.get("valuation", {}).get("securities", 0)
        cash = total_value - securities_value
        
        # Transformiere Holdings
        positions = []
        for holding in holdings.get("items", []):
            valuation = holding.get("valuation", 0)
            if valuation > 0:
                weight = (valuation / total_value * 100) if total_value > 0 else 0
                positions.append({
                    "name": holding.get("name", "Unknown"),
                    "weight": round(weight, 2),
                    "isin": holding.get("isin"),
                    "security_type": holding.get("security_type"),
                    "quantity": holding.get("quantity"),
                    "price": holding.get("quote_mid_price"),
                    "valuation": round(valuation, 2),
                })
        
        positions = sorted(positions, key=lambda x: x["weight"], reverse=True)
        
        return {
            "total_value": round(total_value, 2),
            "cash": round(cash, 2),
            "positions": positions,
            "transactions": transactions,
            "source": "Scalable Live",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        st.error(f"❌ Fehler beim Laden von Scalable-Daten: {e}")
        return None


def refresh_scalable_data():
    """Aktualisiere Scalable-Daten via Script"""
    try:
        with st.spinner("🔄 Aktualisiere Daten von Scalable..."):
            result = subprocess.run(
                ["/usr/bin/sudo", "-n", "-u", "investment-coach", "/home/investment-coach/investment-coach/sync-scalable.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                st.session_state.last_refresh_time = datetime.now()
                st.success("✅ Alle Daten aktualisiert!")
                return True
            else:
                st.error(f"❌ Fehler beim Sync (Code: {result.returncode})")
                if result.stderr:
                    st.error(f"Details: {result.stderr[:200]}")
                return False
    
    except Exception as e:
        st.error(f"❌ Fehler beim Refresh: {e}")
        return False


def get_badge_class(value):
    if value == "Hoch":
        return "badge badge-high"
    if value == "Mittel":
        return "badge badge-medium"
    return "badge badge-low"


def run_question(user_input, portfolio_data, analysis):
    """Verarbeite User-Frage"""
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    history_for_model = st.session_state.messages[:-1]
    
    with st.spinner("🤖 Coach denkt nach..."):
        answer = ask_coach(
            question=user_input,
            portfolio_data=portfolio_data,
            analysis=analysis,
            history=history_for_model
        )
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })


def render_transactions_tab(portfolio_data):
    """Zeige Transaktionen mit Profit/Loss"""
    if "transactions" not in portfolio_data:
        st.info("ℹ️ Keine Transaktionsdaten vorhanden")
        return
    
    transactions = portfolio_data.get("transactions", [])
    
    if not transactions:
        st.info("ℹ️ Keine Transaktionen vorhanden")
        return
    
    # Erstelle DataFrame
    tx_data = []
    for tx in transactions:
        name = tx.get("name", "Unknown")
        ticker = tx.get("ticker", "")
        tx_type = tx.get("type", "")
        quantity = tx.get("quantity", 0)
        price = tx.get("price", 0)
        total = tx.get("total", 0)
        date = tx.get("date", "")
        notes = tx.get("notes", "")
        
        tx_data.append({
            "Datum": date,
            "Ticker": ticker,
            "Position": name,
            "Typ": tx_type,
            "Menge": f"{quantity:.0f}",
            "Preis €": f"{price:.2f}",
            "Total €": f"{total:,.0f}",
            "Notizen": notes,
        })
    
    df = pd.DataFrame(tx_data)
    
    # Sortiere nach Datum (neueste zuerst)
    df["Datum_sort"] = pd.to_datetime(df["Datum"])
    df = df.sort_values("Datum_sort", ascending=False)
    df = df.drop(columns=["Datum_sort"])
    
    st.dataframe(
        df,
        hide_index=True,
        width='stretch',
        use_container_width=True
    )
    
    # Statistiken
    col1, col2, col3, col4 = st.columns(4)
    
    total_invested = sum(float(tx.get("total", 0)) for tx in transactions)
    buys = sum(1 for tx in transactions if tx.get("type") == "BUY")
    sells = sum(1 for tx in transactions if tx.get("type") == "SELL")
    
    with col1:
        st.metric("Gesamt investiert", f"€{total_invested:,.0f}")
    
    with col2:
        st.metric("Transaktionen", f"{len(transactions)}")
    
    with col3:
        st.metric("Käufe", f"{buys}")
    
    with col4:
        st.metric("Verkäufe", f"{sells}")


# ==================
# MAIN APP
# ==================

# Header mit Schalter
col_title, col_toggle = st.columns([4, 1])

with col_title:
    st.title("📈 Investment Coach")
    st.caption("Dein intelligenter Portfolio-Assistent")

with col_toggle:
    st.markdown("")
    data_source = st.radio(
        "Datenquelle",
        options=["demo", "live"],
        format_func=lambda x: "📊 Demo-Daten" if x == "demo" else "📡 Scalable Live",
        horizontal=True
    )
    
    if data_source != st.session_state.data_source:
        st.session_state.data_source = data_source
        st.session_state.messages = []

# ==================
# DATEN LADEN (IMMER!)
# ==================

# Lade Daten NEU bei jedem Rerun
if st.session_state.data_source == "demo":
    info_card_style = "demo-card"
    info_label = "📊 Demo-Portfolio"
    info_text = "Demonstrationsdaten zum Vorzeigen und Testen"
    badge_style = "badge badge-demo"
    portfolio_data = load_demo_data()
else:
    info_card_style = "success-card"
    info_label = "✅ Live-Integration aktiv"
    info_text = "Echte Scalable Broker Daten – alle Empfehlungen basieren auf deinem echten Portfolio"
    badge_style = "badge badge-live"
    portfolio_data = load_scalable_data()

st.markdown(f"""
<div class="{info_card_style}">
    <div class="small-label">{info_label}</div>
    <div class="big-text">{"Demo-Daten" if st.session_state.data_source == "demo" else "Echte Scalable Daten"}</div>
    <div class="helper-text">{info_text}</div>
</div>
""", unsafe_allow_html=True)

if not portfolio_data:
    st.error("❌ Konnte Portfolio-Daten nicht laden!")
    st.stop()

analysis = analyze_portfolio(portfolio_data)

# ==================
# SIDEBAR
# ==================

with st.sidebar:
    st.markdown("## 📊 Portfolio Snapshot")
    
    st.metric("Depotwert", f"€{portfolio_data['total_value']:,.0f}".replace(",", "."))
    st.metric("Cash-Quote", f"{analysis['cash_ratio']:.1f} %" if isinstance(analysis['cash_ratio'], (int, float)) else f"{analysis['cash_ratio']} %")
    st.metric("Top-3-Gewichtung", f"{analysis['top3_weight']} %")
    st.metric("Positionen", analysis["num_positions"])
    
    st.divider()
    
    st.markdown("### 🎯 Einordnung")
    st.markdown(f"""
- **Größte Position:** {analysis['biggest_position']}
- **Größte Gewichtung:** {analysis['biggest_weight']} %
- **Konzentration:** {analysis['concentration_level']}
- **Cash-Niveau:** {analysis['cash_assessment']}
- **Quelle:** {portfolio_data.get('source', 'Unknown')}
""")
    
    st.divider()
    
    # Refresh Buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔄 Neu laden", width="stretch"):
            st.rerun()
    
    with col_btn2:
        if st.session_state.data_source == "live":
            if st.button("⬆️ Scalable", width="stretch"):
                if refresh_scalable_data():
                    st.rerun()
        else:
            if st.button("🗑️ Chat reset", width="stretch"):
                st.session_state.messages = []
                st.rerun()
    
    if st.session_state.last_refresh_time:
        st.caption(f"Aktualisiert: {st.session_state.last_refresh_time.strftime('%H:%M:%S')}")

# ==================
# TABS
# ==================

tab1, tab2, tab3 = st.tabs(["💬 Coach Chat", "📊 Portfolio", "💱 Transaktionen"])

# ==================
# TAB 1: COACH CHAT
# ==================

with tab1:
    col1, col2 = st.columns([2.2, 1])
    
    with col1:
        st.markdown('<div class="section-title">💬 Coach Chat</div>', unsafe_allow_html=True)
        
        # Badges
        st.markdown(f"""
        <span class="{get_badge_class(analysis['concentration_level'])}">
            Konzentration: {analysis['concentration_level']}
        </span>
        <span class="badge badge-low">
            Cash: {analysis['cash_assessment']}
        </span>
        <span class="{badge_style}">
            {"📊 Demo" if st.session_state.data_source == "demo" else "📡 Live"}
        </span>
        """, unsafe_allow_html=True)
        
        # Highlight
        st.markdown(f"""
        <div class="highlight-card">
            <div class="small-label">🔥 Wichtigster Punkt aktuell</div>
            <div class="big-text">{analysis['highlight_title']}</div>
            <div class="helper-text">{analysis['highlight_text']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat-Messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat-Input
        user_input = st.chat_input("Frag deinen Coach...")
        
        if user_input:
            run_question(user_input, portfolio_data, analysis)
            st.rerun()
    
    with col2:
        st.markdown('<div class="section-title">📌 Insights</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-card">
            <div class="small-label">💡 Wichtigster Hebel</div>
            <div class="big-text">{analysis['main_lever']}</div>
            <div class="helper-text">Das ist aktuell der naheliegendste Denkhebel.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-card">
            <div class="small-label">⚠️ Risikoeinschätzung</div>
            <div class="big-text">{analysis['risk_summary']}</div>
            <div class="helper-text">Verdichtete Einordnung auf Basis deiner Struktur.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-card">
            <div class="small-label">❓ Nächste Frage</div>
            <div class="big-text">{analysis['next_question']}</div>
            <div class="helper-text">Damit kommst du im Gespräch am schnellsten weiter.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
        
        if st.button("📊 Portfolio einordnen", width="stretch"):
            user_q = "Wie ist mein Portfolio wirklich aufgestellt?"
            run_question(user_q, portfolio_data, analysis)
            st.rerun()
        
        if st.button("⚠️ Risiken checken", width="stretch"):
            user_q = "Wo habe ich ein Klumpenrisiko?"
            run_question(user_q, portfolio_data, analysis)
            st.rerun()
        
        if st.button("🎯 Top 3 Punkte", width="stretch"):
            user_q = "Was sind die 3 wichtigsten Punkte?"
            run_question(user_q, portfolio_data, analysis)
            st.rerun()

# ==================
# TAB 2: PORTFOLIO
# ==================

with tab2:
    st.markdown("## 📋 Portfolio-Struktur (Top 15)")
    
    positions_list = portfolio_data["positions"][:15]
    positions_df = pd.DataFrame(positions_list)
    
    # Formatiere für Anzeige
    cols_available = positions_df.columns.tolist()
    
    if "security_type" in cols_available:
        # Scalable Live Daten
        display_df = positions_df[["name", "weight", "security_type", "quantity", "valuation"]].copy()
        display_df.columns = ["Position", "Gewichtung (%)", "Typ", "Menge", "Wert €"]
        display_df["Gewichtung (%)"] = display_df["Gewichtung (%)"].apply(lambda x: f"{x:.2f}%")
        display_df["Menge"] = display_df["Menge"].apply(lambda x: f"{x:.2f}")
        display_df["Wert €"] = display_df["Wert €"].apply(lambda x: f"€{x:,.0f}")
    else:
        # Demo Daten
        display_df = positions_df[["name", "weight"]].copy()
        if "valuation" in cols_available:
            display_df["valuation"] = positions_df["valuation"]
            display_df = display_df[["name", "weight", "valuation"]]
            display_df.columns = ["Position", "Gewichtung (%)", "Wert €"]
            display_df["Wert €"] = display_df["Wert €"].apply(lambda x: f"€{x:,.0f}")
        else:
            display_df.columns = ["Position", "Gewichtung (%)"]
        display_df["Gewichtung (%)"] = display_df["Gewichtung (%)"].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(
        display_df,
        hide_index=True,
        width='stretch'
    )

# ==================
# TAB 3: TRANSAKTIONEN
# ==================

with tab3:
    st.markdown("## 💱 Transaktionshistorie")
    render_transactions_tab(portfolio_data)

# ==================
# FOOTER
# ==================

st.divider()
st.caption(f"""
📡 **Quelle:** {portfolio_data.get('source', 'Unknown')}  
🔄 **Aktualisiert:** {portfolio_data.get('timestamp', 'Unknown')}  
⚠️ **Disclaimer:** Der Coach gibt keine Kauf-/Verkaufsanweisungen, nur Entscheidungshilfen.
""")
