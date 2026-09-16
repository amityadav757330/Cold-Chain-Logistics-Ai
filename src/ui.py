import re
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from src.orchestrator import build_graph, parse_telemetry


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
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .kpi-card {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #30363d;
        background-color: #161b22;
        min-height: 120px;
    }

    .kpi-title {
        color: #9ca3af;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 700;
    }

    .section-title {
        font-size: 23px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .risk-high {
        color: #ff6b6b;
        font-weight: 700;
    }

    .risk-normal {
        color: #51cf66;
        font-weight: 700;
    }

    .action-box {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        background-color: #161b22;
        margin-bottom: 10px;
    }

    .session-info {
        color: #8b949e;
        font-size: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


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
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Dispatch Console")

    st.markdown(
        """
        **System Status**

        🟢 Database: Connected  
        🟢 Weather API: Available  
        🟢 SOP Search: Available  
        🟢 Risk Engine: Active
        """
    )

    st.divider()

    st.subheader("Current Session")

    if "session_id" not in st.session_state:

        st.session_state["session_id"] = str(
            uuid.uuid4()
        )[:8]

    st.markdown(
        f"""
        <div class="session-info">
        Session ID: {st.session_state["session_id"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "analysis_time" in st.session_state:

        st.markdown(
            f"""
            <div class="session-info">
            Last analysis:<br>
            {st.session_state["analysis_time"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# DISPATCHER CONSOLE
# =========================================================

st.markdown(
    '<div class="section-title">Dispatcher Console</div>',
    unsafe_allow_html=True,
)

user_request = st.text_area(
    "Enter your operational query",
    placeholder=(
        "Example: Analyze the current fleet and identify "
        "any cold-chain risks and required actions."
    ),
    height=100,
)


# =========================================================
# RUN ANALYSIS
# =========================================================

if st.button(
    "🚀 Run Analysis",
    type="primary",
    use_container_width=False,
):

    if not user_request.strip():

        st.warning(
            "Please enter an operational query."
        )

    else:

        with st.spinner(
            "Running telemetry, weather, and SOP analysis..."
        ):

            try:

                # -------------------------------------------------
                # CREATE GRAPH
                # -------------------------------------------------

                graph = build_graph()

                # -------------------------------------------------
                # RUN WORKFLOW
                # -------------------------------------------------

                result = graph.invoke(
                    {
                        "user_request": user_request
                    }
                )

                # -------------------------------------------------
                # SAVE SESSION RESULTS
                # -------------------------------------------------

                st.session_state[
                    "result"
                ] = result

                st.session_state[
                    "last_response"
                ] = result.get(
                    "final_response",
                    "No response was generated."
                )

                st.session_state[
                    "tool_trace"
                ] = result.get(
                    "tool_trace",
                    []
                )

                st.session_state[
                    "analysis_time"
                ] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                st.session_state[
                    "analysis_error"
                ] = None

            except Exception as e:

                st.session_state[
                    "analysis_error"
                ] = str(e)

                st.error(
                    "An error occurred while running "
                    "the analysis."
                )

                st.exception(e)


# =========================================================
# DISPLAY ANALYSIS
# =========================================================

if "result" in st.session_state:

    result = st.session_state["result"]

    telemetry = result.get(
        "telemetry",
        ""
    )

    weather = result.get(
        "weather",
        ""
    )

    sop = result.get(
        "sop",
        ""
    )

    required_actions = result.get(
        "required_actions",
        ""
    )

    analysis = result.get(
        "analysis",
        ""
    )

    # =====================================================
    # PARSE TELEMETRY
    # =====================================================

    vehicles = parse_telemetry(
        telemetry
    )

    # =====================================================
    # CALCULATE KPIs
    # =====================================================

    total_vehicles = len(
        vehicles
    )

    high_risk_vehicles = sum(
        1
        for vehicle in vehicles
        if vehicle["risk"] == "High Risk"
    )

    temperature_breaches = sum(
        1
        for vehicle in vehicles
        if vehicle["temperature"] > 4.0
    )

    action_vehicles = sum(
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

    # =====================================================
    # OPERATIONAL OVERVIEW
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Operational Overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            label="🚚 Total Vehicles",
            value=total_vehicles,
        )

    with col2:

        st.metric(
            label="⚠️ High Risk",
            value=high_risk_vehicles,
        )

    with col3:

        st.metric(
            label="🌡️ Temp Breaches",
            value=temperature_breaches,
        )

    with col4:

        st.metric(
            label="🚨 Vehicles Requiring Action",
            value=action_vehicles,
        )

    # =====================================================
    # OPERATIONAL ASSESSMENT
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Operational Assessment</div>',
        unsafe_allow_html=True,
    )

    # Extract assessment from final response
    final_response = st.session_state.get(
        "last_response",
        ""
    )

    assessment_text = ""

    if "### Operational Assessment" in final_response:

        assessment_text = final_response.split(
            "### Operational Assessment",
            1
        )[1]

        if "### Fleet Risk Summary" in assessment_text:

            assessment_text = assessment_text.split(
                "### Fleet Risk Summary",
                1
            )[0]

    assessment_text = assessment_text.strip()

    if assessment_text:

        st.info(
            assessment_text
        )

    else:

        st.info(
            "Operational assessment generated successfully."
        )

    # =====================================================
    # FLEET RISK TABLE
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Fleet Risk Summary</div>',
        unsafe_allow_html=True,
    )

    if vehicles:

        fleet_table = []

        for index, vehicle in enumerate(
            vehicles,
            start=1
        ):

            temperature = vehicle[
                "temperature"
            ]

            if temperature > 4.0:

                temperature_status = (
                    "Immediate Breach"
                )

            elif temperature >= 0.0:

                temperature_status = (
                    "Normal"
                )

            else:

                temperature_status = (
                    "Below Range"
                )

            fleet_table.append(
                {
                    "Vehicle": f"Vehicle {index}",
                    "Risk": vehicle["risk"],
                    "IoT Temp (°C)": round(
                        temperature,
                        2,
                    ),
                    "Temp Status": temperature_status,
                    "Delay Probability": round(
                        vehicle[
                            "delay_probability"
                        ],
                        3,
                    ),
                    "Port Congestion": round(
                        vehicle[
                            "port_congestion"
                        ],
                        3,
                    ),
                    "Route Risk": round(
                        vehicle[
                            "route_risk"
                        ],
                        3,
                    ),
                }
            )

        fleet_df = pd.DataFrame(
            fleet_table
        )

        st.dataframe(
            fleet_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.warning(
            "No fleet telemetry records were available."
        )

    # =====================================================
    # WEATHER CONDITIONS
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Weather Conditions</div>',
        unsafe_allow_html=True,
    )

    weather_rows = []

    # -----------------------------------------------------
    # Parse weather text
    # -----------------------------------------------------

    vehicle_blocks = re.split(
        r"\n\s*\n",
        weather.strip()
    )

    for block in vehicle_blocks:

        vehicle_match = re.search(
            r"Vehicle\s+(\d+)",
            block,
            re.IGNORECASE
        )

        latitude_match = re.search(
            r"Latitude:\s*([-+]?\d*\.?\d+)",
            block,
            re.IGNORECASE
        )

        longitude_match = re.search(
            r"Longitude:\s*([-+]?\d*\.?\d+)",
            block,
            re.IGNORECASE
        )

        temperature_match = re.search(
            r"Current temperature:\s*([-+]?\d*\.?\d+)",
            block,
            re.IGNORECASE
        )

        wind_match = re.search(
            r"Wind speed:\s*([-+]?\d*\.?\d+)",
            block,
            re.IGNORECASE
        )

        disruption_match = re.search(
            r"Disruption index:\s*([-+]?\d*\.?\d+)",
            block,
            re.IGNORECASE
        )

        if vehicle_match:

            weather_rows.append(
                {
                    "Vehicle": (
                        f"Vehicle {vehicle_match.group(1)}"
                    ),
                    "Latitude": (
                        round(
                            float(latitude_match.group(1)),
                            4,
                        )
                        if latitude_match
                        else "N/A"
                    ),
                    "Longitude": (
                        round(
                            float(longitude_match.group(1)),
                            4,
                        )
                        if longitude_match
                        else "N/A"
                    ),
                    "Weather Temp (°C)": (
                        round(
                            float(
                                temperature_match.group(1)
                            ),
                            1,
                        )
                        if temperature_match
                        else "N/A"
                    ),
                    "Wind (km/h)": (
                        round(
                            float(
                                wind_match.group(1)
                            ),
                            1,
                        )
                        if wind_match
                        else "N/A"
                    ),
                    "Disruption Index": (
                        float(
                            disruption_match.group(1)
                        )
                        if disruption_match
                        else "N/A"
                    ),
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
            "Weather information could not be parsed."
        )

    # =====================================================
    # REQUIRED ACTIONS
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">🚨 Required Actions</div>',
        unsafe_allow_html=True,
    )

    if required_actions:

        # -------------------------------------------------
        # Split vehicle sections
        # -------------------------------------------------

        action_blocks = re.split(
            r"\n(?=Vehicle\s+\d+:)",
            required_actions.strip()
        )

        for block in action_blocks:

            if not block.strip():
                continue

            lines = block.strip().splitlines()

            vehicle_title = lines[0].strip()

            actions = [
                line.strip("- ").strip()
                for line in lines[1:]
                if line.strip()
            ]

            st.markdown(
                f"""
                <div class="action-box">
                <strong>{vehicle_title}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for action in actions:

                if (
                    "No immediate SOP-triggered action"
                    in action
                ):

                    st.success(
                        f"✓ {action}"
                    )

                else:

                    st.warning(
                        f"⚠️ {action}"
                    )

    else:

        st.success(
            "No required actions were generated."
        )

    # =====================================================
    # DETAILED ANALYSIS
    # =====================================================

    st.divider()

    with st.expander(
        "📊 Detailed Risk Analysis",
        expanded=False,
    ):

        if analysis:

            st.text(
                analysis
            )

        else:

            st.info(
                "No detailed analysis available."
            )

    # =====================================================
    # SOP COMPLIANCE
    # =====================================================

    st.divider()

    with st.expander(
        "📋 SOP Compliance",
        expanded=False,
    ):

        if sop:

            st.markdown(
                sop
            )

        else:

            st.info(
                "No SOP information was retrieved."
            )

    # =====================================================
    # EXECUTION TRACE
    # =====================================================

    st.divider()

    with st.expander(
        "🔍 Analysis Execution Trace",
        expanded=False,
    ):

        trace = st.session_state.get(
            "tool_trace",
            []
        )

        if trace:

            for index, step in enumerate(
                trace,
                start=1
            ):

                st.success(
                    f"{index}. {step}"
                )

        else:

            st.info(
                "No execution trace available."
            )

    # =====================================================
    # RAW RESPONSE
    # =====================================================

    st.divider()

    with st.expander(
        "📝 Raw Agent Response",
        expanded=False,
    ):

        st.markdown(
            st.session_state.get(
                "last_response",
                "No response available."
            )
        )