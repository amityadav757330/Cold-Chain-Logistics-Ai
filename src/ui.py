import json
from datetime import datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.orchestrator import (
    build_graph,
    parse_telemetry,
    parse_weather,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cold-Chain Logistics AI",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PREMIUM DASHBOARD STYLING
# ============================================================

st.markdown(
    """
    <style>
    /* ---------- Global ---------- */
    .stApp {
        background:
            radial-gradient(circle at 10% 0%, rgba(30, 64, 175, 0.12), transparent 28%),
            radial-gradient(circle at 90% 10%, rgba(14, 165, 233, 0.08), transparent 25%),
            #080b12;
    }

    /* Use the full browser width for the command center.
       Streamlit may apply a narrower default content container, so
       these selectors intentionally override it. */
    .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"] .main .block-container,
    section.main > div {
        width: 100% !important;
        max-width: none !important;
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        padding-left: 1.75rem;
        padding-right: 1.75rem;
    }

    [data-testid="stAppViewContainer"] .main {
        width: 100% !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1320 0%, #090d15 100%);
        border-right: 1px solid #1d2939;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    /* ---------- Hero ---------- */
    .hero {
        padding: 28px 30px;
        border-radius: 20px;
        border: 1px solid #24344b;
        background:
            linear-gradient(135deg, rgba(18, 36, 64, 0.95), rgba(10, 17, 29, 0.96));
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
        margin-bottom: 18px;
    }

    .hero-kicker {
        color: #60a5fa;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 2.35rem;
        line-height: 1.05;
        font-weight: 850;
        color: #f8fafc;
        margin: 0;
    }

    .hero-subtitle {
        color: #a9b6c8;
        font-size: 0.98rem;
        margin-top: 10px;
        max-width: 1100px;
        line-height: 1.6;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 18px;
    }

    .hero-pill {
        border: 1px solid #29405d;
        background: rgba(15, 23, 42, 0.72);
        color: #cbd5e1;
        padding: 6px 11px;
        border-radius: 999px;
        font-size: 0.75rem;
    }

    /* ---------- Section headings ---------- */
    .section-title {
        color: #f8fafc;
        font-size: 1.12rem;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 2px;
    }

    .section-subtitle {
        color: #8492a6;
        font-size: 0.78rem;
        margin-bottom: 12px;
    }

    /* ---------- KPI cards ---------- */
    .kpi {
        min-height: 125px;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #233249;
        background: linear-gradient(145deg, #101827, #0b111d);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
    }

    .kpi-label {
        color: #8796aa;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-weight: 700;
    }

    .kpi-value {
        color: #f8fafc;
        font-size: 2rem;
        line-height: 1.1;
        font-weight: 850;
        margin-top: 8px;
    }

    .kpi-note {
        color: #718096;
        font-size: 0.72rem;
        margin-top: 6px;
    }

    .kpi-danger {
        border-color: #7f1d1d;
        background: linear-gradient(145deg, #1c1015, #0f1018);
    }

    .kpi-warning {
        border-color: #854d0e;
        background: linear-gradient(145deg, #1b160d, #0f1118);
    }

    .kpi-good {
        border-color: #14532d;
        background: linear-gradient(145deg, #0d1b16, #0d1118);
    }

    /* ---------- Status cards ---------- */
    .status-card {
        border-radius: 13px;
        border: 1px solid #233249;
        background: #0d1420;
        padding: 12px 14px;
        margin-bottom: 8px;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 7px;
        background: #22c55e;
        box-shadow: 0 0 9px rgba(34, 197, 94, 0.55);
    }

    .status-text {
        color: #dbe5f0;
        font-size: 0.78rem;
        font-weight: 650;
    }

    /* ---------- Action cards ---------- */
    .action-card {
        border-radius: 15px;
        padding: 15px 17px;
        margin-bottom: 10px;
        border: 1px solid #28384e;
        background: linear-gradient(145deg, #0f1724, #0b1018);
    }

    .action-card.critical {
        border-left: 4px solid #ef4444;
    }

    .action-card.warning {
        border-left: 4px solid #f59e0b;
    }

    .action-card.info {
        border-left: 4px solid #38bdf8;
    }

    .action-vehicle {
        color: #f8fafc;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .action-text {
        color: #aebdce;
        font-size: 0.78rem;
        line-height: 1.5;
    }

    .mode-banner {
        border: 1px solid #31527a;
        background: linear-gradient(90deg, #0d1b2d, #101827);
        color: #b9d7f5;
        border-radius: 12px;
        padding: 9px 13px;
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .alert-grid-card {
        border: 1px solid #263852;
        background: linear-gradient(145deg, #101827, #0b111a);
        border-radius: 15px;
        padding: 16px;
        min-height: 112px;
    }

    .alert-number {
        color: #f8fafc;
        font-size: 1.65rem;
        font-weight: 850;
        margin-top: 5px;
    }

    .alert-label {
        color: #8796aa;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
    }

    /* ---------- Welcome cards ---------- */
    .feature-card {
        border: 1px solid #233249;
        background: linear-gradient(145deg, #101827, #0b111b);
        border-radius: 16px;
        padding: 18px;
        min-height: 145px;
    }

    .feature-icon {
        font-size: 1.45rem;
    }

    .feature-title {
        color: #eaf1f8;
        font-weight: 800;
        margin-top: 8px;
    }

    .feature-text {
        color: #8492a6;
        font-size: 0.76rem;
        line-height: 1.55;
        margin-top: 5px;
    }

    /* ---------- Query panel ---------- */
    .query-panel {
        border: 1px solid #263852;
        border-radius: 17px;
        background: linear-gradient(145deg, #0f1725, #0a1019);
        padding: 18px;
        margin-bottom: 18px;
    }

    /* ---------- Small badges ---------- */
    .badge {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        margin-right: 5px;
    }

    .badge-red {
        color: #fecaca;
        background: #3f151b;
        border: 1px solid #7f1d1d;
    }

    .badge-yellow {
        color: #fde68a;
        background: #3a290d;
        border: 1px solid #854d0e;
    }

    .badge-green {
        color: #bbf7d0;
        background: #0d2a1b;
        border: 1px solid #166534;
    }

    /* ---------- Footer ---------- */
    .footer {
        color: #64748b;
        font-size: 0.72rem;
        text-align: center;
        padding: 24px 0 5px 0;
    }

    /* ---------- Streamlit refinements ---------- */
    div[data-testid="stMetric"] {
        background: #0d1420;
        border: 1px solid #233249;
        padding: 12px;
        border-radius: 14px;
    }

    div[data-testid="stMetricLabel"] {
        color: #8fa0b5;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 10px;
        padding: 0 16px;
    }

    .stTabs [aria-selected="true"] {
        background: #172338;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    /* ---------- Wide-layout responsiveness ---------- */
    @media (max-width: 1100px) {
        .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewContainer"] .main .block-container,
        section.main > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero-title {
            font-size: 1.9rem;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())[:8]

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_request" not in st.session_state:
    st.session_state.last_request = ""

if "analysis_count" not in st.session_state:
    st.session_state.analysis_count = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "dispatch_query" not in st.session_state:
    st.session_state.dispatch_query = ""

if "presentation_mode" not in st.session_state:
    st.session_state.presentation_mode = True


# ============================================================
# GRAPH
# ============================================================

@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def temperature_status(value):
    if not is_number(value):
        return "Unknown"

    if value > 4.0:
        return "Immediate breach"

    if 0.0 <= value <= 4.0:
        return "Within range"

    return "Below range"


def risk_badge(risk):
    value = str(risk or "Unknown")

    if value.lower() == "high risk":
        return '<span class="badge badge-red">HIGH RISK</span>'

    if "medium" in value.lower():
        return '<span class="badge badge-yellow">MEDIUM</span>'

    if value.lower() == "low risk":
        return '<span class="badge badge-green">LOW RISK</span>'

    return f'<span class="badge badge-yellow">{value.upper()}</span>'


def action_class(action_text):
    text = str(action_text).lower()

    if any(
        word in text
        for word in [
            "escalate",
            "breach",
            "immediate",
        ]
    ):
        return "critical"

    if any(
        word in text
        for word in [
            "divert",
            "suspend",
            "restart",
            "cold-storage",
            "cold storage",
        ]
    ):
        return "warning"

    return "info"


def build_fleet_dataframe(vehicles):
    rows = []

    for index, vehicle in enumerate(vehicles, start=1):
        temperature = vehicle.get("Current_Temperature_C")
        delay_probability = vehicle.get("Delay_Probability")
        port_congestion = vehicle.get("Port_Congestion_Level")
        route_risk = vehicle.get("Route_Risk_Index")
        risk = vehicle.get("Risk_Classification", "Unknown")

        rows.append(
            {
                "Vehicle": f"Vehicle {index}",
                "Risk": risk,
                "IoT Temperature (°C)": (
                    round(temperature, 2)
                    if is_number(temperature)
                    else None
                ),
                "Temperature Status": temperature_status(
                    temperature
                ),
                "Delay Probability": (
                    round(delay_probability, 3)
                    if is_number(delay_probability)
                    else None
                ),
                "Port Congestion": (
                    round(port_congestion, 3)
                    if is_number(port_congestion)
                    else None
                ),
                "Route Risk": (
                    round(route_risk, 3)
                    if is_number(route_risk)
                    else None
                ),
            }
        )

    return pd.DataFrame(rows)


def build_weather_dataframe(weather_data):
    rows = []

    for item in weather_data:
        rows.append(
            {
                "Vehicle": item.get("Vehicle", "Unknown"),
                "Weather Temperature (°C)": (
                    round(
                        item.get("Weather_Temperature_C"),
                        1,
                    )
                    if is_number(
                        item.get("Weather_Temperature_C")
                    )
                    else None
                ),
                "Wind Speed (km/h)": (
                    round(
                        item.get("Wind_Speed_kmh"),
                        1,
                    )
                    if is_number(
                        item.get("Wind_Speed_kmh")
                    )
                    else None
                ),
                "Disruption Index": (
                    round(
                        item.get("Disruption_Index"),
                        1,
                    )
                    if is_number(
                        item.get("Disruption_Index")
                    )
                    else None
                ),
            }
        )

    return pd.DataFrame(rows)


def build_action_map(actions):
    result = {}

    if not isinstance(actions, list):
        return result

    for item in actions:
        if not isinstance(item, dict):
            continue

        vehicle = item.get("Vehicle")
        action = item.get("Action")

        if vehicle is None or not action:
            continue

        result.setdefault(vehicle, []).append(str(action))

    return result


def make_report_download(result):
    final_response = result.get("final_response", "")

    if final_response:
        return str(final_response)

    analysis = result.get("analysis", "")
    return str(analysis)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🚚 Dispatch Console")
    st.caption("Cold-Chain Logistics AI")

    presentation_mode = st.toggle(
        "🎤 Presentation Mode",
        value=st.session_state.presentation_mode,
        help="Use a clean executive view for project demonstrations. Disable it to expose developer diagnostics.",
    )
    st.session_state.presentation_mode = presentation_mode

    st.markdown(
        f'<div class="mode-banner">{("🎤 Presentation view active" if presentation_mode else "🛠️ Developer view active")}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### System Status")

    for label in [
        "Database connected",
        "Weather service available",
        "SOP search available",
        "Deterministic risk engine ready",
    ]:
        st.markdown(
            f"""
            <div class="status-card">
                <span class="status-dot"></span>
                <span class="status-text">{label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### Quick Queries")

    quick_queries = {
        "🌡️ Temperature breaches":
            "Show me all vehicles with temperature above 4°C and tell me what action is required.",
        "🚨 High-risk vehicles":
            "Show me all High Risk vehicles with delay probability above 0.65 and tell me which vehicles require Tier 2 Logistics Manager escalation.",
        "⚓ Port congestion":
            "Show me all vehicles affected by port congestion above 7 and tell me what routing action is required.",
        "⏱️ Delay risk":
            "Show me all vehicles with delay risk and tell me which vehicles require diversion to emergency cold storage.",
        "🌐 Full fleet assessment":
            "Check the active fleet. Identify all vehicles with temperature above 4°C, port congestion above 7, and High Risk classification with delay probability above 0.65. For each vehicle, provide the telemetry values, applicable SOP rule, and required operational action. Also check the current weather conditions for the relevant vehicle locations.",
    }

    for label, query in quick_queries.items():
        if st.button(label, width="stretch"):
            st.session_state.dispatch_query = query
            st.rerun()

    st.divider()

    st.markdown("### Current Session")
    st.code(st.session_state.session_id)

    st.caption(
        f"Analyses completed: {st.session_state.analysis_count}"
    )

    if st.button(
        "🆕 Start New Session",
        width="stretch",
    ):
        st.session_state.session_id = str(uuid4())[:8]
        st.session_state.last_result = None
        st.session_state.last_request = ""
        st.session_state.analysis_count = 0
        st.session_state.history = []
        st.session_state.dispatch_query = ""
        st.rerun()

    if st.session_state.history:
        st.divider()
        st.markdown("### Recent Queries")

        for item in reversed(st.session_state.history[-5:]):
            st.caption(
                f"{item['time']}  •  {item['query'][:65]}"
            )


# ============================================================
# HERO HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Intelligent Fleet Operations Platform</div>
        <div class="hero-title">🚚 Cold-Chain Logistics AI</div>
        <div class="hero-subtitle">
            A dispatcher command center for telemetry monitoring,
            weather intelligence, deterministic SOP compliance,
            risk detection, operational actions, and audit traceability.
        </div>
        <div class="hero-pills">
            <span class="hero-pill">SQL Server Telemetry</span>
            <span class="hero-pill">LangGraph Orchestration</span>
            <span class="hero-pill">Open-Meteo</span>
            <span class="hero-pill">Pinecone SOP Search</span>
            <span class="hero-pill">Enterprise Audit Trail</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DISPATCHER QUERY PANEL
# ============================================================

st.markdown(
    '<div class="section-title">🎛️ Dispatcher Command Center</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">Ask the operational assistant a natural-language fleet question.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="query-panel">', unsafe_allow_html=True)

user_query = st.text_area(
    "Operational Query",
    key="dispatch_query",
    placeholder=(
        "Example: Show me all vehicles with temperature above 4°C "
        "and tell me what action is required."
    ),
    height=110,
    label_visibility="collapsed",
)

run_analysis = st.button(
    "🔎 Run Fleet Analysis",
    type="primary",
    width="stretch",
)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# RUN ANALYSIS
# ============================================================

if run_analysis:
    if not user_query.strip():
        st.warning("Please enter an operational query.")

    else:
        clean_query = user_query.strip()
        st.session_state.last_request = clean_query

        with st.spinner(
            "Running telemetry → weather → SOP → reasoning pipeline..."
        ):
            try:
                result = graph.invoke(
                    {
                        "user_request": clean_query,
                        "session_id": st.session_state.session_id,
                    }
                )

                st.session_state.last_result = result
                st.session_state.analysis_count += 1

                st.session_state.history.append(
                    {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "query": clean_query,
                    }
                )

            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                st.stop()


# ============================================================
# WELCOME SCREEN
# ============================================================

result = st.session_state.last_result

if not result:
    st.markdown("### 👋 Welcome to the Dispatcher Workspace")
    st.caption(
        "Use a quick query from the sidebar or enter your own operational question above."
    )

    feature_columns = st.columns(4)

    features = [
        (
            "🌡️",
            "Temperature Control",
            "Detect cold-chain breaches above the 4°C threshold and surface the required mitigation.",
        ),
        (
            "⚓",
            "Port Intelligence",
            "Identify congestion conditions and the corresponding routing response.",
        ),
        (
            "🌦️",
            "Weather Intelligence",
            "Combine vehicle location with current corridor weather conditions.",
        ),
        (
            "🧾",
            "Audit & Compliance",
            "Expose SOP evidence, execution trace, and enterprise audit records.",
        ),
    ]

    for column, feature in zip(feature_columns, features):
        with column:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="feature-icon">{feature[0]}</div>
                    <div class="feature-title">{feature[1]}</div>
                    <div class="feature-text">{feature[2]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.info(
        "Tip: try the “🌐 Full fleet assessment” quick query for an end-to-end demonstration."
    )

    st.markdown(
        '<div class="footer">Cold-Chain Logistics AI • Dispatcher Command Center</div>',
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# EXTRACT RESULT
# ============================================================

telemetry_text = result.get("telemetry", "")
weather_text = result.get("weather", "")
sop_text = result.get("sop", "")
analysis_text = result.get("analysis", "")
final_response = result.get("final_response", "")

vehicles = parse_telemetry(telemetry_text)
weather_data = parse_weather(weather_text)
actions = result.get("actions", [])

action_map = build_action_map(actions)

fleet_df = build_fleet_dataframe(vehicles)
weather_df = build_weather_dataframe(weather_data)

high_risk_count = sum(
    1
    for vehicle in vehicles
    if str(vehicle.get("Risk_Classification", "")).lower()
    == "high risk"
)

temperature_breach_count = sum(
    1
    for vehicle in vehicles
    if is_number(vehicle.get("Current_Temperature_C"))
    and vehicle.get("Current_Temperature_C") > 4.0
)

port_congestion_count = sum(
    1
    for vehicle in vehicles
    if is_number(vehicle.get("Port_Congestion_Level"))
    and vehicle.get("Port_Congestion_Level") > 7.0
)

tier2_count = sum(
    1
    for vehicle in vehicles
    if str(vehicle.get("Risk_Classification", "")).lower()
    == "high risk"
    and is_number(vehicle.get("Delay_Probability"))
    and vehicle.get("Delay_Probability") > 0.65
)

action_vehicle_count = len(action_map)


# ============================================================
# KPI STRIP
# ============================================================

st.markdown(
    '<div class="section-title">📊 Operational Overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">Current result snapshot generated from the operational analysis.</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

kpi_data = [
    (
        k1,
        "Fleet Records",
        len(vehicles),
        "Telemetry records returned",
        "",
    ),
    (
        k2,
        "High Risk",
        high_risk_count,
        "Risk classification",
        "kpi-danger" if high_risk_count else "kpi-good",
    ),
    (
        k3,
        "Temp Breaches",
        temperature_breach_count,
        "Above 4.0°C",
        "kpi-danger" if temperature_breach_count else "kpi-good",
    ),
    (
        k4,
        "Port Alerts",
        port_congestion_count,
        "Above 7.0",
        "kpi-warning" if port_congestion_count else "kpi-good",
    ),
    (
        k5,
        "Action Vehicles",
        action_vehicle_count,
        "SOP-triggered actions",
        "kpi-warning" if action_vehicle_count else "kpi-good",
    ),
]

for column, label, value, note, extra_class in kpi_data:
    with column:
        st.markdown(
            f"""
            <div class="kpi {extra_class}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.write("")


# ============================================================
# OPERATIONAL ASSESSMENT
# ============================================================

assessment_parts = []

if high_risk_count:
    assessment_parts.append(
        f"🔴 {high_risk_count} High Risk vehicle(s)"
    )

if temperature_breach_count:
    assessment_parts.append(
        f"🌡️ {temperature_breach_count} temperature breach(es)"
    )

if port_congestion_count:
    assessment_parts.append(
        f"⚓ {port_congestion_count} congestion alert(s)"
    )

if tier2_count:
    assessment_parts.append(
        f"👤 {tier2_count} Tier 2 escalation trigger(s)"
    )

if not assessment_parts:
    assessment_message = (
        "No immediate deterministic SOP trigger was identified in the returned fleet records."
    )
else:
    assessment_message = " • ".join(assessment_parts)

st.info(
    f"**Operational assessment:** {assessment_message}"
)


# ============================================================
# MAIN TABS
# ============================================================

(
    command_tab,
    fleet_tab,
    weather_tab,
    action_tab,
    audit_tab,
) = st.tabs(
    [
        "🎯 Command Center",
        "🚛 Fleet Intelligence",
        "🌦️ Weather Intelligence",
        "🚨 Actions & SOP",
        "🧾 Audit & Report",
    ]
)


# ============================================================
# COMMAND CENTER TAB
# ============================================================

with command_tab:
    st.markdown(
        '<div class="section-title">🎯 Command Center</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.presentation_mode:
        st.markdown(
            '<div class="section-subtitle">Executive view — focus on operational signals, alerts, and recommended actions.</div>',
            unsafe_allow_html=True,
        )

        alert_cols = st.columns(4)
        alert_cards = [
            (alert_cols[0], "🌡️", temperature_breach_count, "Temperature Breaches"),
            (alert_cols[1], "⚓", port_congestion_count, "Port Congestion Alerts"),
            (alert_cols[2], "👤", tier2_count, "Tier 2 Escalations"),
            (alert_cols[3], "🚨", action_vehicle_count, "Vehicles Requiring Action"),
        ]

        for column, icon, number, label in alert_cards:
            with column:
                st.markdown(
                    f"""
                    <div class=\"alert-grid-card\">
                        <div>{icon}</div>
                        <div class=\"alert-number\">{number}</div>
                        <div class=\"alert-label\">{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")
        st.markdown("#### 🧠 Executive Assessment")

        if final_response:
            summary_text = str(final_response)
            if len(summary_text) > 1800:
                summary_text = summary_text[:1800].rsplit(" ", 1)[0] + "…"
            st.markdown(summary_text)
        elif analysis_text:
            st.markdown(str(analysis_text))
        else:
            st.info("No operational assessment was generated.")

        if action_map:
            st.markdown("#### 🚨 Priority Actions")
            action_items = []
            for vehicle_id, vehicle_actions in action_map.items():
                for action_text in vehicle_actions:
                    action_items.append((vehicle_id, action_text))

            for vehicle_id, action_text in action_items[:6]:
                css_class = action_class(action_text)
                st.markdown(
                    f"""
                    <div class=\"action-card {css_class}\">
                        <div class=\"action-vehicle\">🚚 Vehicle {vehicle_id}</div>
                        <div class=\"action-text\">{action_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if len(action_items) > 6:
                st.caption(f"Showing 6 priority actions. Open “🚨 Actions & SOP” for the complete list ({len(action_items)} actions).")

        # Keep the executive screen focused. Detailed material stays available
        # behind one collapsed report section so the dispatcher sees decisions
        # before implementation details.
        with st.expander(
            "📄 Detailed Operational Report — click to expand",
            expanded=False,
        ):
            report_col1, report_col2 = st.columns(2)

            with report_col1:
                with st.expander("1. Executive Summary", expanded=False):
                    if final_response:
                        st.markdown(final_response)
                    elif analysis_text:
                        st.markdown(analysis_text)
                    else:
                        st.info("No executive summary is available.")

                with st.expander("2. Telemetry & Environment Analysis", expanded=False):
                    if not fleet_df.empty:
                        st.dataframe(
                            fleet_df,
                            width="stretch",
                            hide_index=True,
                        )
                    else:
                        st.info("No telemetry records are available.")

            with report_col2:
                with st.expander("3. Required Action Plan", expanded=False):
                    if action_map:
                        action_items = []
                        for vehicle_id, vehicle_actions in action_map.items():
                            for action_text in vehicle_actions:
                                action_items.append(
                                    (vehicle_id, action_text)
                                )

                        for vehicle_id, action_text in action_items:
                            st.markdown(
                                f"**🚚 Vehicle {vehicle_id}:** {action_text}"
                            )
                    else:
                        st.success("No immediate SOP-triggered actions were generated.")

                with st.expander("4. SOP Compliance", expanded=False):
                    if sop_text:
                        st.markdown(sop_text)
                    else:
                        st.info("No SOP evidence was returned for this analysis.")

                with st.expander("5. Query Executed", expanded=False):
                    st.code(
                        st.session_state.last_request or "No query recorded.",
                        language="text",
                    )

    else:
        st.markdown(
            '<div class="section-subtitle">Developer view — detailed reasoning context and operational output.</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([1.35, 1])

        with left:
            st.markdown("#### AI Operational Assessment")
            if final_response:
                st.markdown(final_response)
            elif analysis_text:
                st.write(analysis_text)
            else:
                st.info("No final operational response was generated.")

            st.markdown("#### Query Executed")
            st.code(st.session_state.last_request, language="text")

        with right:
            st.markdown("#### Risk Distribution")
            if not fleet_df.empty and "Risk" in fleet_df.columns:
                risk_counts = (
                    fleet_df["Risk"].fillna("Unknown").value_counts().rename("Vehicles").to_frame()
                )
                st.bar_chart(risk_counts)

            st.markdown("#### Temperature Distribution")
            if not fleet_df.empty:
                temperature_chart = fleet_df[["Vehicle", "IoT Temperature (°C)"]].dropna()
                if not temperature_chart.empty:
                    st.bar_chart(temperature_chart.set_index("Vehicle"))

    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Tier 2 Escalations", tier2_count)
    with c2:
        st.metric("Port Congestion Alerts", port_congestion_count)
    with c3:
        st.metric("Vehicles With Actions", action_vehicle_count)


# ============================================================
# FLEET INTELLIGENCE TAB
# ============================================================

with fleet_tab:
    st.markdown(
        '<div class="section-title">🚛 Fleet Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Filter the returned telemetry records before reviewing risk and threshold conditions.</div>',
        unsafe_allow_html=True,
    )

    if fleet_df.empty:
        st.warning("No fleet telemetry records were returned.")

    else:
        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            risk_options = sorted(
                fleet_df["Risk"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            selected_risk = st.multiselect(
                "Risk classification",
                risk_options,
                default=risk_options,
            )

        with filter_col2:
            status_options = sorted(
                fleet_df["Temperature Status"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            selected_status = st.multiselect(
                "Temperature status",
                status_options,
                default=status_options,
            )

        with filter_col3:
            search_text = st.text_input(
                "Vehicle search",
                placeholder="Vehicle 1",
            )

        filtered_df = fleet_df.copy()

        if selected_risk:
            filtered_df = filtered_df[
                filtered_df["Risk"].astype(str).isin(
                    selected_risk
                )
            ]

        if selected_status:
            filtered_df = filtered_df[
                filtered_df["Temperature Status"].astype(str).isin(
                    selected_status
                )
            ]

        if search_text.strip():
            filtered_df = filtered_df[
                filtered_df["Vehicle"]
                .astype(str)
                .str.contains(
                    search_text.strip(),
                    case=False,
                    na=False,
                )
            ]

        st.caption(
            f"Showing {len(filtered_df)} of {len(fleet_df)} fleet record(s)."
        )

        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
        )

        st.markdown("#### Threshold Analytics")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            delay_chart = filtered_df[
                ["Vehicle", "Delay Probability"]
            ].dropna()

            if not delay_chart.empty:
                st.caption("Delay probability by vehicle")
                st.bar_chart(
                    delay_chart.set_index("Vehicle")
                )

        with chart_col2:
            congestion_chart = filtered_df[
                ["Vehicle", "Port Congestion"]
            ].dropna()

            if not congestion_chart.empty:
                st.caption("Port congestion by vehicle")
                st.bar_chart(
                    congestion_chart.set_index("Vehicle")
                )

        st.download_button(
            "⬇️ Download Fleet CSV",
            data=filtered_df.to_csv(index=False),
            file_name="cold_chain_fleet_analysis.csv",
            mime="text/csv",
        )


# ============================================================
# WEATHER INTELLIGENCE TAB
# ============================================================

with weather_tab:
    st.markdown(
        '<div class="section-title">🌦️ Weather Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Weather values are kept separate from vehicle IoT telemetry.</div>',
        unsafe_allow_html=True,
    )

    if weather_df.empty:
        st.warning("Weather data is unavailable for this analysis.")

    else:
        weather_col1, weather_col2 = st.columns(2)

        with weather_col1:
            st.markdown("#### Current Corridor Conditions")

            st.dataframe(
                weather_df,
                width="stretch",
                hide_index=True,
            )

        with weather_col2:
            st.markdown("#### Weather Disruption Index")

            disruption_chart = weather_df[
                ["Vehicle", "Disruption Index"]
            ].dropna()

            if not disruption_chart.empty:
                st.bar_chart(
                    disruption_chart.set_index("Vehicle")
                )

            st.caption(
                "The weather service provides current temperature, wind speed, and the disruption index returned by the weather tool."
            )

        st.download_button(
            "⬇️ Download Weather CSV",
            data=weather_df.to_csv(index=False),
            file_name="cold_chain_weather_analysis.csv",
            mime="text/csv",
        )


# ============================================================
# ACTIONS & SOP TAB
# ============================================================

with action_tab:
    st.markdown(
        '<div class="section-title">🚨 Actions & SOP Compliance</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Operational actions generated from the deterministic rules and retrieved SOP context.</div>',
        unsafe_allow_html=True,
    )

    if action_map:
        for vehicle_id, vehicle_actions in action_map.items():
            for action_text in vehicle_actions:
                css_class = action_class(action_text)

                st.markdown(
                    f"""
                    <div class="action-card {css_class}">
                        <div class="action-vehicle">
                            🚚 Vehicle {vehicle_id}
                        </div>
                        <div class="action-text">
                            {action_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.success(
            "✅ No immediate SOP-triggered actions were generated."
        )

    st.markdown("#### SOP Evidence")

    if sop_text:
        st.markdown(sop_text)
    else:
        st.info(
            "No SOP evidence was returned for this analysis."
        )

    st.markdown("#### Decision Rules Used")

    rule_col1, rule_col2 = st.columns(2)

    with rule_col1:
        st.markdown(
            """
            **Cold-chain**
            - Fresh perishables: 0–4°C
            - Above 4°C: immediate breach

            **Delay**
            - ETA delay > 1 hour
            - Consider emergency cold-storage diversion
            """
        )

    with rule_col2:
        st.markdown(
            """
            **Port congestion**
            - Congestion > 7.0
            - Suspend standard routing
            - Divert to Inland Empire Overflow Depot

            **High-risk escalation**
            - High Risk
            - Delay probability > 0.65
            - Tier 2 Logistics Manager escalation
            """
        )


# ============================================================
# AUDIT & REPORT TAB
# ============================================================

with audit_tab:
    st.markdown(
        '<div class="section-title">🧾 Audit & Traceability</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Enterprise trace of the current analysis execution.</div>',
        unsafe_allow_html=True,
    )

    audit_history = result.get("audit_history", [])

    if audit_history:
        audit_rows = []

        for record in audit_history:
            if not isinstance(record, dict):
                continue

            audit_rows.append(
                {
                    key: "" if value is None else str(value)
                    for key, value in record.items()
                }
            )

        if audit_rows:
            audit_df = pd.DataFrame(audit_rows)

            st.dataframe(
                audit_df,
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No audit records are available.")

    else:
        st.info("No audit records are available.")

    st.divider()

    st.markdown("### 🔍 Analysis Execution Trace")

    trace_items = [
        (
            "Telemetry",
            result.get(
                "telemetry_status",
                "Telemetry node completed.",
            ),
        ),
        (
            "Weather",
            result.get(
                "weather_status",
                "Weather node completed.",
            ),
        ),
        (
            "SOP",
            result.get(
                "sop_status",
                "SOP node completed.",
            ),
        ),
        (
            "Analysis",
            result.get(
                "analysis_status",
                "Analysis node completed.",
            ),
        ),
        (
            "Reasoner",
            result.get(
                "reasoner_status",
                "Reasoner completed.",
            ),
        ),
    ]

    trace_columns = st.columns(len(trace_items))

    for column, (name, status) in zip(
        trace_columns,
        trace_items,
    ):
        with column:
            st.success(
                f"**{name}**\n\n{status}"
            )

    st.divider()

    st.markdown("### 📄 Export Center")

    report_text = make_report_download(result)

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        st.download_button(
            "⬇️ Download Fleet JSON",
            data=json.dumps(
                result,
                indent=2,
                default=str,
            ),
            file_name="cold_chain_analysis.json",
            mime="application/json",
            width="stretch",
        )

    with export_col2:
        st.download_button(
            "⬇️ Download Operational Report",
            data=report_text,
            file_name="cold_chain_operational_report.txt",
            mime="text/plain",
            width="stretch",
        )

    with export_col3:
        if not fleet_df.empty:
            st.download_button(
                "⬇️ Download Full Fleet CSV",
                data=fleet_df.to_csv(index=False),
                file_name="cold_chain_full_fleet.csv",
                mime="text/csv",
                width="stretch",
            )


# ============================================================
# RAW / DEBUG INFORMATION
# ============================================================

if not st.session_state.presentation_mode:
    with st.expander("🛠️ Technical Diagnostics", expanded=False):
        diagnostic_col1, diagnostic_col2 = st.columns(2)

        with diagnostic_col1:
            st.markdown("**Telemetry tool output**")
            st.code(
                telemetry_text or "No telemetry output.",
                language="text",
            )

            st.markdown("**Weather tool output**")
            st.code(
                weather_text or "No weather output.",
                language="text",
            )

        with diagnostic_col2:
            st.markdown("**Analysis output**")
            st.code(
                analysis_text or "No analysis output.",
                language="text",
            )

            st.markdown("**Session information**")
            st.json(
                {
                    "session_id": st.session_state.session_id,
                    "last_query": st.session_state.last_request,
                    "analysis_count": st.session_state.analysis_count,
                    "presentation_mode": st.session_state.presentation_mode,
                }
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Cold-Chain Logistics AI • Intelligent Dispatcher Command Center
        <br>
        Telemetry • Weather • SOP Compliance • Risk Detection • Auditability
    </div>
    """,
    unsafe_allow_html=True,
)
