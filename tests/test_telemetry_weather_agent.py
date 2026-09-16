import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator import build_graph


graph = build_graph()

result = graph.invoke(
    {
        "user_request": (
            "Check the active fleet telemetry, "
            "check the current weather conditions, "
            "check the relevant cold-chain SOP, "
            "and provide a short operational assessment."
        )
    }
)

print("\n===== FINAL RESPONSE =====\n")
print(result["final_response"])