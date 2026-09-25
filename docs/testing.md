# Testing Documentation

## Cold-Chain Logistics AI

This document describes the testing and validation approach used for the Cold-Chain Logistics AI project.

The testing process covers:

- Intent parsing
- AI workflow execution
- Database tool behavior
- SQL security validation
- Weather integration
- Session handling
- Operational workflow behavior
- Streamlit application validation

---

# 1. Testing Objectives

The primary objectives of testing are to verify that:

1. Natural-language dispatcher requests are classified correctly.
2. The AI workflow executes the appropriate tools.
3. Database queries are restricted to the secure telemetry view.
4. Unauthorized SQL operations are rejected.
5. Raw telemetry table access is blocked.
6. Weather information is retrieved separately from telemetry.
7. LangGraph workflows execute successfully.
8. Session handling works correctly.
9. Operational responses are generated without tool failures.
10. Existing functionality remains stable after code changes.

---

# 2. Testing Environment

The project is developed and tested locally.

Primary environment:

```text
Operating System: Windows
Python: 3.12.x
IDE: PyCharm Community
Database: Microsoft SQL Server
Database: ColdChainLogistics
LLM Runtime: Ollama
LLM Model: qwen2.5:1.5b
Application: Streamlit
Test Framework: pytest
```

The project uses a Python virtual environment:

```text
.venv
```

---

# 3. Test Framework

The project uses:

```text
pytest
```

Tests are executed from the project root.

Run:

```powershell
pytest -q
```

The quiet mode provides a concise test result.

---

# 4. Current Test Result

The current test suite has been successfully executed.

Latest validated result:

```text
9 passed in 78.11s
```

Result:

```text
......... [100%]
9 passed in 78.11s (0:01:18)
```

This confirms that all nine automated tests passed during the latest recorded test run.

---

# 5. Test Categories

The project testing strategy can be divided into the following categories:

```text
                    Automated Tests
                          |
        +-----------------+-----------------+
        |                 |                 |
        v                 v                 v
   Intent Tests      Tool Tests       Workflow Tests
        |                 |                 |
        v                 v                 v
   Intent Parser     SQL Security      LangGraph
                                      Weather
                                      Session
```

Additional manual testing is performed for the Streamlit user interface.

---

# 6. Intent Parser Testing

The intent parser is implemented in:

```text
src/intent_parser.py
```

The parser converts dispatcher language into controlled operational intents.

Supported intents include:

```text
risk_analysis
temperature_breach
port_congestion
high_risk
delay_risk
route_risk
general
```

---

## 6.1 Temperature Intent

Example request:

```text
Show me vehicles with temperature above 4°C.
```

Expected intent:

```text
temperature_breach
```

---

## 6.2 Port Congestion Intent

Example request:

```text
Which vehicles are affected by port congestion?
```

Expected intent:

```text
port_congestion
```

---

## 6.3 High-Risk Intent

Example request:

```text
Show me high risk vehicles.
```

Expected intent:

```text
high_risk
```

---

## 6.4 Delay Intent

Example request:

```text
Which vehicles have delay risk?
```

Expected intent:

```text
delay_risk
```

---

## 6.5 Route Risk Intent

Example request:

```text
Which routes are risky?
```

Expected intent:

```text
route_risk
```

---

## 6.6 General Intent

Requests that do not match a defined operational category should fall back to:

```text
general
```

---

# 7. Database Tool Testing

The database tool is implemented in:

```text
src/agent_tools.py
```

The primary database tool is:

```text
query_telemetry_db
```

The tool is designed to query:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

---

# 8. Secure View Validation

A valid query should reference:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

Example:

```sql
SELECT TOP 10 *
FROM FDE_VIEWS.VW_ACTIVE_FLEET;
```

The tool should execute the query and return telemetry data when the database is available.

---

# 9. Invalid Table Validation

The application should reject direct access to:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

Example:

```sql
SELECT TOP 10 *
FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

Expected behavior:

```text
ERROR: Direct access to the raw fleet table is not allowed.
```

This verifies the application-level raw-table protection.

---

# 10. SELECT-Only Validation

The database tool only accepts SELECT queries.

An operation such as:

```sql
DELETE FROM FDE_VIEWS.VW_ACTIVE_FLEET;
```

must be rejected.

Similarly:

```sql
UPDATE FDE_VIEWS.VW_ACTIVE_FLEET
SET Current_Temperature_C = 0;
```

must be rejected.

This ensures that the AI telemetry tool remains read-oriented.

---

# 11. Destructive SQL Validation

The tool rejects potentially destructive SQL operations.

The blocked operations include:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
EXEC
EXECUTE
MERGE
```

Testing should confirm that each blocked operation returns an appropriate error instead of being executed.

---

# 12. SQL Server Syntax Validation

SQL Server uses:

```text
TOP
```

rather than:

```text
LIMIT
```

Therefore a query such as:

```sql
SELECT *
FROM FDE_VIEWS.VW_ACTIVE_FLEET
LIMIT 10;
```

should be rejected.

A valid SQL Server query is:

```sql
SELECT TOP 10 *
FROM FDE_VIEWS.VW_ACTIVE_FLEET;
```

---

# 13. Result Limiting

The telemetry tool limits the number of records returned to the AI workflow.

The current maximum is:

```text
10 rows
```

This keeps tool output controlled and reduces unnecessary data transfer into the AI workflow.

---

# 14. Database Permission Testing

Database permissions were independently verified using SQL Server impersonation.

The verification uses:

```sql
EXECUTE AS USER = 'USR_FDE_RO';
```

The latest verified permission results were:

```text
CurrentUser        USR_FDE_RO
RawTableSelect     0
SecureViewSelect   1
AuditSelect        1
```

---

# 15. Permission Test Interpretation

The permission results confirm:

### Raw table

```text
RawTableSelect = 0
```

The application user does not have SELECT permission on the raw telemetry table.

### Secure view

```text
SecureViewSelect = 1
```

The application user can access the secure telemetry view.

### Audit table

```text
AuditSelect = 1
```

The application user has the required SELECT permission on the audit table.

---

# 16. Weather Integration Testing

The weather tool is:

```text
fetch_corridor_conditions
```

The tool uses Open-Meteo.

The weather response contains:

```text
Current temperature
Wind speed
Disruption index
```

The weather information must remain separate from vehicle telemetry.

---

# 17. Weather Data Separation

The system distinguishes:

```text
Vehicle IoT Temperature
```

from:

```text
Weather Temperature
```

For example:

```text
Current_Temperature_C
```

represents vehicle telemetry.

The weather API's:

```text
temperature_2m
```

represents environmental weather temperature.

These values should not be mixed.

---

# 18. Weather Workflow Test

A combined operational request can be used to test the weather workflow.

Example:

```text
Check the active fleet telemetry, check the current weather conditions, and provide a short operational assessment.
```

The expected workflow is:

```text
User Request
     |
     v
LangGraph
     |
     v
Telemetry Tool
     |
     v
Vehicle Location
     |
     v
Weather Tool
     |
     v
Operational Assessment
```

The workflow must provide a valid `session_id`.

The current test pattern uses:

```python
from uuid import uuid4
```

and passes:

```python
"session_id": str(uuid4())
```

to the graph invocation.

---

# 19. LangGraph Workflow Testing

The main orchestration logic is implemented in:

```text
src/orchestrator.py
```

The graph is constructed using:

```python
graph = build_graph()
```

A test invocation can provide:

```python
result = graph.invoke(
    {
        "user_request": "...",
        "session_id": str(uuid4()),
    }
)
```

The final response is obtained using:

```python
result["final_response"]
```

---

# 20. Session Handling

The LangGraph workflow requires a valid session identifier for the tested workflow.

The test uses:

```python
str(uuid4())
```

to generate a unique session ID.

This prevents workflow execution failures caused by missing session state.

The pattern is:

```python
result = graph.invoke(
    {
        "user_request": user_request,
        "session_id": str(uuid4()),
    }
)
```

---

# 21. End-to-End Workflow Testing

An end-to-end test validates the complete operational pipeline.

Example:

```text
Check the active fleet. Identify temperature breaches and high-risk vehicles, then provide the required operational actions.
```

Expected workflow:

```text
Dispatcher Request
        |
        v
Intent Detection
        |
        v
LangGraph Orchestration
        |
        v
Telemetry Retrieval
        |
        v
SOP / Rule Evaluation
        |
        v
Operational Assessment
        |
        v
Final Response
```

---

# 22. Operational Rule Testing

The main operational thresholds should be validated independently.

## Temperature Rule

Condition:

```text
Current_Temperature_C > 4.0
```

Expected interpretation:

```text
Immediate cold-chain breach
```

---

## Port Congestion Rule

Condition:

```text
Port_Congestion_Level > 7.0
```

Expected interpretation:

```text
Suspend standard routing and divert to
Inland Empire Overflow Depot in San Bernardino
for cross-docking.
```

---

## High-Risk Rule

Condition:

```text
Risk Classification = High Risk
AND
Delay Probability > 0.65
```

Expected interpretation:

```text
Escalate to Tier 2 Logistics Manager.
```

---

## Delay Rule

Condition:

```text
ETA delay > 1 hour
```

Expected interpretation:

```text
Consider diversion to the nearest emergency
cold-storage facility.
```

---

# 23. SOP Retrieval Testing

The SOP search tool is:

```text
search_compliance_sop
```

It uses:

```text
Pinecone
```

and:

```text
BAAI/bge-m3
```

embeddings.

The tool should return relevant SOP content for operational queries.

Example:

```text
What should be done when vehicle temperature exceeds 4°C?
```

Expected behavior:

```text
Relevant cold-chain incident procedure is retrieved.
```

---

# 24. Tool Failure Testing

The application should not invent information when a tool fails.

For example, if the weather API is unavailable, the system should report a weather API error instead of creating a weather value.

Similarly, if the database query fails, the system should report the database failure.

Expected principle:

```text
Tool failure
     |
     v
Report failure
     |
     X
Do not invent data
```

---

# 25. Streamlit UI Testing

The Streamlit interface is implemented in:

```text
src/ui.py
```

The application can be started using:

```powershell
python -m streamlit run src/ui.py
```

The UI should be manually checked for:

- Application startup
- Dispatcher Command Center
- KPI cards
- Risk summaries
- Temperature information
- Priority actions
- Executive Assessment
- Detailed Operational Report
- Quick queries
- Presentation Mode
- Developer Mode

---

# 26. Dispatcher Query Testing

The following queries should be tested manually through the UI.

### Query 1

```text
Show me all vehicles with temperature above 4°C and tell me what action is required.
```

### Query 2

```text
Show me all vehicles affected by port congestion above 7 and tell me what routing action is required.
```

### Query 3

```text
Show me all vehicles with delay risk and tell me which vehicles require diversion to emergency cold storage.
```

### Query 4

```text
Show me all High Risk vehicles with delay probability above 0.65 and tell me which vehicles require Tier 2 Logistics Manager escalation.
```

### Query 5

```text
Check the current weather conditions for the active fleet and identify vehicles operating in higher disruption conditions.
```

---

# 27. Presentation Mode Testing

The application includes a Presentation Mode designed to provide a cleaner project demonstration interface.

The presentation mode should be checked for:

- Reduced technical clutter
- KPI visibility
- Executive Assessment
- Priority Actions
- Clear operational summaries
- Expandable detailed report

The detailed technical report can remain collapsed until required.

---

# 28. Developer Mode Testing

Developer Mode provides additional technical information useful during development and debugging.

The developer interface should be checked for:

- Intent information
- Tool activity
- Technical results
- Operational details
- Debug information

The mode is intended primarily for project development and demonstration.

---

# 29. Regression Testing

After modifying application code, the complete automated test suite should be executed.

Use:

```powershell
pytest -q
```

The expected outcome is:

```text
9 passed
```

If a test fails:

1. Identify the failing test.
2. Determine whether the failure is caused by the code change.
3. Fix the issue.
4. Run the full test suite again.
5. Do not commit until the regression suite passes.

---

# 30. Code Validation

Python syntax can be checked using:

```powershell
python -m py_compile src/ui.py
```

For other modified source files, run:

```powershell
python -m py_compile src/agent_tools.py
python -m py_compile src/intent_parser.py
python -m py_compile src/orchestrator.py
python -m py_compile src/llm.py
```

A successful command produces no syntax error.

---

# 31. Git Validation

Before committing changes, check:

```powershell
git status
```

Then:

```powershell
git diff --check
```

The second command checks for whitespace and patch formatting problems.

Review changes using:

```powershell
git diff
```

Only after reviewing the changes should they be committed.

---

# 32. Recommended Validation Sequence

For a normal development change, use:

```powershell
git status
```

then:

```powershell
git diff --check
```

then:

```powershell
pytest -q
```

then:

```powershell
python -m py_compile src/ui.py
```

Then review:

```powershell
git diff
```

Finally:

```powershell
git add .
git commit -m "Describe the change"
git push origin main
```

---

# 33. Current Validation Status

The latest recorded automated test execution produced:

```text
......... [100%]
9 passed in 78.11s (0:01:18)
```

Therefore:

```text
Automated Tests: PASS
```

The database permission verification also produced:

```text
CurrentUser        USR_FDE_RO
RawTableSelect     0
SecureViewSelect   1
AuditSelect        1
```

Therefore:

```text
Database Permission Verification: PASS
```

---

# 34. Testing Checklist

## Automated Testing

- [x] Test suite executed
- [x] 9 tests passed
- [x] Intent workflow tested
- [x] Tool behavior tested
- [x] Workflow execution tested
- [x] Weather workflow tested
- [x] Session handling validated

## Database Testing

- [x] Secure view verified
- [x] Raw table SELECT restriction verified
- [x] Audit permissions verified
- [x] Application user verified
- [x] SQL validation implemented

## Application Testing

- [x] Streamlit application tested
- [x] Dispatcher Command Center tested
- [x] KPI interface tested
- [x] Operational assessment tested
- [x] Presentation Mode tested
- [x] Developer Mode tested

## Code Quality

- [x] Python syntax validation
- [x] Git diff validation
- [x] Regression testing
- [x] Git repository maintained

---

# 35. Testing Limitations

The current test suite is primarily focused on the project's core application workflow.

Additional testing would be required for a production deployment, including:

- Load testing
- Concurrent dispatcher testing
- Penetration testing
- API failure simulation
- Database failover testing
- Long-duration monitoring
- Security penetration testing
- Authentication testing
- Authorization testing
- Production infrastructure testing

These are outside the scope of the current academic implementation.

---

# 36. Final Testing Summary

The testing strategy validates the project at multiple levels:

```text
Unit / Component Testing
          |
          v
Tool Validation
          |
          v
Database Security Validation
          |
          v
LangGraph Workflow Testing
          |
          v
End-to-End Testing
          |
          v
Streamlit UI Testing
```

The latest automated validation successfully completed with:

```text
9 passed
```

The database permission model was also independently verified.

The project therefore has documented evidence covering its core application workflow, database security boundaries, and dispatcher-facing functionality.