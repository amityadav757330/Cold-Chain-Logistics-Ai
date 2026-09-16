import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.agent_tools import search_compliance_sop


query = "What should be done if IoT temperature exceeds 4 degrees Celsius?"

result = search_compliance_sop.invoke(
    {
        "query": query
    }
)

print("\n===== SOP TOOL RESULT =====\n")
print(result)