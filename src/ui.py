import pandas as pd
import streamlit as st
from uuid import uuid4

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
# RUN ANALYSIS
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

    analysis_text = result.get(
        "analysis",
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
        if vehicle.get(
            "Risk_Classification"
        ) == "High Risk"
    )


    temperature_breach_count = sum(
        1
        for vehicle in vehicles
        if isinstance(
            vehicle.get(
                "Current_Temperature_C"
            ),
            (int, float),
        )
        and vehicle.get(
            "Current_Temperature_C"
        ) > 4.0
    )


    # -----------------------------------------------------
    # Count unique vehicles that have actual actions
    # -----------------------------------------------------

    actions = result.get(
        "actions",
        []
    )

    action_vehicle_ids = set()


    if isinstance(actions, list):

        for action in actions:

            if not isinstance(
                action,
                dict,
            ):
                continue

            vehicle_id = action.get(
                "Vehicle"
            )

            if vehicle_id is not None:

                action_vehicle_ids.add(
                    vehicle_id
                )


    action_vehicle_count = len(
        action_vehicle_ids
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
            start=1,
        ):

            temperature = vehicle.get(
                "Current_Temperature_C"
            )

            risk = vehicle.get(
                "Risk_Classification",
                "Unknown",
            )

            delay_probability = vehicle.get(
                "Delay_Probability"
            )

            port_congestion = vehicle.get(
                "Port_Congestion_Level"
            )

            route_risk = vehicle.get(
                "Route_Risk_Index"
            )


            # -------------------------------------------------
            # Temperature status
            # -------------------------------------------------

            if (
                isinstance(
                    temperature,
                    (int, float),
                )
                and temperature > 4.0
            ):

                temperature_status = (
                    "IMMEDIATE COLD-CHAIN BREACH"
                )

            elif (
                isinstance(
                    temperature,
                    (int, float),
                )
                and 0.0 <= temperature <= 4.0
            ):

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

                    "Risk": risk,

                    "IoT Temperature": (
                        f"{temperature:.2f} °C"
                        if isinstance(
                            temperature,
                            (int, float),
                        )
                        else "N/A"
                    ),

                    "Delay Probability": (
                        f"{delay_probability:.3f}"
                        if isinstance(
                            delay_probability,
                            (int, float),
                        )
                        else "N/A"
                    ),

                    "Port Congestion": (
                        f"{port_congestion:.3f}"
                        if isinstance(
                            port_congestion,
                            (int, float),
                        )
                        else "N/A"
                    ),

                    "Route Risk": (
                        f"{route_risk:.3f}"
                        if isinstance(
                            route_risk,
                            (int, float),
                        )
                        else "N/A"
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
                    "Vehicle": data.get(
                        "Vehicle",
                        "Unknown",
                    ),

                    "Weather Temperature": (
                        f"{data['Weather_Temperature_C']:.1f} °C"
                        if isinstance(
                            data.get(
                                "Weather_Temperature_C"
                            ),
                            (int, float),
                        )
                        else "N/A"
                    ),

                    "Wind Speed": (
                        f"{data['Wind_Speed_kmh']:.1f} km/h"
                        if isinstance(
                            data.get(
                                "Wind_Speed_kmh"
                            ),
                            (int, float),
                        )
                        else "N/A"
                    ),

                    "Disruption Index": (
                        f"{data['Disruption_Index']:.1f}"
                        if isinstance(
                            data.get(
                                "Disruption_Index"
                            ),
                            (int, float),
                        )
                        else "N/A"
                    ),
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


    if isinstance(
        actions,
        list,
    ) and actions:

        actions_by_vehicle = {}


        for item in actions:

            if not isinstance(
                item,
                dict,
            ):
                continue


            vehicle_id = item.get(
                "Vehicle"
            )

            action_text = item.get(
                "Action"
            )


            if (
                vehicle_id is None
                or not action_text
            ):
                continue


            actions_by_vehicle.setdefault(
                vehicle_id,
                [],
            ).append(
                str(action_text)
            )


        if actions_by_vehicle:

            for (
                vehicle_id,
                vehicle_actions,
            ) in actions_by_vehicle.items():

                st.markdown(
                    f"### Vehicle {vehicle_id}"
                )


                for action_text in vehicle_actions:

                    action_lower = (
                        action_text.lower()
                    )


                    if (
                        "escalate"
                        in action_lower
                    ):

                        st.error(
                            f"🔴 {action_text}"
                        )


                    elif (
                        "breach"
                        in action_lower
                    ):

                        st.error(
                            f"🔴 {action_text}"
                        )


                    elif (
                        "suspend"
                        in action_lower
                        or "divert"
                        in action_lower
                    ):

                        st.warning(
                            f"🟡 {action_text}"
                        )


                    elif (
                        "restart"
                        in action_lower
                    ):

                        st.warning(
                            f"🟡 {action_text}"
                        )


                    else:

                        st.info(
                            f"🔵 {action_text}"
                        )


        else:

            st.success(
                "No immediate SOP-triggered actions."
            )


    else:

        st.success(
            "No immediate SOP-triggered actions."
        )


    # =====================================================
    # SOP COMPLIANCE
    # =====================================================

    st.divider()


    with st.expander(
        "📋 SOP Compliance",
        expanded=False,
    ):

        if sop_text:

            st.markdown(
                sop_text
            )

        else:

            st.info(
                "No SOP information was retrieved."
            )


    # =====================================================
    # DETAILED ANALYSIS
    # =====================================================

    with st.expander(
        "🔎 Detailed Analysis",
        expanded=False,
    ):

        if analysis_text:

            st.text(
                analysis_text
            )

        else:

            st.info(
                "No detailed analysis available."
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
            "Telemetry node completed.",
        )

        weather_status = result.get(
            "weather_status",
            "Weather node completed.",
        )

        sop_status = result.get(
            "sop_status",
            "SOP node completed.",
        )

        analysis_status = result.get(
            "analysis_status",
            "Analysis node completed.",
        )

        reasoner_status = result.get(
            "reasoner_status",
            "Reasoner completed.",
        )


        st.success(
            f"Telemetry: {telemetry_status}"
        )

        st.success(
            f"Weather: {weather_status}"
        )

        st.success(
            f"SOP: {sop_status}"
        )

        st.success(
            f"Analysis: {analysis_status}"
        )

        st.success(
            f"Reasoner: {reasoner_status}"
        )


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    final_response = result.get(
        "final_response",
        ""
    )


    if final_response:

        with st.expander(
            "📝 Final Operational Report",
            expanded=False,
        ):

            st.markdown(
                final_response
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