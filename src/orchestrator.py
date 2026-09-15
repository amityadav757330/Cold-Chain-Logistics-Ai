from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
)
from src.llm import get_llm


class AgentState(TypedDict, total=False):
    user_request: str
    telemetry: str
    weather: str
    analysis: str
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
            "weather": "Weather data unavailable because telemetry data was not returned."
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


def analysis_node(state: AgentState):
    telemetry = state.get("telemetry", "")
    weather = state.get("weather", "")

    vehicles = parse_telemetry(telemetry)

    if not vehicles:
        return {
            "analysis": "No valid telemetry records were available."
        }

    analysis_lines = []

    for index, vehicle in enumerate(vehicles, start=1):

        temperature = vehicle["temperature"]
        risk = vehicle["risk"]
        delay_probability = vehicle["delay_probability"]
        port_congestion = vehicle["port_congestion"]
        route_risk = vehicle["route_risk"]

        if temperature > 4.0:
            temperature_status = "IMMEDIATE COLD-CHAIN BREACH"
        elif 0.0 <= temperature <= 4.0:
            temperature_status = "Within normal fresh-perishables range"
        else:
            temperature_status = "Below the normal fresh-perishables range"

        actions = []

        if temperature > 4.0:
            actions.append(
                "Contact driver to restart the auxiliary cooling unit"
            )

        if port_congestion > 7.0:
            actions.append(
                "Suspend standard routing and divert to the Inland Empire Overflow Depot in San Bernardino for cross-docking"
            )

        if risk == "High Risk" and delay_probability > 0.65:
            actions.append(
                "Escalate to Tier 2 Logistics Manager"
            )

        if not actions:
            actions.append("No immediate SOP-triggered action")

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

    return {
        "analysis": "\n".join(analysis_lines)
    }


def reasoner_node(state: AgentState):
    llm = get_llm()

    system_prompt = load_system_prompt()

    user_request = state.get(
        "user_request",
        "Analyze the active fleet and current weather conditions."
    )

    analysis = state.get("analysis", "")
    weather = state.get("weather", "")

    prompt = f"""
USER REQUEST:
{user_request}

DETERMINISTIC FLEET RISK ANALYSIS:
{analysis}

CURRENT WEATHER DATA:
{weather}

Create a concise operational assessment.

IMPORTANT:
- The deterministic fleet analysis is authoritative.
- Do NOT change any latitude, longitude, temperature, risk, delay probability,
  congestion, or route-risk values.
- Do NOT invent missing information.
- Keep IoT temperature separate from weather temperature.
- Weather values must come only from CURRENT WEATHER DATA.
- Do not reinterpret the numeric Cargo Condition Code.
- Clearly identify vehicles requiring action.
- Explain the most important operational risks.
- Follow the SOP rules provided in the system instructions.
- Keep the response under approximately 300 words.
"""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "final_response": response.content
    }


def build_graph(llm=None):
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("telemetry", telemetry_node)
    graph_builder.add_node("weather", weather_node)
    graph_builder.add_node("analysis", analysis_node)
    graph_builder.add_node("reasoner", reasoner_node)

    graph_builder.add_edge(START, "telemetry")
    graph_builder.add_edge("telemetry", "weather")
    graph_builder.add_edge("weather", "analysis")
    graph_builder.add_edge("analysis", "reasoner")
    graph_builder.add_edge("reasoner", END)

    return graph_builder.compile()