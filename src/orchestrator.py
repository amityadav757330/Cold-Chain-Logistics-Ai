from pathlib import Path
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
    search_compliance_sop,
)
from src.llm import get_llm


class AgentState(TypedDict, total=False):
    user_request: str
    telemetry: str
    weather: str
    sop: str
    analysis: str
    required_actions: str
    final_response: str


def load_system_prompt():
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


def parse_telemetry(telemetry_text):
    lines = telemetry_text.splitlines()

    if len(lines) < 2:
        return []

    headers = [item.strip() for item in lines[0].split(",")]

    vehicles = []

    for line in lines[1:]:
        values = [item.strip() for item in line.split(",")]

        if len(values) != len(headers):
            continue

        row = dict(zip(headers, values))

        try:
            vehicle = {
                "timestamp": row["Timestamp"],
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
                "temperature": float(row["Current_Temperature_C"]),
                "cargo_condition": row["Cargo_Condition_Code"],
                "risk": row["Risk_Classification"],
                "delay_probability": float(row["Delay_Probability"]),
                "port_congestion": float(row["Port_Congestion_Level"]),
                "route_risk": float(row["Route_Risk_Index"]),
            }

            vehicles.append(vehicle)

        except (KeyError, ValueError):
            continue

    return vehicles


def telemetry_node(state: AgentState):

    telemetry = query_telemetry_db.invoke(
        {
            "sql_query": """
                SELECT TOP 3 *
                FROM FDE_VIEWS.VW_ACTIVE_FLEET
            """
        }
    )

    return {
        "telemetry": telemetry
    }


def weather_node(state: AgentState):

    telemetry = state.get("telemetry", "")

    vehicles = parse_telemetry(telemetry)

    if not vehicles:
        return {
            "weather": (
                "Weather data unavailable because "
                "telemetry data was not returned."
            )
        }

    weather_results = []

    for index, vehicle in enumerate(vehicles, start=1):

        weather = fetch_corridor_conditions.invoke(
            {
                "latitude": vehicle["latitude"],
                "longitude": vehicle["longitude"],
            }
        )

        weather_results.append(
            f"Vehicle {index}\n"
            f"Latitude: {vehicle['latitude']}\n"
            f"Longitude: {vehicle['longitude']}\n"
            f"{weather}"
        )

    return {
        "weather": "\n\n".join(weather_results)
    }


def sop_node(state: AgentState):

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

    return {
        "sop": sop
    }


def analysis_node(state: AgentState):

    telemetry = state.get("telemetry", "")

    vehicles = parse_telemetry(telemetry)

    if not vehicles:
        return {
            "analysis": "No valid telemetry records were available.",
            "required_actions": (
                "No actions available because telemetry "
                "was not returned."
            )
        }

    analysis_lines = []
    action_lines = []

    for index, vehicle in enumerate(vehicles, start=1):

        temperature = vehicle["temperature"]
        risk = vehicle["risk"]
        delay_probability = vehicle["delay_probability"]
        port_congestion = vehicle["port_congestion"]
        route_risk = vehicle["route_risk"]

        # ---------------------------------------------------------
        # TEMPERATURE STATUS
        # ---------------------------------------------------------

        if temperature > 4.0:

            temperature_status = "IMMEDIATE COLD-CHAIN BREACH"

        elif 0.0 <= temperature <= 4.0:

            temperature_status = (
                "Within normal fresh-perishables range"
            )

        else:

            temperature_status = (
                "Below the normal fresh-perishables range"
            )

        # ---------------------------------------------------------
        # DETERMINISTIC ACTION ENGINE
        # ---------------------------------------------------------

        actions = []

        # Rule 1:
        # IoT temperature above 4.0°C
        if temperature > 4.0:

            actions.append(
                "Contact driver to restart the auxiliary cooling unit"
            )

        # Rule 2:
        # Port congestion above 7.0
        if port_congestion > 7.0:

            actions.append(
                "Suspend standard routing and divert to the "
                "Inland Empire Overflow Depot in San Bernardino "
                "for cross-docking"
            )

        # Rule 3:
        # High Risk AND delay probability above 0.65
        if risk == "High Risk" and delay_probability > 0.65:

            actions.append(
                "Escalate to Tier 2 Logistics Manager"
            )

        if not actions:

            actions.append(
                "No immediate SOP-triggered action"
            )

        # ---------------------------------------------------------
        # DETERMINISTIC ANALYSIS
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # DETERMINISTIC REQUIRED ACTIONS
        # ---------------------------------------------------------

        action_lines.append(
            f"Vehicle {index}:"
        )

        for action in actions:

            action_lines.append(
                f"- {action}"
            )

    return {
        "analysis": "\n".join(analysis_lines),
        "required_actions": "\n".join(action_lines),
    }


def build_deterministic_report(state: AgentState):

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
        state.get("telemetry", "")
    )

    # -------------------------------------------------------------
    # OPERATIONAL ASSESSMENT
    # -------------------------------------------------------------

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
            f"{high_risk_count} vehicle(s) are classified as High Risk."
        )

    if temperature_breach_count > 0:

        assessment_parts.append(
            f"{temperature_breach_count} vehicle(s) exceed "
            "the 4.0°C immediate breach threshold."
        )

    if action_vehicle_count > 0:

        assessment_parts.append(
            f"{action_vehicle_count} vehicle(s) have "
            "deterministic SOP-triggered actions."
        )

    if not assessment_parts:

        assessment_parts.append(
            "No immediate SOP-triggered fleet actions were identified."
        )

    operational_assessment = " ".join(assessment_parts)

    # -------------------------------------------------------------
    # FLEET RISK SUMMARY
    # -------------------------------------------------------------

    fleet_lines = []

    if vehicles:

        for index, vehicle in enumerate(vehicles, start=1):

            temperature = vehicle["temperature"]

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

            fleet_lines.append(
                f"""**Vehicle {index}**
- Risk Classification: {vehicle['risk']}
- IoT Temperature: {temperature:.2f} °C
- Temperature Status: {temperature_status}
- Delay Probability: {vehicle['delay_probability']:.3f}
- Port Congestion Level: {vehicle['port_congestion']:.3f}
- Route Risk Index: {vehicle['route_risk']:.3f}"""
            )

    else:

        fleet_lines.append(
            "No valid fleet telemetry records were available."
        )

    fleet_summary = "\n\n".join(fleet_lines)

    # -------------------------------------------------------------
    # WEATHER SECTION
    # -------------------------------------------------------------

    weather_section = weather

    # -------------------------------------------------------------
    # SOP SECTION
    # -------------------------------------------------------------

    sop_section = sop

    # -------------------------------------------------------------
    # FINAL REPORT
    # -------------------------------------------------------------

    final_report = f"""### Operational Assessment

{operational_assessment}

### Fleet Risk Summary

{fleet_summary}

### Weather Conditions

{weather_section}

### Required Actions

{required_actions}

### SOP Compliance

{sop_section}
"""

    return final_report


def reasoner_node(state: AgentState):

    # -------------------------------------------------------------
    # IMPORTANT:
    #
    # The critical operational report is generated deterministically.
    #
    # We still initialize the LLM here so the architecture remains
    # ready for future natural-language reasoning tasks.
    #
    # The LLM is NOT allowed to modify:
    # - telemetry values
    # - risk classification
    # - temperature status
    # - required actions
    # -------------------------------------------------------------

    _ = get_llm()

    final_response = build_deterministic_report(state)

    return {
        "final_response": final_response
    }


def build_graph(llm=None):

    graph_builder = StateGraph(AgentState)

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