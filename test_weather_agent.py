from src.llm import get_llm
from src.orchestrator import build_graph


llm = get_llm()

graph = build_graph(llm)

result = graph.invoke(
    {
        "messages": [
            (
                "user",
                "Check the current weather conditions at latitude 40.375568 "
                "and longitude -77.014318."
            )
        ]
    }
)

print("\n===== FINAL RESPONSE =====\n")

for message in result["messages"]:
    if hasattr(message, "content") and message.content:
        print(message.content)