from typing import TypedDict

import os
import pyodbc
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.agent_tools import (
    fetch_corridor_conditions,
    query_telemetry_db,
    search_compliance_sop,
)
from src.intent_parser import parse_intent


load_dotenv()


# =====================================================
# AGENT STATE
# =====================================================

class AgentState(TypedDict, total=False):
    user_request: str
    session_id: str

    intent: str

    telemetry: str
    weather: str
    sop: str

    analysis: str
    actions: list

    final_response: str

    telemetry_status: str
    weather_status: str
    sop_status: str
    analysis_status: str
    reasoner_status: str

    audit_history: list


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('FDE_DB_SERVER')};"
        f"DATABASE={os.getenv('FDE_DB_NAME')};"
        f"UID={os.getenv('FDE_DB_USER')};"
        f"PWD={os.getenv('FDE_DB_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


# =====================================================
# AUDIT LOG WRITER
# =====================================================

def write_audit_log(
    session_id: str,
    node_executed: str,
    tool_name: str,
    content: str,
):
    """
    Write an execution entry into the audit table.
    """

    try:
        conn = get_connection()
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

    except Exception as e:
        print(f"Audit logging error: {e}")


# =====================================================
# AUDIT HISTORY READER
# =====================================================

def get_audit_history(
    session_id: str,
    limit: int = 100,
):
    """
    Read audit records for the current session.

    This function only reads from the audit table.
    It does not access the raw fleet telemetry table.
    """

    try:
        limit = max(
            1,
            min(int(limit), 100),
        )

        conn = get_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT TOP {limit}
                *
            FROM FDE_VIEWS.AgentAuditLog
            WHERE SessionID = ?
        """

        cursor.execute(
            query,
            session_id,
        )

        columns = [
            column[0]
            for column in cursor.description
        ]

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        history = []

        for row in rows:

            history.append(
                {
                    column: value
                    for column, value in zip(
                        columns,
                        row,
                    )
                }
            )

        return history

    except Exception as e:
        print(f"Audit history error: {e}")
        return []


# =====================================================
# TELEMETRY PARSER
# =====================================================

def parse_telemetry(result: str):
    """
    Convert the text returned by the telemetry tool
    into structured Python dictionaries.
    """

    lines = result.splitlines()

    if len(lines) < 2:
        return []

    headers = [
        header.strip()
        for header in lines[0].split(",")
    ]

    records = []

    for line in lines[1:]:

        values = [
            value.strip()
            for value in line.split(",")
        ]

        if len(values) != len(headers):
            continue

        record = dict(
            zip(
                headers,
                values,
            )
        )

        numeric_fields = [
            "Latitude",
            "Longitude",
            "Current_Temperature_C",
            "Delay_Probability",
            "Port_Congestion_Level",
            "Route_Risk_Index",
        ]

        for field in numeric_fields:

            if field in record:

                try:
                    record[field] = float(
                        record[field]
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    pass

        records.append(record)

    return records


# =====================================================
# TELEMETRY QUERY BUILDER
# =====================================================

def build_telemetry_query(
    intent: str,
) -> str:
    """
    Build a safe SQL Server query based on the
    controlled intent returned by the intent parser.

    Safety-critical thresholds remain hard-coded here.
    """

    base = """
        SELECT TOP 10
            [Timestamp],
            [Latitude],
            [Longitude],
            [Current_Temperature_C],
            [Cargo_Condition_Code],
            [Risk_Classification],
            [Delay_Probability],
            [Port_Congestion_Level],
            [Route_Risk_Index]
        FROM FDE_VIEWS.VW_ACTIVE_FLEET
    """

    if intent == "temperature_breach":

        return base + """
        WHERE [Current_Temperature_C] > 4.0
        """

    if intent == "port_congestion":

        return base + """
        WHERE [Port_Congestion_Level] > 7.0
        """

    if intent == "high_risk":

        return base + """
        WHERE [Risk_Classification] = 'High Risk'
        """

    if intent == "delay_risk":

        return base + """
        WHERE [Delay_Probability] > 0.65
        """

    if intent == "route_risk":

        return base + """
        WHERE [Route_Risk_Index] > 7.0
        """

    return base


# =====================================================
# TELEMETRY NODE
# =====================================================

def telemetry_node(
    state: AgentState,
):

    user_request = state.get(
        "user_request",
        "",
    )

    intent = parse_intent(
        user_request
    )

    query = build_telemetry_query(
        intent
    )

    result = query_telemetry_db.invoke(
        {
            "sql_query": query
        }
    )

    write_audit_log(
        session_id=state["session_id"],
        node_executed="telemetry",
        tool_name="query_telemetry_db",
        content=(
            f"User request: {user_request}\n"
            f"Intent: {intent}\n"
            f"Query:\n{query}\n"
            f"Result:\n{result}"
        ),
    )

    return {
        "intent": intent,
        "telemetry": result,
        "telemetry_status": "success",
    }


# =====================================================
# WEATHER NODE
# =====================================================

def weather_node(
    state: AgentState,
):

    telemetry_text = state.get(
        "telemetry",
        "",
    )

    vehicles = parse_telemetry(
        telemetry_text
    )

    if not vehicles:

        result = (
            "No vehicle locations available "
            "for weather analysis."
        )

        write_audit_log(
            session_id=state["session_id"],
            node_executed="weather",
            tool_name="fetch_corridor_conditions",
            content=result,
        )

        return {
            "weather": result,
            "weather_status": "no_data",
        }

    weather_results = []

    for index, vehicle in enumerate(
        vehicles,
        start=1,
    ):

        latitude = vehicle.get(
            "Latitude"
        )

        longitude = vehicle.get(
            "Longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            continue

        weather = (
            fetch_corridor_conditions.invoke(
                {
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
        )

        weather_results.append(
            f"Vehicle {index} "
            f"({latitude}, {longitude})\n"
            f"{weather}"
        )

    if not weather_results:

        result = (
            "Weather data could not be retrieved "
            "for the available vehicles."
        )

    else:

        result = "\n\n".join(
            weather_results
        )

    write_audit_log(
        session_id=state["session_id"],
        node_executed="weather",
        tool_name="fetch_corridor_conditions",
        content=result,
    )

    return {
        "weather": result,
        "weather_status": "success",
    }


# =====================================================
# SOP NODE
# =====================================================

def sop_node(
    state: AgentState,
):

    intent = state.get(
        "intent",
        "general",
    )

    sop_query = (
        "Cold-chain incident response procedures, "
        "temperature breaches, port congestion, "
        "delay risk, route risk, high risk vehicles, "
        "escalation and required dispatcher actions."
    )

    result = search_compliance_sop.invoke(
        {
            "query": sop_query
        }
    )

    write_audit_log(
        session_id=state["session_id"],
        node_executed="sop",
        tool_name="search_compliance_sop",
        content=(
            f"Intent: {intent}\n"
            f"SOP Query: {sop_query}\n"
            f"Result:\n{result}"
        ),
    )

    return {
        "sop": result,
        "sop_status": "success",
    }


# =====================================================
# WEATHER PARSER
# =====================================================

def parse_weather(
    weather_text: str,
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

        temperature = None
        wind_speed = None
        disruption_index = None

        for line in lines:

            if line.startswith(
                "Current temperature:"
            ):

                try:

                    temperature = float(
                        line.split(
                            ":",
                            1,
                        )[1]
                        .replace(
                            "°C",
                            "",
                        )
                        .strip()
                    )

                except ValueError:
                    pass

            elif line.startswith(
                "Wind speed:"
            ):

                try:

                    wind_speed = float(
                        line.split(
                            ":",
                            1,
                        )[1]
                        .replace(
                            "km/h",
                            "",
                        )
                        .strip()
                    )

                except ValueError:
                    pass

            elif line.startswith(
                "Disruption index:"
            ):

                try:

                    disruption_index = float(
                        line.split(
                            ":",
                            1,
                        )[1].strip()
                    )

                except ValueError:
                    pass

        results.append(
            {
                "Vehicle": vehicle,
                "Weather_Temperature_C": temperature,
                "Wind_Speed_kmh": wind_speed,
                "Disruption_Index": disruption_index,
            }
        )

    return results


# =====================================================
# DETERMINISTIC RISK ENGINE
# =====================================================

def analysis_node(
    state: AgentState,
):

    telemetry_text = state.get(
        "telemetry",
        "",
    )

    vehicles = parse_telemetry(
        telemetry_text
    )

    findings = []
    actions = []

    for index, vehicle in enumerate(
        vehicles,
        start=1,
    ):

        temperature = vehicle.get(
            "Current_Temperature_C"
        )

        port_congestion = vehicle.get(
            "Port_Congestion_Level"
        )

        risk_classification = vehicle.get(
            "Risk_Classification"
        )

        delay_probability = vehicle.get(
            "Delay_Probability"
        )

        route_risk = vehicle.get(
            "Route_Risk_Index"
        )

        vehicle_actions = []

        # -------------------------------------------------
        # Cold-chain temperature rule
        # -------------------------------------------------

        if (
            isinstance(
                temperature,
                (int, float),
            )
            and temperature > 4.0
        ):

            vehicle_actions.append(
                "Immediate cold-chain breach: "
                "contact driver to restart the auxiliary cooling unit."
            )

        # -------------------------------------------------
        # Port congestion rule
        # -------------------------------------------------

        if (
            isinstance(
                port_congestion,
                (int, float),
            )
            and port_congestion > 7.0
        ):

            vehicle_actions.append(
                "Suspend standard routing and divert to "
                "the Inland Empire Overflow Depot in "
                "San Bernardino for cross-docking."
            )

        # -------------------------------------------------
        # High-risk + delay probability rule
        # -------------------------------------------------

        if (
            risk_classification == "High Risk"
            and isinstance(
                delay_probability,
                (int, float),
            )
            and delay_probability > 0.65
        ):

            vehicle_actions.append(
                "Escalate to a Tier 2 Logistics Manager."
            )

        finding = {
            "Vehicle": index,
            "Temperature": temperature,
            "Risk": risk_classification,
            "Delay_Probability": delay_probability,
            "Port_Congestion": port_congestion,
            "Route_Risk": route_risk,
            "Actions": vehicle_actions,
        }

        findings.append(
            finding
        )

        for action in vehicle_actions:

            actions.append(
                {
                    "Vehicle": index,
                    "Action": action,
                }
            )

    analysis_text = []

    if not findings:

        analysis_text.append(
            "No telemetry records were available for analysis."
        )

    else:

        for finding in findings:

            analysis_text.append(
                f"Vehicle {finding['Vehicle']}: "
                f"temperature={finding['Temperature']}°C, "
                f"risk={finding['Risk']}, "
                f"delay_probability="
                f"{finding['Delay_Probability']}, "
                f"port_congestion="
                f"{finding['Port_Congestion']}, "
                f"route_risk="
                f"{finding['Route_Risk']}."
            )

            if finding["Actions"]:

                for action in finding[
                    "Actions"
                ]:

                    analysis_text.append(
                        f"Action: {action}"
                    )

            else:

                analysis_text.append(
                    "Action: No immediate deterministic "
                    "SOP action triggered."
                )

    result = "\n".join(
        analysis_text
    )

    write_audit_log(
        session_id=state["session_id"],
        node_executed="analysis",
        tool_name="deterministic_risk_engine",
        content=result,
    )

    return {
        "analysis": result,
        "actions": actions,
        "analysis_status": "success",
    }


# =====================================================
# OPERATIONAL REPORT
# =====================================================

def build_deterministic_report(
    state: AgentState,
):

    telemetry_text = state.get(
        "telemetry",
        "",
    )

    weather_text = state.get(
        "weather",
        "",
    )

    sop_text = state.get(
        "sop",
        "",
    )

    analysis_text = state.get(
        "analysis",
        "",
    )

    vehicles = parse_telemetry(
        telemetry_text
    )

    weather_records = parse_weather(
        weather_text
    )

    report = []

    # =================================================
    # 1. EXECUTIVE SUMMARY
    # =================================================

    report.append(
        "### 1. Executive Summary"
    )

    if not vehicles:

        report.append(
            "* No telemetry records were available."
        )

    else:

        risk_count = 0

        for vehicle in vehicles:

            risk = vehicle.get(
                "Risk_Classification"
            )

            temperature = vehicle.get(
                "Current_Temperature_C"
            )

            port_congestion = vehicle.get(
                "Port_Congestion_Level"
            )

            delay_probability = vehicle.get(
                "Delay_Probability"
            )

            if (
                risk == "High Risk"
                or (
                    isinstance(
                        temperature,
                        (int, float),
                    )
                    and temperature > 4.0
                )
                or (
                    isinstance(
                        port_congestion,
                        (int, float),
                    )
                    and port_congestion > 7.0
                )
                or (
                    isinstance(
                        delay_probability,
                        (int, float),
                    )
                    and delay_probability > 0.65
                )
            ):

                risk_count += 1

        report.append(
            f"* {risk_count} of "
            f"{len(vehicles)} retrieved vehicle "
            f"records require risk review or "
            f"operational attention."
        )

        if risk_count == 0:

            report.append(
                "* No immediate deterministic SOP action "
                "was triggered by the retrieved telemetry."
            )

        else:

            report.append(
                "* Operational actions are listed below "
                "for the affected vehicles."
            )

    # =================================================
    # 2. TELEMETRY & ENVIRONMENT ANALYSIS
    # =================================================

    report.append("")

    report.append(
        "### 2. Telemetry & Environment Analysis"
    )

    report.append(
        "| Location (Lat/Lon) | Current Temp | Cargo Risk | "
        "Weather / Congestion |"
    )

    report.append(
        "|---|---:|---|---|"
    )

    for index, vehicle in enumerate(
        vehicles
    ):

        latitude = vehicle.get(
            "Latitude"
        )

        longitude = vehicle.get(
            "Longitude"
        )

        temperature = vehicle.get(
            "Current_Temperature_C"
        )

        risk = vehicle.get(
            "Risk_Classification"
        )

        congestion = vehicle.get(
            "Port_Congestion_Level"
        )

        weather_info = "Weather unavailable"

        if index < len(
            weather_records
        ):

            weather = weather_records[
                index
            ]

            weather_temp = weather.get(
                "Weather_Temperature_C"
            )

            wind = weather.get(
                "Wind_Speed_kmh"
            )

            disruption = weather.get(
                "Disruption_Index"
            )

            weather_info = (
                f"Weather {weather_temp}°C, "
                f"wind {wind} km/h, "
                f"disruption {disruption}; "
                f"port congestion {congestion}"
            )

        report.append(
            f"| ({latitude}, {longitude}) | "
            f"{temperature}°C | "
            f"{risk} | "
            f"{weather_info} |"
        )

    report.append("")

    report.append(
        "*Analysis:*"
    )

    report.append(
        analysis_text
    )

    # =================================================
    # 3. REQUIRED ACTION PLAN
    # =================================================

    report.append("")

    report.append(
        "### 3. Required Action Plan"
    )

    actions = state.get(
        "actions",
        [],
    )

    if not actions:

        report.append(
            "1. **No immediate action:** "
            "No deterministic SOP action was triggered."
        )

    else:

        for number, action in enumerate(
            actions,
            start=1,
        ):

            report.append(
                f"{number}. **Vehicle "
                f"{action['Vehicle']}:** "
                f"{action['Action']}"
            )

    # =================================================
    # 4. SOP
    # =================================================

    report.append("")

    report.append(
        "*SOP Compliance Citation:*"
    )

    report.append(
        "The operational actions above are based on "
        "the retrieved Cold-Chain Incident SOP."
    )

    if sop_text:

        report.append("")

        report.append(
            "Relevant SOP information retrieved:"
        )

        report.append(
            sop_text
        )

    return "\n".join(
        report
    )


# =====================================================
# REASONER / REPORT NODE
# =====================================================

def reasoner_node(
    state: AgentState,
):

    report = build_deterministic_report(
        state
    )

    actions = state.get(
        "actions",
        [],
    )

    # -------------------------------------------------
    # Record complete analysis run
    # -------------------------------------------------

    run_summary = (
        f"User request: "
        f"{state.get('user_request', '')}\n"
        f"Intent: "
        f"{state.get('intent', 'general')}\n"
        f"Actions generated: "
        f"{len(actions)}\n"
        f"Telemetry status: "
        f"{state.get('telemetry_status', '')}\n"
        f"Weather status: "
        f"{state.get('weather_status', '')}\n"
        f"SOP status: "
        f"{state.get('sop_status', '')}\n"
        f"Analysis status: "
        f"{state.get('analysis_status', '')}\n"
        f"Reasoner status: success"
    )

    write_audit_log(
        session_id=state["session_id"],
        node_executed="analysis_run",
        tool_name="operational_audit",
        content=run_summary,
    )

    # -------------------------------------------------
    # Record generated report
    # -------------------------------------------------

    write_audit_log(
        session_id=state["session_id"],
        node_executed="reasoner",
        tool_name="operational_report_generator",
        content=report,
    )

    # -------------------------------------------------
    # Read audit history for current session
    # -------------------------------------------------

    audit_history = get_audit_history(
        session_id=state["session_id"],
        limit=100,
    )

    return {
        "final_response": report,
        "reasoner_status": "success",
        "audit_history": audit_history,
    }


# =====================================================
# GRAPH
# =====================================================

def build_graph():

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "telemetry",
        telemetry_node,
    )

    graph.add_node(
        "weather",
        weather_node,
    )

    graph.add_node(
        "sop",
        sop_node,
    )

    graph.add_node(
        "analysis",
        analysis_node,
    )

    graph.add_node(
        "reasoner",
        reasoner_node,
    )

    graph.add_edge(
        START,
        "telemetry",
    )

    graph.add_edge(
        "telemetry",
        "weather",
    )

    graph.add_edge(
        "weather",
        "sop",
    )

    graph.add_edge(
        "sop",
        "analysis",
    )

    graph.add_edge(
        "analysis",
        "reasoner",
    )

    graph.add_edge(
        "reasoner",
        END,
    )

    return graph.compile()


# =====================================================
# PUBLIC RUN FUNCTION
# =====================================================

def run_agent(
    user_request: str,
    session_id: str,
):

    graph = build_graph()

    initial_state: AgentState = {
        "user_request": user_request,
        "session_id": session_id,
        "intent": "",
        "telemetry": "",
        "weather": "",
        "sop": "",
        "analysis": "",
        "actions": [],
        "final_response": "",
        "telemetry_status": "",
        "weather_status": "",
        "sop_status": "",
        "analysis_status": "",
        "reasoner_status": "",
        "audit_history": [],
    }

    result = graph.invoke(
        initial_state
    )

    return result