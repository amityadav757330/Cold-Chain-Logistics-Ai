from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
)


# Step 1: Get fleet telemetry
telemetry = query_telemetry_db.invoke(
    {
        "sql_query": """
        SELECT TOP 3 *
        FROM FDE_VIEWS.VW_ACTIVE_FLEET
        """
    }
)

print("\n===== TELEMETRY =====\n")
print(telemetry)


# Step 2: Test weather for one vehicle
weather = fetch_corridor_conditions.invoke(
    {
        "latitude": 40.375568475194925,
        "longitude": -77.0143177425258,
    }
)

print("\n===== WEATHER =====\n")
print(weather)