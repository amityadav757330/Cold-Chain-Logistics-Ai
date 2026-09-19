from src.orchestrator import build_graph


graph = build_graph()


result = graph.invoke(
    {
        "user_request": "Which trucks need attention right now?",
        "session_id": "TEST-SESSION-001",
    }
)


print("\n" + "=" * 70)
print("FINAL RESPONSE")
print("=" * 70)

print(result.get("final_response", "No final response."))


print("\n" + "=" * 70)
print("INTENT")
print("=" * 70)

print(result.get("intent", "No intent found."))


print("\n" + "=" * 70)
print("TELEMETRY")
print("=" * 70)

print(result.get("telemetry", "No telemetry."))


print("\n" + "=" * 70)
print("WEATHER")
print("=" * 70)

print(result.get("weather", "No weather data."))


print("\n" + "=" * 70)
print("SOP")
print("=" * 70)

print(result.get("sop", "No SOP data."))


print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print(result.get("analysis", "No analysis."))


print("\n" + "=" * 70)
print("ACTIONS")
print("=" * 70)

for action in result.get("actions", []):
    print(action)


print("\n" + "=" * 70)
print("STATUS")
print("=" * 70)

print("Telemetry:", result.get("telemetry_status"))
print("Weather:", result.get("weather_status"))
print("SOP:", result.get("sop_status"))
print("Analysis:", result.get("analysis_status"))
print("Reasoner:", result.get("reasoner_status"))

print("\nTest completed successfully.")