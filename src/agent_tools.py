import re
import pyodbc
from langchain_core.tools import tool


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=ColdChainLogistics;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


@tool
def query_telemetry_db(sql_query: str) -> str:
    """
    Query the secure fleet telemetry view.

    Only SELECT queries against FDE_VIEWS.VW_ACTIVE_FLEET are allowed.
    A maximum of 10 rows is returned.
    """

    query = sql_query.strip()

    # Only SELECT statements are allowed
    if not re.match(r"^SELECT\b", query, re.IGNORECASE):
        return "ERROR: Only SELECT queries are allowed."

    # Block SQL statements that could modify the database
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

    upper_query = query.upper()

    for keyword in blocked:
        if re.search(rf"\b{keyword}\b", upper_query):
            return f"ERROR: SQL operation '{keyword}' is not allowed."

    # Only allow the secure telemetry view
    if "VW_ACTIVE_FLEET" not in upper_query:
        return "ERROR: Query must use FDE_VIEWS.VW_ACTIVE_FLEET."

    # Prevent direct access to the raw table
    if "TBL_SC_FLEET_HIST_RAW" in upper_query:
        return "ERROR: Direct access to the raw fleet table is not allowed."

    # Add TOP 10 if the query doesn't already contain TOP
    if not re.search(r"\bTOP\s+\d+", query, re.IGNORECASE):
        query = re.sub(
            r"^SELECT\b",
            "SELECT TOP 10",
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