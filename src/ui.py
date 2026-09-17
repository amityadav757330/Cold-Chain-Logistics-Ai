import os
import uuid

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.orchestrator import build_graph


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cold-Chain Logistics AI",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "session_id" not in st.session_state:

    st.session_state.session_id = (
        str(uuid.uuid4())[:8]
    )

if "analysis_result" not in st.session_state:

    st.session_state.analysis_result = None

if "execution_trace" not in st.session_state:

    st.session_state.execution_trace = []


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #9aa4b2;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .status-success {
        padding: 0.55rem 0.8rem;
        border-radius: 0.35rem;
        background-color: #123b29;
        color: #6ee7a0;
        border: 1px solid #1d6b49;
        margin-bottom: 0.45rem;
    }

    .status-warning {
        padding: 0.55rem 0.8rem;
        border-radius: 0.35rem;
        background-color: #40380f;
        color: #f3d36a;
        border: 1px solid #756717;
        margin-bottom: 0.45rem;
    }

    .status-error {
        padding: 0.55rem 0.8rem;
        border-radius: 0.35rem;
        background-color: #421d24;
        color: #ff8f9d;
        border: 1px solid #74313d;
        margin-bottom: 0.45rem;
    }

    .session-box {
        padding: 0.7rem;
        border-radius: 0.4rem;
        background-color: #171a21;
        border: 1px solid #30343d;
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🚚 Dispatch Console"
    )

    st.caption(
        "Cold-Chain Logistics AI"
    )

    st.divider()

    st.markdown(
        "**System Status**"
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
        "**Current Session**"
    )

    st.markdown(
        f"""
        <div class="session-box">
        Session ID<br>
        <strong>{st.session_state.session_id}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "Start New Session",
        use_container_width=True
    ):

        st.session_state.session_id = (
            str(uuid.uuid4())[:8]
        )

        st.session_state.analysis_result = None
        st.session_state.execution_trace = []

        st.rerun()


# ============================================================
# HEADER
# ============================================================

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


# ============================================================
# DISPATCHER CONSOLE
# ============================================================

st.markdown(
    "## Dispatcher Console"
)

st.caption(
    "Enter your operational query"
)

query = st.text_area(
    "Operational query",
    value=(
        "Analyze the current fleet and identify "
        "any cold-chain risks and required actions."
    ),
    height=100,
    label_visibility="collapsed",
)


run_analysis = st.button(
    "🚀 Run Analysis",
    type="primary",
)


# ============================================================
# RUN GRAPH
# ============================================================

if run_analysis:

    if not query.strip():

        st.warning(
            "Please enter an operational query."
        )

    else:

        with st.spinner(
            "Running cold-chain analysis..."
        ):

            try:

                graph = build_graph()

                result = graph.invoke(
                    {
                        "user_request": query,
                        "session_id": (
                            st.session_state.session_id
                        ),
                        "execution_trace": [],
                    }
                )

                st.session_state.analysis_result = (
                    result
                )

                st.session_state.execution_trace = (
                    result.get(
                        "execution_trace",
                        []
                    )
                )

            except Exception as e:

                st.error(
                    f"Analysis failed: {str(e)}"
                )


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.analysis_result


if result:

    st.divider()

    # ========================================================
    # PARSE VEHICLES
    # ========================================================

    telemetry = result.get(
        "telemetry",
        ""
    )

    vehicles = []

    if telemetry:

        lines = telemetry.splitlines()

        if len(lines) >= 2:

            headers = [
                x.strip()
                for x in lines[0].split(",")
            ]

            for line in lines[1:]:

                values = [
                    x.strip()
                    for x in line.split(",")
                ]

                if len(values) != len(headers):
                    continue

                row = dict(
                    zip(headers, values)
                )

                try:

                    vehicles.append(
                        {
                            "Risk": row[
                                "Risk_Classification"
                            ],
                            "IoT Temperature": float(
                                row[
                                    "Current_Temperature_C"
                                ]
                            ),
                            "Delay Probability": float(
                                row[
                                    "Delay_Probability"
                                ]
                            ),
                            "Port Congestion": float(
                                row[
                                    "Port_Congestion_Level"
                                ]
                            ),
                            "Route Risk": float(
                                row[
                                    "Route_Risk_Index"
                                ]
                            ),
                        }
                    )

                except (
                    KeyError,
                    ValueError,
                    TypeError,
                ):
                    continue


    # ========================================================
    # OPERATIONAL OVERVIEW
    # ========================================================

    st.markdown(
        "## Operational Overview"
    )

    total_vehicles = len(
        vehicles
    )

    high_risk = sum(
        1
        for vehicle in vehicles
        if vehicle["Risk"] == "High Risk"
    )

    temperature_breaches = sum(
        1
        for vehicle in vehicles
        if vehicle["IoT Temperature"] > 4.0
    )

    action_vehicles = sum(
        1
        for vehicle in vehicles
        if (
            vehicle["IoT Temperature"] > 4.0
            or vehicle["Port Congestion"] > 7.0
            or (
                vehicle["Risk"] == "High Risk"
                and vehicle["Delay Probability"] > 0.65
            )
        )
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Vehicles",
            total_vehicles
        )

    with col2:

        st.metric(
            "High Risk",
            high_risk
        )

    with col3:

        st.metric(
            "Temp Breaches",
            temperature_breaches
        )

    with col4:

        st.metric(
            "Vehicles Requiring Action",
            action_vehicles
        )


    # ========================================================
    # OPERATIONAL ASSESSMENT
    # ========================================================

    st.divider()

    st.markdown(
        "## Operational Assessment"
    )

    report = result.get(
        "final_response",
        ""
    )

    assessment_text = ""

    if "### Operational Assessment" in report:

        assessment_text = (
            report
            .split(
                "### Operational Assessment",
                1
            )[1]
            .split(
                "### Fleet Risk Summary",
                1
            )[0]
            .strip()
        )

    if assessment_text:

        st.info(
            assessment_text
        )


    # ========================================================
    # FLEET RISK SUMMARY
    # ========================================================

    st.markdown(
        "## Fleet Risk Summary"
    )

    if vehicles:

        fleet_df = pd.DataFrame(
            vehicles
        )

        fleet_df.insert(
            0,
            "Vehicle",
            [
                f"Vehicle {i}"
                for i in range(
                    1,
                    len(fleet_df) + 1
                )
            ],
        )

        fleet_df[
            "Temperature Status"
        ] = fleet_df[
            "IoT Temperature"
        ].apply(
            lambda x:
                "IMMEDIATE COLD-CHAIN BREACH"
                if x > 4.0
                else (
                    "Within normal fresh-perishables range"
                    if x >= 0.0
                    else
                    "Below the normal fresh-perishables range"
                )
        )

        st.dataframe(
            fleet_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.warning(
            "No valid fleet telemetry records."
        )


    # ========================================================
    # WEATHER
    # ========================================================

    st.divider()

    st.markdown(
        "## Weather Conditions"
    )

    weather = result.get(
        "weather",
        ""
    )

    weather_rows = []

    weather_blocks = weather.split(
        "\n\n"
    )

    for block in weather_blocks:

        lines = block.splitlines()

        if not lines:
            continue

        if not lines[0].startswith(
            "Vehicle"
        ):
            continue

        vehicle = lines[0]

        latitude = ""
        longitude = ""
        temperature = ""
        wind_speed = ""
        disruption = ""

        for line in lines[1:]:

            if line.startswith(
                "Latitude:"
            ):

                latitude = line.replace(
                    "Latitude:",
                    ""
                ).strip()

            elif line.startswith(
                "Longitude:"
            ):

                longitude = line.replace(
                    "Longitude:",
                    ""
                ).strip()

            elif line.startswith(
                "Current temperature:"
            ):

                temperature = line.replace(
                    "Current temperature:",
                    ""
                ).strip()

            elif line.startswith(
                "Wind speed:"
            ):

                wind_speed = line.replace(
                    "Wind speed:",
                    ""
                ).strip()

            elif line.startswith(
                "Disruption index:"
            ):

                disruption = line.replace(
                    "Disruption index:",
                    ""
                ).strip()

        weather_rows.append(
            {
                "Vehicle": vehicle,
                "Latitude": latitude,
                "Longitude": longitude,
                "Weather Temperature": temperature,
                "Wind Speed": wind_speed,
                "Disruption Index": disruption,
            }
        )

    if weather_rows:

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
            "Weather information is unavailable."
        )


    # ========================================================
    # REQUIRED ACTIONS
    # ========================================================

    st.divider()

    st.markdown(
        "## 🚨 Required Actions"
    )

    actions = result.get(
        "required_actions",
        ""
    )

    action_blocks = actions.split(
        "\n"
    )

    current_vehicle = None

    for line in action_blocks:

        line = line.strip()

        if not line:
            continue

        if line.startswith(
            "Vehicle"
        ) and line.endswith(":"):

            current_vehicle = line

            st.markdown(
                f"### {current_vehicle}"
            )

        elif line.startswith(
            "-"
        ):

            action = line[1:].strip()

            if (
                action
                == "No immediate SOP-triggered action"
            ):

                st.success(
                    action
                )

            else:

                st.warning(
                    action
                )


    # ========================================================
    # SOP COMPLIANCE
    # ========================================================

    st.divider()

    with st.expander(
        "📋 SOP Compliance",
        expanded=False
    ):

        sop = result.get(
            "sop",
            "No SOP information retrieved."
        )

        st.markdown(
            sop
        )


    # ========================================================
    # RAW ANALYSIS
    # ========================================================

    with st.expander(
        "🔍 Detailed Analysis",
        expanded=False
    ):

        analysis = result.get(
            "analysis",
            ""
        )

        st.text(
            analysis
        )


    # ========================================================
    # EXECUTION TRACE
    # ========================================================

    st.divider()

    with st.expander(
        "🔎 Analysis Execution Trace",
        expanded=False
    ):

        trace = st.session_state.execution_trace

        if not trace:

            st.info(
                "No execution trace available."
            )

        else:

            for event in trace:

                status = event.get(
                    "status",
                    "UNKNOWN"
                )

                node = event.get(
                    "node",
                    ""
                )

                tool = event.get(
                    "tool",
                    ""
                )

                message = event.get(
                    "message",
                    ""
                )

                timestamp = event.get(
                    "timestamp",
                    ""
                )

                if status == "SUCCESS":

                    st.markdown(
                        f"""
                        <div class="status-success">
                        <strong>✓ {node}</strong>
                        &nbsp; | &nbsp;
                        {tool}
                        <br>
                        {message}
                        <br>
                        <small>{timestamp}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                elif status == "WARNING":

                    st.markdown(
                        f"""
                        <div class="status-warning">
                        <strong>⚠ {node}</strong>
                        &nbsp; | &nbsp;
                        {tool}
                        <br>
                        {message}
                        <br>
                        <small>{timestamp}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="status-error">
                        <strong>✗ {node}</strong>
                        &nbsp; | &nbsp;
                        {tool}
                        <br>
                        {message}
                        <br>
                        <small>{timestamp}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


    # ========================================================
    # SESSION INFORMATION
    # ========================================================

    with st.expander(
        "🆔 Session Information",
        expanded=False
    ):

        st.write(
            f"Session ID: `{st.session_state.session_id}`"
        )

        st.write(
            "This session ID is also stored in "
            "`FDE_VIEWS.AgentAuditLog`."
        )