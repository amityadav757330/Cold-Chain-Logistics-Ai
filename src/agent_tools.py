import os
import re

import pyodbc
from dotenv import load_dotenv
from langchain_core.tools import tool


load_dotenv()


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('FDE_DB_SERVER')};"
    f"DATABASE={os.getenv('FDE_DB_NAME')};"
    f"UID={os.getenv('FDE_DB_USER')};"
    f"PWD={os.getenv('FDE_DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)


@tool
def query_telemetry_db(sql_query: str) -> str:
    """
    Query the secure fleet telemetry view.

    Only SELECT queries against FDE_VIEWS.VW_ACTIVE_FLEET are allowed.
    SQL Server syntax must be used.
    Maximum 10 rows can be returned.
    """

    query = sql_query.strip()

    # Remove markdown code fences if the model sends them
    query = re.sub(r"^```sql\s*", "", query, flags=re.IGNORECASE)
    query = re.sub(r"^```\s*", "", query)
    query = re.sub(r"\s*```$", "", query)
    query = query.strip()

    # Only SELECT statements are allowed
    if not re.match(r"^SELECT\b", query, re.IGNORECASE):
        return "ERROR: Only SELECT queries are allowed."

    upper_query = query.upper()

    # Block database modification operations
    blocked = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "EXEC",
        "EXECUTE",
        "MERGE",
    ]

    for keyword in blocked:
        if re.search(rf"\b{keyword}\b", upper_query):
            return f"ERROR: SQL operation '{keyword}' is not allowed."

    # Only allow the secure view
    if "FDE_VIEWS.VW_ACTIVE_FLEET" not in upper_query:
        return "ERROR: Query must use FDE_VIEWS.VW_ACTIVE_FLEET."

    # Prevent direct access to raw table
    if "TBL_SC_FLEET_HIST_RAW" in upper_query:
        return "ERROR: Direct access to the raw fleet table is not allowed."

    # SQL Server does not support LIMIT
    if re.search(r"\bLIMIT\b", upper_query):
        return "ERROR: SQL Server does not support LIMIT. Use TOP instead."

    # Remove trailing semicolon
    query = query.rstrip(";").strip()

    # Add TOP 10 if the model did not specify a limit
    if not re.search(r"\bTOP\s+\d+\b", query, re.IGNORECASE):
        query = re.sub(
            r"^SELECT\s+",
            "SELECT TOP 10 ",
            query,
            count=1,
            flags=re.IGNORECASE,
        )

    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        cursor.execute(query)

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchmany(10)

        cursor.close()
        conn.close()

        if not rows:
            return "No telemetry records found."

        result = [", ".join(columns)]

        for row in rows:
            result.append(
                ", ".join(
                    str(value) if value is not None else "NULL"
                    for value in row
                )
            )

        return "\n".join(result)

    except Exception as e:
        return f"Database query error: {str(e)}"