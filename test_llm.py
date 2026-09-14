from src.llm import get_llm
from src.orchestrator import build_graph


llm = get_llm()

graph = build_graph(llm)

result = graph.invoke(
    {
        "messages": [
            (
                "user",
                "Show me 3 fleet telemetry records from the secure telemetry view."
            )
        ]
    }
)

print("\n===== FINAL RESPONSE =====\n")

for message in result["messages"]:
    if hasattr(message, "content") and message.content:
        print(message.content)