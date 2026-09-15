from src.agent_tools import query_telemetry_db


result = query_telemetry_db.invoke(
    {
        "sql_query": """
        SELECT TOP 3 *
        FROM FDE_VIEWS.VW_ACTIVE_FLEET
        """
    }
)

print("\n===== TELEMETRY RESULT =====\n")
print(result)