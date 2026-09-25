# Security Documentation

## Cold-Chain Logistics AI

This document describes the security controls implemented in the Cold-Chain Logistics AI project.

The security design focuses on:

- Least-privilege database access
- Secure telemetry access
- Raw-table protection
- SQL query validation
- Credential protection
- Auditability
- Separation between AI tools and underlying systems

---

# 1. Security Objectives

The project is designed to prevent the AI application from receiving unnecessary privileges or unrestricted access to operational data.

The primary security objectives are:

1. Restrict database access to the information required by the application.
2. Prevent direct access to raw telemetry data through the AI telemetry tool.
3. Prevent destructive SQL operations.
4. Protect database credentials and API keys.
5. Maintain operational auditability.
6. Separate telemetry, weather, and SOP information.
7. Ensure that AI-generated responses are grounded in tool results.

---

# 2. Database Security Architecture

The application uses Microsoft SQL Server.

The database is:

```text
ColdChainLogistics
```

The raw telemetry table is:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

The application is designed to access the secure view:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

The overall architecture is:

```text
Raw Fleet Telemetry
        |
        v
dbo.TBL_SC_FLEET_HIST_RAW
        |
        v
FDE_VIEWS.VW_ACTIVE_FLEET
        |
        v
USR_FDE_RO
        |
        v
AI Telemetry Tool
        |
        v
LangGraph Application
```

The AI application should interact with the secure view rather than directly accessing the raw telemetry table.

---

# 3. Least-Privilege Database Account

The application uses a dedicated SQL Server account:

```text
USR_FDE_RO
```

The account is intended to provide only the permissions required by the application.

The security model separates:

```text
Raw database administration
```

from:

```text
Application telemetry access
```

This reduces the impact of an application-level SQL error or unauthorized query.

---

# 4. Secure Telemetry View

The application uses:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

instead of directly querying:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

The secure view exposes operational fields required by the AI assistant, including:

```text
Timestamp
Latitude
Longitude
Current_Temperature_C
Cargo_Condition_Code
Risk_Classification
Delay_Probability
Port_Congestion_Level
Route_Risk_Index
```

This provides a controlled interface between the application and the underlying database.

---

# 5. Raw Table Protection

The raw telemetry table is:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

The application account is not intended to have direct SELECT access to this table.

The AI telemetry tool also contains an application-level protection against direct raw-table queries.

For example, a query containing:

```text
TBL_SC_FLEET_HIST_RAW
```

is rejected by the tool.

This creates two security boundaries:

```text
Database permission boundary
            +
Application query validation
```

---

# 6. SQL Query Validation

The telemetry tool is implemented in:

```text
src/agent_tools.py
```

The `query_telemetry_db` tool validates the requested SQL before executing it.

Only SELECT queries are accepted.

The query must use:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

---

# 7. Blocked SQL Operations

The application explicitly blocks potentially destructive or unauthorized SQL operations.

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

For example, a request containing:

```sql
DROP TABLE ...
```

is rejected before the database query is executed.

Similarly:

```sql
DELETE FROM ...
```

is rejected.

The objective is to keep the AI telemetry tool read-oriented.

---

# 8. Required Secure View

The telemetry tool verifies that the query references:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

If the query does not use the required secure view, the application returns an error.

This prevents the tool from being used as a general-purpose database query interface.

---

# 9. Raw Table Query Protection

The application explicitly rejects queries containing:

```text
TBL_SC_FLEET_HIST_RAW
```

This is an additional application-layer safeguard.

For example:

```sql
SELECT *
FROM dbo.TBL_SC_FLEET_HIST_RAW
```

is rejected by the telemetry tool.

The intended query target is:

```sql
SELECT *
FROM FDE_VIEWS.VW_ACTIVE_FLEET
```

---

# 10. SQL Server Syntax Validation

The application expects SQL Server syntax.

The tool rejects:

```text
LIMIT
```

because SQL Server uses:

```text
TOP
```

instead.

If a query does not specify a TOP limit, the application automatically adds:

```sql
TOP 10
```

to the SELECT statement.

---

# 11. Result Limiting

The telemetry tool limits returned records.

The current implementation retrieves a maximum of:

```text
10 rows
```

This limits the amount of database information returned directly to the AI workflow.

The purpose is to keep tool responses controlled and manageable.

---

# 12. Database Connection

The database connection is configured through environment variables.

The application reads:

```text
FDE_DB_SERVER
FDE_DB_NAME
FDE_DB_USER
FDE_DB_PASSWORD
```

The connection configuration is loaded using:

```python
from dotenv import load_dotenv
```

Credentials are therefore kept outside the source-code files.

---

# 13. Environment Variable Protection

The project's `.env` file contains sensitive configuration such as:

```text
FDE_DB_PASSWORD
PINECONE_API_KEY
```

The `.env` file is excluded from Git through:

```text
.gitignore
```

The project provides:

```text
.env.example
```

as a safe configuration template.

The example file contains placeholders rather than real credentials.

---

# 14. Git Protection

The project `.gitignore` excludes sensitive files including:

```text
.env
.env.*
```

while allowing:

```text
.env.example
```

This means developers can commit the configuration template without committing actual credentials.

---

# 15. Pinecone API Security

The SOP retrieval component uses Pinecone.

The API key is supplied through:

```text
PINECONE_API_KEY
```

rather than being hard-coded into the application.

The Pinecone index is configured using:

```text
PINECONE_INDEX
```

This keeps the external vector database configuration separate from application source code.

---

# 16. Weather API Security

Weather information is retrieved using the Open-Meteo API.

The weather tool:

```text
fetch_corridor_conditions
```

accepts:

```text
latitude
longitude
```

and requests current weather information.

The weather integration does not require the application's SQL Server credentials.

This maintains separation between:

```text
Database credentials
```

and:

```text
External weather service
```

---

# 17. AI Tool Boundaries

The AI assistant does not receive unrestricted access to external systems.

Instead, system capabilities are exposed through specific tools.

The main tools include:

```text
query_telemetry_db
fetch_corridor_conditions
search_compliance_sop
```

Each tool has a defined responsibility.

### Telemetry Tool

```text
query_telemetry_db
```

Responsible for controlled fleet telemetry access.

### Weather Tool

```text
fetch_corridor_conditions
```

Responsible for retrieving corridor weather information.

### SOP Tool

```text
search_compliance_sop
```

Responsible for retrieving compliance procedures.

---

# 18. Separation of Data Sources

The application intentionally separates information from different sources.

```text
SQL Server
    |
    +--> Vehicle telemetry

Open-Meteo
    |
    +--> Weather conditions

Pinecone
    |
    +--> SOP information
```

These sources should not be treated as interchangeable.

For example:

```text
Current_Temperature_C
```

is the vehicle's IoT telemetry temperature.

It is not the same as:

```text
Weather temperature
```

returned by Open-Meteo.

---

# 19. Preventing Invented Operational Data

The system prompt instructs the AI assistant not to invent missing tool information.

The assistant is expected to use:

```text
Database results
Weather tool results
SOP search results
```

when making operational assessments.

If a tool fails, the assistant should report the failure rather than fabricate a value.

This is particularly important for:

- Temperature
- Weather
- Delay probability
- Port congestion
- Risk classification
- SOP procedures

---

# 20. Operational Rule Security

Operational recommendations are based on defined project rules.

Examples include:

### Temperature

```text
Current_Temperature_C > 4.0°C
```

indicates an immediate cold-chain breach.

### Port Congestion

```text
Port_Congestion_Level > 7.0
```

requires suspension of standard routing and diversion to the designated Inland Empire Overflow Depot in San Bernardino for cross-docking.

### High Risk

```text
Risk Classification = High Risk
AND
Delay Probability > 0.65
```

requires escalation to a Tier 2 Logistics Manager.

### Delay

```text
ETA delay > 1 hour
```

requires consideration of diversion to the nearest emergency cold-storage facility.

The AI assistant should apply these rules only when the relevant information is available.

---

# 21. Audit Infrastructure

The project includes an audit table:

```text
FDE_VIEWS.AgentAuditLog
```

The purpose of the audit infrastructure is to provide traceability for operational activity.

Audit information can support:

- Operational review
- Incident investigation
- AI workflow traceability
- Dispatcher activity analysis
- Compliance review

The application account has been granted the required access to the audit infrastructure.

---

# 22. Permission Verification

Database permissions were explicitly verified using SQL Server impersonation.

The verification used:

```sql
EXECUTE AS USER = 'USR_FDE_RO';
```

The permission checks confirmed the intended access model.

The verified results were:

```text
CurrentUser        USR_FDE_RO
RawTableSelect     0
SecureViewSelect   1
AuditSelect        1
```

This demonstrates that the application user:

- Does not have SELECT permission on the raw telemetry table.
- Has SELECT permission on the secure telemetry view.
- Has SELECT permission on the audit table.

---

# 23. Security Verification Model

The database security model can therefore be represented as:

```text
                    USR_FDE_RO
                         |
          +--------------+--------------+
          |                             |
          v                             v
FDE_VIEWS.VW_ACTIVE_FLEET      FDE_VIEWS.AgentAuditLog
          |
          |
          X
          |
dbo.TBL_SC_FLEET_HIST_RAW
```

The `X` represents the intended absence of raw-table SELECT permission.

---

# 24. Application-Level Defense in Depth

Security is not implemented at only one layer.

The project uses multiple controls:

```text
Layer 1
Database permissions
        |
        v
Layer 2
Secure SQL view
        |
        v
Layer 3
Application SQL validation
        |
        v
Layer 4
Tool-specific access
        |
        v
Layer 5
AI system instructions
```

This provides defense in depth.

---

# 25. SQL Injection Considerations

The telemetry tool does not expose unrestricted SQL execution.

It validates the generated query before sending it to SQL Server.

The validation checks:

- Query starts with SELECT
- Required secure view is referenced
- Forbidden operations are absent
- Raw table is not referenced
- SQL Server syntax is used
- Result size is limited

However, the current implementation is a controlled application-level SQL validation layer rather than a complete SQL parser.

For a production deployment, additional controls could include:

- Parameterized query templates
- Stored procedures
- SQL parser-based validation
- Query allowlists
- Read-only database roles
- Network restrictions
- Database activity monitoring

---

# 26. Credential Security

Sensitive credentials should never be placed directly inside source code.

Avoid:

```python
password = "actual_password"
```

Instead, the project uses:

```text
.env
```

and environment variables.

Example:

```text
FDE_DB_PASSWORD=your_database_password
```

The actual password should remain local.

---

# 27. Source-Control Security

Before pushing changes to GitHub, verify:

```powershell
git status
```

and ensure sensitive files are not staged.

A useful check is:

```powershell
git status
```

followed by:

```powershell
git diff --cached
```

before committing.

The `.env` file should not appear as a staged file.

---

# 28. Local Development Security

During local development:

1. Use the project's virtual environment.
2. Keep credentials in `.env`.
3. Do not commit `.env`.
4. Use the least-privilege database account.
5. Test the secure view instead of the raw table.
6. Run the automated tests before pushing changes.
7. Review Git changes before committing.

---

# 29. Production Security Considerations

The current project is primarily a development/academic implementation.

A production deployment would require additional controls.

Potential production improvements include:

- Secret management service
- Managed identity
- Database TLS configuration
- Network segmentation
- Firewall rules
- Private database connectivity
- Role-based application access
- Centralized logging
- Security monitoring
- API rate limiting
- Authentication
- Authorization
- Automated secret rotation
- Database backup and recovery controls

These are future production-hardening considerations and are not claimed as implemented by the current local project.

---

# 30. Security Testing

Security-related behavior should be verified through both application and database tests.

Important checks include:

### Raw table access

Verify:

```text
USR_FDE_RO
```

cannot SELECT from:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

### Secure view access

Verify:

```text
USR_FDE_RO
```

can SELECT from:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

### Audit access

Verify the required audit permissions.

### SQL validation

Verify that the application rejects:

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

### Raw-table query

Verify that a query referencing:

```text
TBL_SC_FLEET_HIST_RAW
```

is rejected.

### LIMIT syntax

Verify that:

```text
LIMIT
```

is rejected because SQL Server uses:

```text
TOP
```

---

# 31. Security Test Examples

The following types of requests should be rejected by the telemetry tool:

```sql
DROP TABLE dbo.TBL_SC_FLEET_HIST_RAW;
```

```sql
DELETE FROM FDE_VIEWS.VW_ACTIVE_FLEET;
```

```sql
UPDATE FDE_VIEWS.VW_ACTIVE_FLEET
SET Current_Temperature_C = 0;
```

```sql
SELECT *
FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

```sql
SELECT *
FROM FDE_VIEWS.VW_ACTIVE_FLEET
LIMIT 10;
```

A valid read query should instead use SQL Server syntax and the secure view:

```sql
SELECT TOP 10 *
FROM FDE_VIEWS.VW_ACTIVE_FLEET;
```

---

# 32. Security Responsibilities

Security responsibilities are divided across the architecture.

| Component | Security Responsibility |
|---|---|
| Streamlit | User-facing application interface |
| Intent Parser | Controlled interpretation of user requests |
| LangGraph | Controlled workflow orchestration |
| Telemetry Tool | SQL validation and restricted database access |
| SQL Server | Database-level permissions |
| Secure View | Controlled telemetry exposure |
| Pinecone | SOP retrieval |
| Open-Meteo | Weather retrieval |
| `.env` | Local secret configuration |
| `.gitignore` | Prevent sensitive files from source control |
| AgentAuditLog | Operational traceability |

---

# 33. Security Design Principles

The project follows these principles:

## Least Privilege

Give the application only the database permissions it requires.

## Defense in Depth

Use both database-level and application-level controls.

## Separation of Data

Keep telemetry, weather, and SOP data logically separate.

## Controlled Tool Access

Expose system capabilities through specific tools rather than unrestricted access.

## Credential Protection

Keep passwords and API keys outside source code.

## Auditability

Maintain infrastructure for operational traceability.

## Fail Safely

When a tool fails, do not invent missing operational information.

---

# 34. Security Summary

The Cold-Chain Logistics AI project implements a layered security approach.

The core security architecture is:

```text
                    AI Assistant
                         |
                         v
                 LangGraph Workflow
                         |
                         v
                  Controlled Tools
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
     SQL Server       Open-Meteo      Pinecone
          |
          v
    Secure View
          |
          v
     Raw Database
```

The database security boundary is:

```text
USR_FDE_RO
    |
    +---- SELECT ----> FDE_VIEWS.VW_ACTIVE_FLEET
    |
    +---- SELECT ----> FDE_VIEWS.AgentAuditLog
    |
    +---- NO SELECT -> dbo.TBL_SC_FLEET_HIST_RAW
```

The application adds an additional SQL validation layer to prevent unauthorized operations and direct raw-table queries.

Together, these controls provide a controlled foundation for the AI-powered cold-chain logistics workflow.

---

# 35. Security Status

Current implemented security controls include:

- [x] Dedicated application database user
- [x] Secure telemetry view
- [x] Raw-table SELECT restriction
- [x] Audit table access
- [x] SQL SELECT-only validation
- [x] Destructive SQL operation blocking
- [x] Raw-table query blocking
- [x] SQL Server `TOP` enforcement
- [x] Maximum telemetry result limit
- [x] Environment-based credentials
- [x] `.env` excluded from Git
- [x] `.env.example` provided
- [x] Database permission verification
- [x] Tool-level separation
- [x] Telemetry/weather data separation

---

## Conclusion

Security in the Cold-Chain Logistics AI project is implemented through a combination of database permissions, secure views, application-level SQL validation, controlled AI tools, credential separation, and audit infrastructure.

The design follows a least-privilege and defense-in-depth approach while keeping the AI assistant focused on its intended operational role.