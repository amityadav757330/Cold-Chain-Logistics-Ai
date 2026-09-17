import os
from datetime import datetime
from typing import Any
from typing_extensions import TypedDict

import pyodbc
from langgraph.graph import StateGraph, START, END

from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
    search_compliance_sop,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('FDE_DB_SERVER', 'localhost')};"
    f"DATABASE={os.getenv('FDE_DB_NAME', 'ColdChainLogistics')};"
    f"UID={os.getenv('FDE_DB_USER')};"
    f"PWD={os.getenv('FDE_DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)


# ============================================================
# GRAPH STATE
# ============================================================

class AgentState(TypedDict, total=False):
    user_request: str
    session_id: str

    telemetry: str
    weather: str
    sop: str

    analysis: str
    required_actions: str
    final_response: str

    execution_trace: list[dict[str, Any]]


# ============================================================
# AUDIT LOGGING
# ============================================================

def write_audit_log(
    session_id: str,
    node_executed: str,
    tool_name: str,
    content: str,
):
    """
    Write one audit record to FDE_VIEWS.AgentAuditLog.

    The application uses the restricted USR_FDE_RO SQL login.
    Audit failures are intentionally isolated so that an audit
    problem does not prevent the operational report from being
    generated.
    """

    try:

        conn = pyodbc.connect(
            CONNECTION_STRING,
            timeout=10
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO FDE_VIEWS.AgentAuditLog
            (
                SessionID,
                NodeExecuted,
                ToolName,
                Content
            )
            VALUES (?, ?, ?, ?)
            """,
            session_id,
            node_executed,
            tool_name,
            str(content)[:8000],
        )

        conn.commit()

        cursor.close()
        conn.close()

        return True, "Audit log written successfully."

    except Exception as e:

        return False, f"Audit logging error: {str(e)}"


# ============================================================
# EXECUTION TRACE
# ============================================================

def add_trace(
    state: AgentState,
    node: str,
    tool: str,
    status: str,
    message: str,
):
    """
    Add an execution event to the Streamlit trace.
    """

    trace = list(
        state.get("execution_trace", [])
    )

    trace.append(
        {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "node": node,
            "tool": tool,
            "status": status,
            "message": message,
        }
    )

    return trace


# ============================================================
# TELEMETRY PARSER
# ============================================================

def parse_telemetry(telemetry_text):
    """
    Convert the secure-view text result into Python dictionaries.
    """

    if not telemetry_text:
        return []

    lines = telemetry_text.splitlines()

    if len(lines) < 2:
        return []

    headers = [
        item.strip()
        for item in lines[0].split(",")
    ]

    vehicles = []

    for line in lines[1:]:

        values = [
            item.strip()
            for item in line.split(",")
        ]

        if len(values) != len(headers):
            continue

        row = dict(
            zip(headers, values)
        )

        try:

            vehicle = {
                "timestamp": row["Timestamp"],
                "latitude": float(
                    row["Latitude"]
                ),
                "longitude": float(
                    row["Longitude"]
                ),
                "temperature": float(
                    row["Current_Temperature_C"]
                ),
                "cargo_condition": row[
                    "Cargo_Condition_Code"
                ],
                "risk": row[
                    "Risk_Classification"
                ],
                "delay_probability": float(
                    row["Delay_Probability"]
                ),
                "port_congestion": float(
                    row["Port_Congestion_Level"]
                ),
                "route_risk": float(
                    row["Route_Risk_Index"]
                ),
            }

            vehicles.append(vehicle)

        except (
            KeyError,
            ValueError,
            TypeError,
        ):
            continue

    return vehicles


# ============================================================
# TELEMETRY NODE
# ============================================================

def telemetry_node(state: AgentState):

    session_id = state.get(
        "session_id",
        "UNKNOWN"
    )

    try:

        telemetry = query_telemetry_db.invoke(
            {
                "sql_query": """
                    SELECT TOP 3 *
                    FROM FDE_VIEWS.VW_ACTIVE_FLEET
                """
            }
        )

        vehicles = parse_telemetry(
            telemetry
        )

        if vehicles:

            message = (
                f"Retrieved {len(vehicles)} "
                f"fleet telemetry record(s)."
            )

            status = "SUCCESS"

        else:

            message = (
                "Telemetry query completed, "
                "but no valid records were returned."
            )

            status = "WARNING"

        trace = add_trace(
            state,
            "telemetry",
            "query_telemetry_db",
            status,
            message,
        )

        audit_ok, audit_message = write_audit_log(
            session_id,
            "telemetry",
            "query_telemetry_db",
            message,
        )

        trace = add_trace(
            {
                **state,
                "execution_trace": trace,
            },
            "telemetry",
            "AgentAuditLog",
            "SUCCESS" if audit_ok else "WARNING",
            audit_message,
        )

        return {
            "telemetry": telemetry,
            "execution_trace": trace,
        }

    except Exception as e:

        message = (
            f"Telemetry tool failed: {str(e)}"
        )

        trace = add_trace(
            state,
            "telemetry",
            "query_telemetry_db",
            "ERROR",
            message,
        )

        write_audit_log(
            session_id,
            "telemetry",
            "query_telemetry_db",
            message,
        )

        return {
            "telemetry": "",
            "execution_trace": trace,
        }


# ============================================================
# WEATHER NODE
# ============================================================

def weather_node(state: AgentState):

    session_id = state.get(
        "session_id",
        "UNKNOWN"
    )

    telemetry = state.get(
        "telemetry",
        ""
    )

    vehicles = parse_telemetry(
        telemetry
    )

    if not vehicles:

        message = (
            "Weather data unavailable because "
            "telemetry data was not returned."
        )

        trace = add_trace(
            state,
            "weather",
            "fetch_corridor_conditions",
            "WARNING",
            message,
        )

        write_audit_log(
            session_id,
            "weather",
            "fetch_corridor_conditions",
            message,
        )

        return {
            "weather": message,
            "execution_trace": trace,
        }

    weather_results = []

    successful = 0
    failed = 0

    for index, vehicle in enumerate(
        vehicles,
        start=1
    ):

        weather = fetch_corridor_conditions.invoke(
            {
                "latitude": vehicle[
                    "latitude"
                ],
                "longitude": vehicle[
                    "longitude"
                ],
            }
        )

        weather_results.append(
            f"Vehicle {index}\n"
            f"Latitude: {vehicle['latitude']}\n"
            f"Longitude: {vehicle['longitude']}\n"
            f"{weather}"
        )

        if (
            weather.startswith("Weather API error")
            or weather.startswith("ERROR")
            or weather.startswith("Weather processing error")
        ):
            failed += 1
        else:
            successful += 1

    weather_text = "\n\n".join(
        weather_results
    )

    if failed == 0:

        status = "SUCCESS"

        message = (
            f"Weather conditions retrieved "
            f"for {successful} vehicle(s)."
        )

    else:

        status = "WARNING"

        message = (
            f"Weather conditions retrieved for "
            f"{successful} vehicle(s); "
            f"{failed} request(s) failed."
        )

    trace = add_trace(
        state,
        "weather",
        "fetch_corridor_conditions",
        status,
        message,
    )

    audit_ok, audit_message = write_audit_log(
        session_id,
        "weather",
        "fetch_corridor_conditions",
        message,
    )

    trace = add_trace(
        {
            **state,
            "execution_trace": trace,
        },
        "weather",
        "AgentAuditLog",
        "SUCCESS" if audit_ok else "WARNING",
        audit_message,
    )

    return {
        "weather": weather_text,
        "execution_trace": trace,
    }


# ============================================================
# SOP NODE
# ============================================================

def sop_node(state: AgentState):

    session_id = state.get(
        "session_id",
        "UNKNOWN"
    )

    sop_query = """
    Retrieve the cold-chain compliance procedures relevant to:

    - fresh-perishable temperature limits
    - IoT temperature breaches
    - auxiliary cooling unit restart
    - ETA delay greater than one hour
    - emergency cold-storage diversion
    - port congestion greater than 7.0
    - Inland Empire Overflow Depot diversion
    - High Risk classification
    - delay probability greater than 0.65
    - Tier 2 Logistics Manager escalation
    """

    try:

        sop = search_compliance_sop.invoke(
            {
                "query": sop_query
            }
        )

        if sop.startswith("ERROR") or sop.startswith("SOP search error"):

            status = "WARNING"

            message = (
                "Cold-chain SOP search returned an error."
            )

        else:

            status = "SUCCESS"

            message = (
                "Cold-chain compliance SOP "
                "searched successfully."
            )

        trace = add_trace(
            state,
            "sop",
            "search_compliance_sop",
            status,
            message,
        )

        audit_ok, audit_message = write_audit_log(
            session_id,
            "sop",
            "search_compliance_sop",
            message,
        )

        trace = add_trace(
            {
                **state,
                "execution_trace": trace,
            },
            "sop",
            "AgentAuditLog",
            "SUCCESS" if audit_ok else "WARNING",
            audit_message,
        )

        return {
            "sop": sop,
            "execution_trace": trace,
        }

    except Exception as e:

        message = (
            f"SOP search failed: {str(e)}"
        )

        trace = add_trace(
            state,
            "sop",
            "search_compliance_sop",
            "ERROR",
            message,
        )

        write_audit_log(
            session_id,
            "sop",
            "search_compliance_sop",
            message,
        )

        return {
            "sop": "",
            "execution_trace": trace,
        }


# ============================================================
# DETERMINISTIC ANALYSIS NODE
# ============================================================

def analysis_node(state: AgentState):

    session_id = state.get(
        "session_id",
        "UNKNOWN"
    )

    telemetry = state.get(
        "telemetry",
        ""
    )

    vehicles = parse_telemetry(
        telemetry
    )

    if not vehicles:

        analysis = (
            "No valid telemetry records were available."
        )

        required_actions = (
            "No actions available because "
            "telemetry was not returned."
        )

        trace = add_trace(
            state,
            "analysis",
            "deterministic_risk_engine",
            "WARNING",
            analysis,
        )

        write_audit_log(
            session_id,
            "analysis",
            "deterministic_risk_engine",
            analysis,
        )

        return {
            "analysis": analysis,
            "required_actions": required_actions,
            "execution_trace": trace,
        }

    analysis_lines = []
    action_lines = []

    for index, vehicle in enumerate(
        vehicles,
        start=1
    ):

        temperature = vehicle[
            "temperature"
        ]

        risk = vehicle[
            "risk"
        ]

        delay_probability = vehicle[
            "delay_probability"
        ]

        port_congestion = vehicle[
            "port_congestion"
        ]

        route_risk = vehicle[
            "route_risk"
        ]

        # ----------------------------------------------------
        # TEMPERATURE STATUS
        # ----------------------------------------------------

        if temperature > 4.0:

            temperature_status = (
                "IMMEDIATE COLD-CHAIN BREACH"
            )

        elif 0.0 <= temperature <= 4.0:

            temperature_status = (
                "Within normal fresh-perishables range"
            )

        else:

            temperature_status = (
                "Below the normal fresh-perishables range"
            )

        # ----------------------------------------------------
        # SOP ACTION ENGINE
        # ----------------------------------------------------

        actions = []

        # Rule 1
        if temperature > 4.0:

            actions.append(
                "Contact driver to restart the "
                "auxiliary cooling unit"
            )

        # Rule 2
        if port_congestion > 7.0:

            actions.append(
                "Suspend standard routing and divert "
                "to the Inland Empire Overflow Depot "
                "in San Bernardino for cross-docking"
            )

        # Rule 3
        if (
            risk == "High Risk"
            and delay_probability > 0.65
        ):

            actions.append(
                "Escalate to Tier 2 Logistics Manager"
            )

        if not actions:

            actions.append(
                "No immediate SOP-triggered action"
            )

        # ----------------------------------------------------
        # ANALYSIS
        # ----------------------------------------------------

        analysis_lines.append(
            f"""
Vehicle {index}
Timestamp: {vehicle['timestamp']}
Latitude: {vehicle['latitude']}
Longitude: {vehicle['longitude']}
IoT Temperature: {temperature:.2f} °C
Temperature Status: {temperature_status}
Risk Classification: {risk}
Delay Probability: {delay_probability:.3f}
Port Congestion Level: {port_congestion:.3f}
Route Risk Index: {route_risk:.3f}

Required Actions:
- {"; ".join(actions)}
"""
        )

        action_lines.append(
            f"Vehicle {index}:"
        )

        for action in actions:

            action_lines.append(
                f"- {action}"
            )

    analysis = "\n".join(
        analysis_lines
    )

    required_actions = "\n".join(
        action_lines
    )

    message = (
        "Deterministic cold-chain risk "
        "analysis completed."
    )

    trace = add_trace(
        state,
        "analysis",
        "deterministic_risk_engine",
        "SUCCESS",
        message,
    )

    audit_ok, audit_message = write_audit_log(
        session_id,
        "analysis",
        "deterministic_risk_engine",
        message,
    )

    trace = add_trace(
        {
            **state,
            "execution_trace": trace,
        },
        "analysis",
        "AgentAuditLog",
        "SUCCESS" if audit_ok else "WARNING",
        audit_message,
    )

    return {
        "analysis": analysis,
        "required_actions": required_actions,
        "execution_trace": trace,
    }


# ============================================================
# FINAL REPORT BUILDER
# ============================================================

def build_deterministic_report(
    state: AgentState
):

    analysis = state.get(
        "analysis",
        "No fleet analysis available."
    )

    weather = state.get(
        "weather",
        "Weather data unavailable."
    )

    required_actions = state.get(
        "required_actions",
        "No required actions available."
    )

    sop = state.get(
        "sop",
        "No SOP information was retrieved."
    )

    vehicles = parse_telemetry(
        state.get(
            "telemetry",
            ""
        )
    )

    # ========================================================
    # OPERATIONAL ASSESSMENT
    # ========================================================

    high_risk_count = 0
    temperature_breach_count = 0
    action_vehicle_count = 0

    for vehicle in vehicles:

        if vehicle["risk"] == "High Risk":

            high_risk_count += 1

        if vehicle["temperature"] > 4.0:

            temperature_breach_count += 1

        if (
            vehicle["port_congestion"] > 7.0
            or (
                vehicle["risk"] == "High Risk"
                and vehicle["delay_probability"] > 0.65
            )
            or vehicle["temperature"] > 4.0
        ):

            action_vehicle_count += 1

    assessment_parts = []

    if high_risk_count > 0:

        assessment_parts.append(
            f"{high_risk_count} vehicle(s) "
            "are classified as High Risk."
        )

    if temperature_breach_count > 0:

        assessment_parts.append(
            f"{temperature_breach_count} vehicle(s) "
            "exceed the 4.0°C immediate breach threshold."
        )

    if action_vehicle_count > 0:

        assessment_parts.append(
            f"{action_vehicle_count} vehicle(s) have "
            "deterministic SOP-triggered actions."
        )

    if not assessment_parts:

        assessment_parts.append(
            "No immediate SOP-triggered fleet "
            "actions were identified."
        )

    operational_assessment = " ".join(
        assessment_parts
    )

    # ========================================================
    # FLEET SUMMARY
    # ========================================================

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
                "Within normal fresh-perishables range"
            )

        else:

            temperature_status = (
                "Below the normal fresh-perishables range"
            )

        fleet_rows.append(
            {
                "Vehicle": f"Vehicle {index}",
                "Risk": vehicle["risk"],
                "IoT Temp (°C)": round(
                    temperature,
                    2
                ),
                "Temperature Status": temperature_status,
                "Delay Probability": round(
                    vehicle["delay_probability"],
                    3
                ),
                "Port Congestion": round(
                    vehicle["port_congestion"],
                    3
                ),
                "Route Risk": round(
                    vehicle["route_risk"],
                    3
                ),
            }
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    final_report = f"""### Operational Assessment

{operational_assessment}

### Fleet Risk Summary

{analysis}

### Weather Conditions

{weather}

### Required Actions

{required_actions}

### SOP Compliance

{sop}
"""

    return final_report, fleet_rows


# ============================================================
# REASONER / FINAL REPORT NODE
# ============================================================

def reasoner_node(state: AgentState):

    session_id = state.get(
        "session_id",
        "UNKNOWN"
    )

    final_report, fleet_rows = (
        build_deterministic_report(
            state
        )
    )

    message = (
        "Operational report generated."
    )

    trace = add_trace(
        state,
        "reasoner",
        "operational_report_generator",
        "SUCCESS",
        message,
    )

    audit_ok, audit_message = write_audit_log(
        session_id,
        "reasoner",
        "operational_report_generator",
        message,
    )

    trace = add_trace(
        {
            **state,
            "execution_trace": trace,
        },
        "reasoner",
        "AgentAuditLog",
        "SUCCESS" if audit_ok else "WARNING",
        audit_message,
    )

    return {
        "final_response": final_report,
        "execution_trace": trace,
    }


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph(llm=None):

    graph_builder = StateGraph(
        AgentState
    )

    graph_builder.add_node(
        "telemetry",
        telemetry_node
    )

    graph_builder.add_node(
        "weather",
        weather_node
    )

    graph_builder.add_node(
        "sop",
        sop_node
    )

    graph_builder.add_node(
        "analysis",
        analysis_node
    )

    graph_builder.add_node(
        "reasoner",
        reasoner_node
    )

    # --------------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------------

    graph_builder.add_edge(
        START,
        "telemetry"
    )

    graph_builder.add_edge(
        "telemetry",
        "weather"
    )

    graph_builder.add_edge(
        "weather",
        "sop"
    )

    graph_builder.add_edge(
        "sop",
        "analysis"
    )

    graph_builder.add_edge(
        "analysis",
        "reasoner"
    )

    graph_builder.add_edge(
        "reasoner",
        END
    )

    return graph_builder.compile()