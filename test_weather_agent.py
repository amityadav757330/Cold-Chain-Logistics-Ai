from uuid import uuid4

from src.orchestrator import build_graph


graph = build_graph()

result = graph.invoke(
    {
        "user_request": (
            "Check the active fleet telemetry, "
            "check the current weather conditions, "
            "and provide a short operational assessment."
        ),
        "session_id": str(uuid4()),
    }
)

print("\n===== FINAL RESPONSE =====\n")
print(result["final_response"])