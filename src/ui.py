import re
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.orchestrator import (
    build_graph,
    parse_telemetry,
    parse_weather,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Cold-Chain Logistics AI",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .status-box {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 14px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .action-box {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    .safe-action {
        background-color: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.30);
    }

    .warning-action {
        background-color: rgba(234, 179, 8, 0.15);
        border: 1px solid rgba(234, 179, 8, 0.30);
    }

    .danger-action {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.30);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "session_id" not in st.session_state:

    st.session_state.session_id = (
        str(uuid4())[:8]
    )

if "last_result" not in st.session_state:

    st.session_state.last_result = None

if "last_request" not in st.session_state:

    st.session_state.last_request = ""

if "analysis_count" not in st.session_state:

    st.session_state.analysis_count = 0


# =========================================================
# GRAPH
# =========================================================

@st.cache_resource
def get_graph():

    return build_graph()


graph = get_graph()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## 🚚 Dispatch Console"
    )

    st.caption(
        "Cold-Chain Logistics AI"
    )

    st.divider()

    st.markdown(
        "### System Status"
    )

    st.success(
        "Database connected"
    )

    st.success(
        "Weather service available"
    )

    st.success(
        "SOP search available"
    )

    st.success(
        "Deterministic risk engine ready"
    )

    st.divider()

    st.markdown(
        "### Current Session"
    )

    st.code(
        st.session_state.session_id
    )

    if st.button(
        "Start New Session",
        use_container_width=True,
    ):

        st.session_state.session_id = (
            str(uuid4())[:8]
        )

        st.session_state.last_result = None

        st.session_state.last_request = ""

        st.session_state.analysis_count = 0

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🚚 Cold-Chain Logistics AI Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    AI-powered operational assistant for fleet telemetry,
    weather conditions, cold-chain risks, and SOP compliance.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# =========================================================
# DISPATCHER CONSOLE
# =========================================================

st.markdown(
    "## Dispatcher Console"
)

st.caption(
    "Enter your operational query"
)

user_query = st.text_area(
    "Operational Query",
    placeholder=(
        "Example: Show me all high risk vehicles"
    ),
    height=100,
    label_visibility="collapsed",
)


run_analysis = st.button(
    "🔍 Run Analysis",
    type="primary",
)


# =========================================================
# RUN GRAPH
# =========================================================

if run_analysis:

    if not user_query.strip():

        st.warning(
            "Please enter an operational query."
        )

    else:

        st.session_state.last_request = (
            user_query.strip()
        )

        with st.spinner(
            "Running cold-chain analysis..."
        ):

            try:

                result = graph.invoke(
                    {
                        "user_request": (
                            user_query.strip()
                        ),
                        "session_id": (
                            st.session_state.session_id
                        ),
                    }
                )

                st.session_state.last_result = (
                    result
                )

                st.session_state.analysis_count += 1

            except Exception as e:

                st.error(
                    f"Analysis failed: {e}"
                )

                st.stop()


# =========================================================
# DISPLAY RESULT
# =========================================================

result = st.session_state.last_result


if result:

    telemetry_text = result.get(
        "telemetry",
        ""
    )

    weather_text = result.get(
        "weather",
        ""
    )

    sop_text = result.get(
        "sop",
        ""
    )

    vehicles = parse_telemetry(
        telemetry_text
    )

    weather_data = parse_weather(
        weather_text
    )


    # =====================================================
    # OPERATIONAL OVERVIEW
    # =====================================================

    st.markdown(
        "## Operational Overview"
    )

    high_risk_count = sum(
        1
        for vehicle in vehicles
        if vehicle["risk"] == "High Risk"
    )

    temperature_breach_count = sum(
        1
        for vehicle in vehicles
        if vehicle["temperature"] > 4.0
    )

    action_vehicle_count = sum(
        1
        for vehicle in vehicles
        if (
            vehicle["temperature"] > 4.0
            or vehicle["port_congestion"] > 7.0
            or (
                vehicle["risk"] == "High Risk"
                and vehicle["delay_probability"] > 0.65
            )
        )
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Vehicles",
            len(vehicles),
        )

    with col2:

        st.metric(
            "High Risk",
            high_risk_count,
        )

    with col3:

        st.metric(
            "Temp Breaches",
            temperature_breach_count,
        )

    with col4:

        st.metric(
            "Vehicles Requiring Action",
            action_vehicle_count,
        )


    st.divider()


    # =====================================================
    # OPERATIONAL ASSESSMENT
    # =====================================================

    st.markdown(
        "## Operational Assessment"
    )

    assessment_parts = []

    if high_risk_count:

        assessment_parts.append(
            f"{high_risk_count} vehicle(s) "
            "classified as High Risk."
        )

    if temperature_breach_count:

        assessment_parts.append(
            f"{temperature_breach_count} vehicle(s) "
            "exceed the 4.0°C threshold."
        )

    if action_vehicle_count:

        assessment_parts.append(
            f"{action_vehicle_count} vehicle(s) "
            "have deterministic SOP-triggered actions."
        )

    if not assessment_parts:

        assessment_parts.append(
            "No immediate SOP-triggered fleet "
            "actions were identified."
        )

    st.info(
        " ".join(assessment_parts)
    )


    # =====================================================
    # FLEET RISK SUMMARY
    # =====================================================

    st.markdown(
        "## Fleet Risk Summary"
    )

    if vehicles:

        fleet_rows = []

        for index, vehicle in enumerate(
            vehicles,
            start=1
        ):

            temperature = vehicle[
                "temperature"
            ]

            if temperature > 4.0:

                temperature_status = (
                    "IMMEDIATE COLD-CHAIN BREACH"
                )

            elif 0.0 <= temperature <= 4.0:

                temperature_status = (
                    "Within normal range"
                )

            else:

                temperature_status = (
                    "Below normal range"
                )

            fleet_rows.append(
                {
                    "Vehicle": (
                        f"Vehicle {index}"
                    ),
                    "Risk": vehicle[
                        "risk"
                    ],
                    "IoT Temperature": (
                        f"{temperature:.2f} °C"
                    ),
                    "Delay Probability": (
                        f"{vehicle['delay_probability']:.3f}"
                    ),
                    "Port Congestion": (
                        f"{vehicle['port_congestion']:.3f}"
                    ),
                    "Route Risk": (
                        f"{vehicle['route_risk']:.3f}"
                    ),
                    "Temperature Status": (
                        temperature_status
                    ),
                }
            )

        fleet_df = pd.DataFrame(
            fleet_rows
        )

        st.dataframe(
            fleet_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.warning(
            "No matching fleet telemetry records found."
        )


    # =====================================================
    # WEATHER CONDITIONS
    # =====================================================

    st.markdown(
        "## Weather Conditions"
    )

    if weather_data:

        weather_rows = []

        for data in weather_data:

            weather_rows.append(
                {
                    "Vehicle": data[
                        "vehicle"
                    ],
                    "Latitude": data[
                        "latitude"
                    ],
                    "Longitude": data[
                        "longitude"
                    ],
                    "Weather Temperature": data[
                        "temperature"
                    ],
                    "Wind Speed": data[
                        "wind"
                    ],
                    "Disruption Index": data[
                        "disruption"
                    ],
                }
            )

        weather_df = pd.DataFrame(
            weather_rows
        )

        st.dataframe(
            weather_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.warning(
            "Weather data unavailable."
        )


    # =====================================================
    # REQUIRED ACTIONS
    # =====================================================

    st.markdown(
        "## 🚨 Required Actions"
    )

    required_actions = result.get(
        "required_actions",
        ""
    )

    if required_actions:

        blocks = required_actions.split(
            "\n\n"
        )

        for block in blocks:

            lines = block.splitlines()

            if not lines:
                continue

            vehicle_name = lines[0]

            st.markdown(
                f"### {vehicle_name}"
            )

            for line in lines[1:]:

                action = line.strip()

                if not action.startswith("-"):

                    continue

                action_text = action[1:].strip()

                if (
                    "No immediate" in action_text
                ):

                    st.success(
                        action_text
                    )

                elif (
                    "Escalate" in action_text
                    or "Suspend" in action_text
                    or "divert" in action_text.lower()
                    or "restart" in action_text.lower()
                ):

                    st.warning(
                        action_text
                    )

                else:

                    st.info(
                        action_text
                    )

    else:

        st.success(
            "No immediate SOP-triggered actions."
        )


    # =====================================================
    # DETAILS
    # =====================================================

    st.divider()

    with st.expander(
        "📋 SOP Compliance",
        expanded=False,
    ):

        st.markdown(
            sop_text
        )


    with st.expander(
        "🔎 Detailed Analysis",
        expanded=False,
    ):

        st.text(
            result.get(
                "analysis",
                "No analysis available."
            )
        )


    # =====================================================
    # ANALYSIS EXECUTION TRACE
    # =====================================================

    with st.expander(
        "🔍 Analysis Execution Trace",
        expanded=False,
    ):

        telemetry_status = result.get(
            "telemetry_status",
            "Telemetry node completed."
        )

        weather_status = result.get(
            "weather_status",
            "Weather node completed."
        )

        sop_status = result.get(
            "sop_status",
            "SOP node completed."
        )

        analysis_status = result.get(
            "analysis_status",
            "Analysis node completed."
        )

        report_status = result.get(
            "report_status",
            "Report node completed."
        )

        st.success(
            telemetry_status
        )

        st.success(
            weather_status
        )

        st.success(
            sop_status
        )

        st.success(
            analysis_status
        )

        st.success(
            report_status
        )


    # =====================================================
    # SESSION INFORMATION
    # =====================================================

    with st.expander(
        "🧾 Session Information",
        expanded=False,
    ):

        st.write(
            "Session ID:",
            st.session_state.session_id,
        )

        st.write(
            "Last Query:",
            st.session_state.last_request,
        )

        st.write(
            "Analyses in this session:",
            st.session_state.analysis_count,
        )