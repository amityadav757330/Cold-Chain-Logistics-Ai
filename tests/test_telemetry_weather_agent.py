from src.orchestrator import build_graph

graph = build_graph()

result = graph.invoke(
    {
        "user_request": (
            "Check the active fleet telemetry, "
            "check the current weather conditions, "
            "and provide a short operational assessment."
        )
    }
)

print("\n===== FINAL RESPONSE =====\n")
print(result["final_response"])