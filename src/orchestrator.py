from pathlib import Path
from typing import Optional
from typing_extensions import TypedDict
from uuid import uuid4

import pyodbc

from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END

from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
    search_compliance_sop,
    CONNECTION_STRING,
)


# =========================================================
# STATE
# =========================================================

class AgentState(TypedDict, total=False):
    user_request: str
    session_id: str

    telemetry: str
    weather: str
    sop: str

    analysis: str
    required_actions: str

    final_response: str

    telemetry_status: str
    weather_status: str
    sop_status: str
    analysis_status: str
    report_status: str


# =========================================================
# SYSTEM PROMPT
# =========================================================

def load_system_prompt():

    prompt_path = (
        Path(__file__).parent
        / "prompts"
        / "system_prompt.txt"
    )

    if not prompt_path.exists():
        return ""

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


# =========================================================
# AUDIT LOGGING
# =========================================================

def write_audit_log(
    session_id: str,
    node_executed: str,
    tool_name: str,
    content: str,
):

    try:

        conn = pyodbc.connect(CONNECTION_STRING)

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
            content,
        )

        conn.commit()

        cursor.close()
        conn.close()

    except Exception:
        # Audit failure should not stop the operational workflow.
        pass


# =========================================================
# TELEMETRY PARSER
# =========================================================

def parse_telemetry(telemetry_text):

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

        line = line.strip()

        if not line:
            continue

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
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
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


# =========================================================
# QUERY BUILDER
# =========================================================

def build_telemetry_query(
    user_request: str
):

    request = (
        user_request
        .lower()
        .strip()
    )

    # -----------------------------------------------------
    # HIGH RISK
    # -----------------------------------------------------

    if (
        "high risk" in request
        or "high-risk" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
            WHERE Risk_Classification = 'High Risk'
        """

    # -----------------------------------------------------
    # TEMPERATURE BREACH
    # -----------------------------------------------------

    if (
        "temperature breach" in request
        or "temperature breaches" in request
        or "cold-chain breach" in request
        or "cold chain breach" in request
        or "temperature above 4" in request
        or "temperature over 4" in request
        or "above 4" in request
        or "over 4" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
            WHERE Current_Temperature_C > 4.0
        """

    # -----------------------------------------------------
    # DELAY
    # -----------------------------------------------------

    if (
        "delayed vehicles" in request
        or "delayed vehicle" in request
        or "delay probability" in request
        or "high delay" in request
        or "delay risk" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
            WHERE Delay_Probability > 0.65
        """

    # -----------------------------------------------------
    # PORT CONGESTION
    # -----------------------------------------------------

    if (
        "port congestion" in request
        or "port congested" in request
        or "congested port" in request
        or "port risk" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
            WHERE Port_Congestion_Level > 7.0
        """

    # -----------------------------------------------------
    # ROUTE RISK
    # -----------------------------------------------------

    if (
        "route risk" in request
        or "risky route" in request
        or "high route risk" in request
        or "route risk vehicles" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
            WHERE Route_Risk_Index > 7.0
        """

    # -----------------------------------------------------
    # ACTION / INCIDENT QUERY
    #
    # We retrieve the fleet and let the deterministic
    # analysis engine identify the required actions.
    # -----------------------------------------------------

    if (
        "immediate action" in request
        or "immediate actions" in request
        or "required action" in request
        or "required actions" in request
        or "what should i do" in request
        or "what should we do" in request
        or "incident" in request
        or "breach" in request
        or "risk" in request
    ):

        return """
            SELECT TOP 10 *
            FROM FDE_VIEWS.VW_ACTIVE_FLEET
        """

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return """
        SELECT TOP 10 *
        FROM FDE_VIEWS.VW_ACTIVE_FLEET
    """


# =========================================================
# TELEMETRY NODE
# =========================================================

def telemetry_node(
    state: AgentState
):

    user_request = state.get(
        "user_request",
        "Analyze the current fleet."
    )

    session_id = state.get(
        "session_id",
        str(uuid4())[:8]
    )

    sql_query = build_telemetry_query(
        user_request
    )

    telemetry = query_telemetry_db.invoke(
        {
            "sql_query": sql_query
        }
    )

    vehicles = parse_telemetry(
        telemetry
    )

    if vehicles:

        status = (
            f"Retrieved {len(vehicles)} "
            f"fleet telemetry record(s)."
        )

    else:

        status = (
            "No matching fleet telemetry "
            "records were found."
        )

    write_audit_log(
        session_id=session_id,
        node_executed="telemetry",
        tool_name="query_telemetry_db",
        content=status,
    )

    return {
        "telemetry": telemetry,
        "telemetry_status": status,
    }


# =========================================================
# WEATHER NODE
# =========================================================

def weather_node(
    state: AgentState
):

    telemetry = state.get(
        "telemetry",
        ""
    )

    session_id = state.get(
        "session_id",
        str(uuid4())[:8]
    )

    vehicles = parse_telemetry(
        telemetry
    )

    if not vehicles:

        weather = (
            "Weather data unavailable because "
            "no matching telemetry records were returned."
        )

        write_audit_log(
            session_id=session_id,
            node_executed="weather",
            tool_name="fetch_corridor_conditions",
            content=weather,
        )

        return {
            "weather": weather,
            "weather_status": "Weather data unavailable.",
        }

    weather_results = []

    for index, vehicle in enumerate(
        vehicles,
        start=1
    ):

        weather = (
            fetch_corridor_conditions.invoke(
                {
                    "latitude": vehicle["latitude"],
                    "longitude": vehicle["longitude"],
                }
            )
        )

        weather_results.append(
            f"Vehicle {index}\n"
            f"Latitude: {vehicle['latitude']}\n"
            f"Longitude: {vehicle['longitude']}\n"
            f"{weather}"
        )

    final_weather = (
        "\n\n".join(weather_results)
    )

    status = (
        f"Weather conditions retrieved for "
        f"{len(vehicles)} vehicle(s)."
    )

    write_audit_log(
        session_id=session_id,
        node_executed="weather",
        tool_name="fetch_corridor_conditions",
        content=status,
    )

    return {
        "weather": final_weather,
        "weather_status": status,
    }


# =========================================================
# SOP NODE
# =========================================================

def sop_node(
    state: AgentState
):

    session_id = state.get(
        "session_id",
        str(uuid4())[:8]
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

    sop = search_compliance_sop.invoke(
        {
            "query": sop_query
        }
    )

    if sop.startswith("ERROR"):

        status = "Cold-chain compliance SOP search failed."

    else:

        status = (
            "Cold-chain compliance SOP "
            "searched successfully."
        )

    write_audit_log(
        session_id=session_id,
        node_executed="sop",
        tool_name="search_compliance_sop",
        content=status,
    )

    return {
        "sop": sop,
        "sop_status": status,
    }


# =========================================================
# DETERMINISTIC ANALYSIS ENGINE
# =========================================================

def analysis_node(
    state: AgentState
):

    telemetry = state.get(
        "telemetry",
        ""
    )

    session_id = state.get(
        "session_id",
        str(uuid4())[:8]
    )

    vehicles = parse_telemetry(
        telemetry
    )

    if not vehicles:

        analysis = (
            "No valid telemetry records "
            "were available for analysis."
        )

        actions = (
            "No actions available because "
            "no telemetry records were returned."
        )

        write_audit_log(
            session_id=session_id,
            node_executed="analysis",
            tool_name="deterministic_risk_engine",
            content=(
                "Deterministic analysis completed "
                "with no telemetry records."
            ),
        )

        return {
            "analysis": analysis,
            "required_actions": actions,
            "analysis_status": (
                "No telemetry records available."
            ),
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

        # -------------------------------------------------
        # TEMPERATURE STATUS
        # -------------------------------------------------

        if temperature > 4.0:

            temperature_status = (
                "IMMEDIATE COLD-CHAIN BREACH"
            )

        elif 0.0 <= temperature <= 4.0:

            temperature_status = (
                "Within normal "
                "fresh-perishables range"
            )

        else:

            temperature_status = (
                "Below the normal "
                "fresh-perishables range"
            )

        # -------------------------------------------------
        # SOP ACTION ENGINE
        # -------------------------------------------------

        actions = []

        # Rule 1:
        # IoT temperature above 4.0°C
        if temperature > 4.0:

            actions.append(
                "Contact driver to restart "
                "the auxiliary cooling unit"
            )

        # Rule 2:
        # Port congestion above 7.0
        if port_congestion > 7.0:

            actions.append(
                "Suspend standard routing and "
                "divert to the Inland Empire "
                "Overflow Depot in San Bernardino "
                "for cross-docking"
            )

        # Rule 3:
        # High Risk AND delay probability > 0.65
        if (
            risk == "High Risk"
            and delay_probability > 0.65
        ):

            actions.append(
                "Escalate to Tier 2 "
                "Logistics Manager"
            )

        if not actions:

            actions.append(
                "No immediate SOP-triggered action"
            )

        # -------------------------------------------------
        # ANALYSIS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # ACTIONS
        # -------------------------------------------------

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

    status = (
        "Deterministic cold-chain risk "
        "analysis completed."
    )

    write_audit_log(
        session_id=session_id,
        node_executed="analysis",
        tool_name="deterministic_risk_engine",
        content=status,
    )

    return {
        "analysis": analysis,
        "required_actions": required_actions,
        "analysis_status": status,
    }


# =========================================================
# WEATHER PARSER FOR UI
# =========================================================

def parse_weather(
    weather_text
):

    if not weather_text:
        return []

    blocks = weather_text.split(
        "\n\n"
    )

    results = []

    for block in blocks:

        lines = block.splitlines()

        if not lines:
            continue

        vehicle = lines[0]

        data = {
            "vehicle": vehicle,
            "latitude": "-",
            "longitude": "-",
            "temperature": "-",
            "wind": "-",
            "disruption": "-",
        }

        for line in lines[1:]:

            line = line.strip()

            if line.startswith(
                "Latitude:"
            ):

                data["latitude"] = (
                    line.split(
                        ":", 1
                    )[1].strip()
                )

            elif line.startswith(
                "Longitude:"
            ):

                data["longitude"] = (
                    line.split(
                        ":", 1
                    )[1].strip()
                )

            elif line.startswith(
                "Current temperature:"
            ):

                data["temperature"] = (
                    line.split(
                        ":", 1
                    )[1].strip()
                )

            elif line.startswith(
                "Wind speed:"
            ):

                data["wind"] = (
                    line.split(
                        ":", 1
                    )[1].strip()
                )

            elif line.startswith(
                "Disruption index:"
            ):

                data["disruption"] = (
                    line.split(
                        ":", 1
                    )[1].strip()
                )

        results.append(data)

    return results


# =========================================================
# BUILD FINAL REPORT
# =========================================================

def build_deterministic_report(
    state: AgentState
):

    telemetry = state.get(
        "telemetry",
        ""
    )

    weather = state.get(
        "weather",
        "Weather data unavailable."
    )

    sop = state.get(
        "sop",
        "No SOP information was retrieved."
    )

    required_actions = state.get(
        "required_actions",
        "No required actions available."
    )

    vehicles = parse_telemetry(
        telemetry
    )

    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    high_risk_count = 0

    temperature_breach_count = 0

    action_vehicle_count = 0

    for vehicle in vehicles:

        if vehicle["risk"] == "High Risk":

            high_risk_count += 1

        if vehicle["temperature"] > 4.0:

            temperature_breach_count += 1

        if (
            vehicle["temperature"] > 4.0
            or vehicle["port_congestion"] > 7.0
            or (
                vehicle["risk"] == "High Risk"
                and vehicle["delay_probability"] > 0.65
            )
        ):

            action_vehicle_count += 1

    # -----------------------------------------------------
    # OPERATIONAL ASSESSMENT
    # -----------------------------------------------------

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
            f"{action_vehicle_count} vehicle(s) "
            "have deterministic SOP-triggered actions."
        )

    if not assessment_parts:

        assessment_parts.append(
            "No immediate SOP-triggered "
            "fleet actions were identified."
        )

    operational_assessment = (
        " ".join(assessment_parts)
    )

    # -----------------------------------------------------
    # FLEET SUMMARY
    # -----------------------------------------------------

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
                "Within normal "
                "fresh-perishables range"
            )

        else:

            temperature_status = (
                "Below the normal "
                "fresh-perishables range"
            )

        fleet_rows.append(
            {
                "Vehicle": f"Vehicle {index}",
                "Risk": vehicle["risk"],
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

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    final_report = f"""
### Operational Assessment

{operational_assessment}

### Fleet Risk Summary

{fleet_rows}

### Weather Conditions

{weather}

### Required Actions

{required_actions}

### SOP Compliance

{sop}
"""

    return final_report


# =========================================================
# REASONER / REPORT NODE
# =========================================================

def reasoner_node(
    state: AgentState
):

    session_id = state.get(
        "session_id",
        str(uuid4())[:8]
    )

    final_response = (
        build_deterministic_report(
            state
        )
    )

    status = (
        "Operational report generated."
    )

    write_audit_log(
        session_id=session_id,
        node_executed="reasoner",
        tool_name="operational_report_generator",
        content=status,
    )

    return {
        "final_response": final_response,
        "report_status": status,
    }


# =========================================================
# GRAPH
# =========================================================

def build_graph(
    llm: Optional[object] = None
):

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

    # -----------------------------------------------------
    # WORKFLOW
    # -----------------------------------------------------

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