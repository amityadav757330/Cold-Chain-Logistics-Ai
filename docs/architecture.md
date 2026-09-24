# Cold-Chain Logistics AI --- System Architecture

## 1. System Overview

Cold-Chain Logistics AI is an AI-assisted dispatcher platform for
monitoring fleet telemetry, environmental conditions, operational risk,
and cold-chain compliance.

The system accepts natural-language dispatcher requests through a
Streamlit interface and coordinates several data and knowledge sources
through a LangGraph workflow.

### Core flow

``` mermaid
flowchart TD
    A["Dispatcher<br/>Natural-language request"] --> B["Streamlit UI<br/>Dispatcher Command Center"]
    B --> C["Intent Parser<br/>Controlled operational intent"]
    C --> D["LangGraph Orchestrator"]

    D --> E["SQL Server<br/>FDE_VIEWS.VW_ACTIVE_FLEET"]
    D --> F["Open-Meteo<br/>Corridor weather"]
    D --> G["Pinecone<br/>Cold-Chain Incident SOP"]

    E --> H["Risk & Rule Analysis"]
    F --> H
    G --> H

    H --> I["Operational Action Plan"]
    I --> B

    D --> J["Audit / Traceability"]
    J --> K["FDE_VIEWS.AgentAuditLog"]
```

------------------------------------------------------------------------

## 2. Architecture Layers

### Layer 1 --- Dispatcher Interface

**Technology:** Streamlit

The dispatcher interacts with the system through a web-based command
center.

The interface provides:

-   Natural-language query input
-   Quick operational queries
-   Fleet KPIs
-   Risk and temperature visualizations
-   Operational assessment
-   Priority actions
-   Detailed operational report
-   Audit and traceability information

The dispatcher does not need to write SQL or know the underlying
database structure.

------------------------------------------------------------------------

### Layer 2 --- Intent Parsing

**File:** `src/intent_parser.py`

The intent parser converts natural-language requests into controlled
operational intents.

Current intent categories include:

-   `temperature_breach`
-   `port_congestion`
-   `high_risk`
-   `delay_risk`
-   `route_risk`
-   `risk_analysis`
-   `general`

The parser is responsible for identifying what the dispatcher is asking
for.

It does **not** independently decide operational thresholds or actions.

------------------------------------------------------------------------

### Layer 3 --- LangGraph Orchestration

**File:** `src/orchestrator.py`

LangGraph coordinates the operational workflow.

The orchestrator:

1.  Receives the dispatcher request.
2.  Uses the operational intent.
3.  Coordinates the required tools.
4.  Collects telemetry, weather, and SOP information.
5.  Produces an operational assessment.
6.  Produces required actions.
7.  Records audit information.

This layer acts as the central control flow for the AI assistant.

------------------------------------------------------------------------

## 3. Data and Knowledge Sources

### 3.1 SQL Server Fleet Telemetry

The fleet telemetry is stored in SQL Server.

The application uses the secure view:

``` text
FDE_VIEWS.VW_ACTIVE_FLEET
```

The view exposes operational fields including:

``` text
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

The raw source table is:

``` text
dbo.TBL_SC_FLEET_HIST_RAW
```

However, the AI application's database user is intentionally restricted
from directly accessing the raw table.

------------------------------------------------------------------------

### 3.2 Weather Intelligence

**Tool:** `fetch_corridor_conditions`

The application uses Open-Meteo to retrieve current environmental
conditions for relevant fleet coordinates.

The weather tool returns:

-   Current temperature
-   Wind speed
-   Disruption index

Telemetry temperature and weather temperature are treated as separate
measurements.

``` text
Vehicle IoT temperature
        ≠
Weather temperature
```

This separation prevents the system from incorrectly treating
environmental temperature as cargo temperature.

------------------------------------------------------------------------

### 3.3 Cold-Chain SOP Knowledge

**Tool:** `search_compliance_sop`

Cold-chain compliance procedures are stored in the SOP knowledge base
and retrieved through Pinecone.

The knowledge retrieval layer provides the operational procedures used
to support mitigation and escalation decisions.

------------------------------------------------------------------------

## 4. Operational Rules

The current system uses the following cold-chain rules.

### Temperature breach

``` text
Current_Temperature_C > 4.0°C
```

Action:

``` text
Contact the driver and restart the auxiliary cooling unit.
```

------------------------------------------------------------------------

### Delay risk

An ETA delay greater than one hour requires consideration of diversion
to the nearest emergency cold-storage facility.

------------------------------------------------------------------------

### Port congestion

``` text
Port_Congestion_Level > 7.0
```

Action:

``` text
Suspend standard routing and divert to the
Inland Empire Overflow Depot in San Bernardino
for cross-docking.
```

------------------------------------------------------------------------

### High-risk escalation

``` text
Risk_Classification = High Risk
AND
Delay_Probability > 0.65
```

Action:

``` text
Escalate to a Tier 2 Logistics Manager.
```

------------------------------------------------------------------------

## 5. Secure Database Architecture

Database security is a core part of the system.

### Least-privilege access

The application connects using:

``` text
USR_FDE_RO
```

The intended access model is:

``` mermaid
flowchart LR
    A["AI Application"] --> B["USR_FDE_RO"]
    B --> C["FDE_VIEWS.VW_ACTIVE_FLEET"]
    B --> D["FDE_VIEWS.AgentAuditLog"]

    B -. "DENIED" .-> E["dbo.TBL_SC_FLEET_HIST_RAW"]
    B -. "DENIED" .-> F["Other dbo DML / ALTER operations"]
```

The permission model was verified with SQL Server impersonation tests.

Expected security behavior:

  Resource                         Application User
  -------------------------------- --------------------------------
  `FDE_VIEWS.VW_ACTIVE_FLEET`      SELECT
  `FDE_VIEWS.AgentAuditLog`        SELECT / required audit access
  `dbo.TBL_SC_FLEET_HIST_RAW`      No SELECT
  Raw `dbo` DML/ALTER operations   Denied

------------------------------------------------------------------------

## 6. SQL Query Protection

**File:** `src/agent_tools.py`

The telemetry tool performs application-level validation before
executing a query.

The current controls include:

-   Only `SELECT` queries are accepted.
-   Queries must reference `FDE_VIEWS.VW_ACTIVE_FLEET`.
-   Direct raw-table access is rejected.
-   Write and schema-changing operations are rejected.
-   SQL Server `TOP` is used instead of `LIMIT`.
-   Results are limited to a maximum of 10 rows.

This provides a second protection layer in addition to SQL Server
permissions.

``` text
Dispatcher request
        ↓
Generated SQL
        ↓
Application validation
        ↓
SQL Server permissions
        ↓
Secure telemetry view
```

------------------------------------------------------------------------

## 7. Audit and Traceability

The system records operational execution information in:

``` text
FDE_VIEWS.AgentAuditLog
```

Audit information supports traceability of:

-   User request
-   Operational intent
-   Tool execution
-   Result information
-   Session information
-   Operational outcome

This is important because the system is intended to support operational
decisions rather than operate as an untraceable chatbot.

------------------------------------------------------------------------

## 8. Example End-to-End Request

A dispatcher can enter:

``` text
Check the active fleet. Identify all vehicles with:
1. Temperature above 4°C,
2. Port congestion above 7,
3. High Risk classification with delay probability above 0.65.

For each vehicle, provide the telemetry values, applicable SOP rule,
and required operational action.

Also check the current weather conditions for the relevant vehicle locations.
```

The processing flow is:

``` mermaid
sequenceDiagram
    participant U as Dispatcher
    participant UI as Streamlit UI
    participant P as Intent Parser
    participant G as LangGraph
    participant SQL as SQL Server
    participant W as Open-Meteo
    participant SOP as Pinecone SOP
    participant A as Audit Log

    U->>UI: Natural-language request
    UI->>P: Parse request
    P->>G: Controlled intent
    G->>SQL: Query secure fleet view
    SQL-->>G: Telemetry results
    G->>W: Request corridor weather
    W-->>G: Weather conditions
    G->>SOP: Retrieve relevant procedures
    SOP-->>G: SOP evidence
    G->>G: Apply operational rules
    G->>A: Record execution / trace
    G-->>UI: Assessment + actions
    UI-->>U: Operational dashboard
```

------------------------------------------------------------------------

## 9. Separation of Responsibilities

The architecture deliberately separates different responsibilities.

  Component                    Responsibility
  ---------------------------- ------------------------------------
  Streamlit                    User interaction and visualization
  Intent Parser                Identify dispatcher intent
  LangGraph                    Workflow orchestration
  SQL Server                   Fleet telemetry
  Secure SQL View              Controlled database exposure
  Open-Meteo                   Current environmental conditions
  Pinecone                     SOP knowledge retrieval
  Rule layer / orchestration   Operational risk evaluation
  Audit Log                    Traceability

This separation makes the system easier to test, explain, and maintain.

------------------------------------------------------------------------

## 10. Local Deployment Architecture

The current development setup runs locally.

``` mermaid
flowchart TD
    A["Windows Development Machine"] --> B["Python Virtual Environment"]
    B --> C["Streamlit Application"]
    C --> D["LangGraph / LangChain"]
    D --> E["SQL Server"]
    D --> F["Open-Meteo API"]
    D --> G["Pinecone"]
```

The project is currently run with:

``` powershell
.\.venv\Scripts\activate
python -m streamlit run src/ui.py
```

Docker was explored during development but is not required for the
current local deployment.

------------------------------------------------------------------------

## 11. Project Structure

``` text
cold-chain-logistics-ai/
│
├── data/
│   ├── cache/
│   ├── policy/
│   ├── raw/
│   └── source/
│
├── docs/
│
├── scripts/
│
├── sql/
│
├── src/
│   ├── agent_tools.py
│   ├── intent_parser.py
│   ├── llm.py
│   ├── orchestrator.py
│   ├── ui.py
│   └── prompts/
│       └── system_prompt.txt
│
├── tests/
│
├── .env.example
├── .gitignore
└── requirements.txt
```

------------------------------------------------------------------------

## 12. Design Principles

The system follows these main design principles:

### Natural-language operation

Dispatchers communicate using normal operational language rather than
SQL commands.

### Least privilege

The application receives only the database permissions required for its
job.

### Controlled data access

Fleet telemetry is exposed through a secure database view rather than
direct raw-table access.

### Evidence-based action

Operational recommendations are based on telemetry, weather results, and
SOP information returned by the system.

### Separation of measurements

Vehicle telemetry temperature is kept distinct from environmental
weather temperature.

### Auditability

Operational executions are recorded so that decisions can be traced.

### Modular architecture

The UI, intent parser, orchestration layer, database tools, weather
integration, and SOP retrieval are separated into different components.

------------------------------------------------------------------------

## 13. Testing Status

The current project test suite has been executed successfully after the
final UI changes.

Current result:

``` text
9 passed
```

The UI changes were committed to the `main` branch after verification.

------------------------------------------------------------------------

## 14. Architecture Summary

The project can be summarized as:

``` text
Natural Language Dispatcher
            ↓
      Streamlit UI
            ↓
       Intent Parser
            ↓
    LangGraph Orchestrator
            ↓
 ┌──────────┼──────────┐
 ↓          ↓          ↓
SQL       Weather     SOP
Server    API        Search
 ↓          ↓          ↓
 └──────────┼──────────┘
            ↓
       Risk Analysis
            ↓
      SOP-Based Action
            ↓
 ┌──────────┴──────────┐
 ↓                     ↓
Dispatcher         Audit Log
```

The key architectural idea is that the AI assistant is not simply
generating text. It coordinates **structured operational data, external
environmental information, and compliance knowledge** before producing a
dispatcher-facing action plan.
