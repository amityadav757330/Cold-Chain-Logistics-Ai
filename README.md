# Cold-Chain Logistics AI

An AI-powered operational assistant for monitoring cold-chain fleet telemetry, identifying logistics risks, checking corridor weather conditions, and recommending actions based on defined cold-chain SOP rules.

The system is designed for logistics dispatchers who need a single interface to understand fleet conditions and respond to operational risks quickly.

---

## 1. Project Overview

Cold-chain logistics requires continuous monitoring of temperature-sensitive shipments while vehicles are in transit.

A dispatcher may need to simultaneously evaluate:

- Vehicle telemetry
- Cargo temperature
- Delay probability
- Port congestion
- Route risk
- Risk classification
- Weather conditions
- Cold-chain compliance procedures

The **Cold-Chain Logistics AI Assistant** combines these sources into an AI-assisted operational workflow.

The application uses:

- **Streamlit** for the dispatcher interface
- **LangGraph** for AI workflow orchestration
- **SQL Server** for fleet telemetry
- **Open-Meteo** for weather information
- **Pinecone** for SOP retrieval
- **Ollama** for local LLM inference

---

## 2. Problem Statement

Cold-chain transportation involves operational risks that can affect product quality and delivery reliability.

Examples include:

- Temperature exceeding the safe threshold
- Increasing delivery delay probability
- High port congestion
- High-risk shipments
- Unsafe route conditions
- Weather-related corridor disruption

Traditionally, a dispatcher may need to inspect multiple systems and manually interpret operational rules.

This project provides an AI-assisted interface where a dispatcher can ask questions using natural language and receive an operational assessment based on telemetry, weather information, and documented SOP procedures.

---

## 3. Proposed Solution

The system provides a centralized AI-powered dispatcher assistant.

A natural-language request is processed through the application workflow:

```text
Dispatcher
    |
    v
Streamlit Interface
    |
    v
Intent Parser
    |
    v
LangGraph Orchestrator
    |
    +--------------------+
    |                    |
    v                    v
Telemetry Tool       SOP Search
    |                    |
    v                    v
SQL Server           Pinecone
    |
    v
Weather Tool
    |
    v
Open-Meteo
    |
    v
Operational Assessment
    |
    v
Dispatcher Response
```

The system separates:

- Telemetry information
- Weather information
- SOP/compliance information
- Operational recommendations

---

# 4. Key Features

## Fleet Telemetry Monitoring

The assistant can query the secure fleet telemetry view to identify:

- Current vehicle temperature
- Vehicle location
- Cargo condition
- Risk classification
- Delay probability
- Port congestion
- Route risk

---

## Cold-Chain Breach Detection

The system identifies vehicles where:

```text
Current_Temperature_C > 4.0°C
```

This is treated as an immediate cold-chain temperature breach according to the project SOP rules.

---

## Delay Risk Analysis

The assistant can identify vehicles with elevated delay probability and determine whether emergency cold-storage diversion should be considered.

---

## Port Congestion Monitoring

The system monitors:

```text
Port_Congestion_Level > 7.0
```

When the threshold is exceeded, the SOP requires suspension of standard routing and diversion to the designated Inland Empire Overflow Depot in San Bernardino for cross-docking.

---

## High-Risk Shipment Detection

The system identifies shipments satisfying:

```text
Risk Classification = High Risk
AND
Delay Probability > 0.65
```

These cases require escalation to a Tier 2 Logistics Manager.

---

## Weather Monitoring

The assistant can query current corridor weather conditions using the Open-Meteo API.

The weather tool returns:

- Current temperature
- Wind speed
- Disruption index

Weather data is kept separate from vehicle IoT telemetry.

---

## SOP Retrieval

The project uses Pinecone-based retrieval to search the Cold-Chain Incident SOP.

This allows the assistant to retrieve relevant operational procedures instead of relying only on information embedded in the model prompt.

---

## Natural-Language Dispatcher Interface

Dispatchers do not need to write SQL queries.

Example:

```text
Show me all vehicles with temperature above 4°C and tell me what action is required.
```

The system converts the operational request into the required workflow and retrieves the relevant information.

---

# 5. Cold-Chain Operational Rules

The current operational rules used by the project are:

| Condition | Operational Rule |
|---|---|
| Fresh perishables | Maintain between 0°C and 4°C |
| Telemetry temperature > 4°C | Immediate cold-chain breach |
| ETA delay > 1 hour | Consider diversion to nearest emergency cold-storage facility |
| Port congestion > 7.0 | Suspend standard routing and divert to Inland Empire Overflow Depot, San Bernardino |
| High Risk + delay probability > 0.65 | Escalate to Tier 2 Logistics Manager |

These rules form the basis for the operational recommendations generated by the system.

---

# 6. System Architecture

The project follows a layered architecture.

```text
+------------------------------------------------------+
|                  Dispatcher Interface                |
|                     Streamlit                        |
+---------------------------+--------------------------+
                            |
                            v
+------------------------------------------------------+
|                    Intent Parser                     |
|       Converts natural language into an intent       |
+---------------------------+--------------------------+
                            |
                            v
+------------------------------------------------------+
|                 LangGraph Orchestrator               |
|        Controls the operational AI workflow          |
+-------------+------------------+---------------------+
              |                  |
              v                  v
+----------------------+   +--------------------------+
| Telemetry Tool       |   | SOP Search Tool           |
| SQL Server           |   | Pinecone                 |
+----------+-----------+   +--------------------------+
           |
           v
+----------------------+
| Secure SQL View      |
| FDE_VIEWS            |
+----------+-----------+
           |
           v
+----------------------+
| Fleet Raw Data       |
| SQL Server           |
+----------------------+

              |
              v
+----------------------+
| Weather Tool         |
| Open-Meteo API       |
+----------------------+
```

---

# 7. Main Components

## 7.1 Streamlit UI

The Streamlit application provides the dispatcher-facing interface.

The interface includes:

- Dispatcher Command Center
- KPI cards
- Risk summaries
- Temperature monitoring
- Priority actions
- Executive assessment
- Detailed operational report
- Quick operational queries
- Presentation Mode
- Developer Mode

Main file:

```text
src/ui.py
```

---

## 7.2 Intent Parser

The intent parser identifies the operational purpose of a dispatcher request.

Supported intent categories include:

```text
risk_analysis
temperature_breach
port_congestion
high_risk
delay_risk
route_risk
general
```

Main file:

```text
src/intent_parser.py
```

The intent parser identifies what information the dispatcher is requesting.

It does not independently determine operational safety thresholds.

---

## 7.3 LangGraph Orchestrator

LangGraph controls the AI workflow.

It coordinates:

- User request processing
- Intent identification
- Tool selection
- Telemetry retrieval
- Weather retrieval
- SOP retrieval
- Final operational response

Main file:

```text
src/orchestrator.py
```

---

## 7.4 Telemetry Database Tool

The telemetry tool provides controlled access to the secure SQL Server view.

Main file:

```text
src/agent_tools.py
```

The assistant is designed to query:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

and not directly query:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

---

## 7.5 Weather Tool

The weather integration uses Open-Meteo to retrieve current weather conditions for a vehicle corridor.

The tool returns:

```text
Current temperature
Wind speed
Disruption index
```

The project currently uses a simple disruption classification based on wind speed.

---

## 7.6 SOP Search

The SOP search tool uses Pinecone and Hugging Face embeddings to retrieve relevant compliance procedures.

The current embedding model is:

```text
BAAI/bge-m3
```

The SOP retrieval system helps the assistant ground operational responses in the project's documented cold-chain procedures.

---

# 8. Database Architecture

The project uses Microsoft SQL Server.

Database:

```text
ColdChainLogistics
```

Schema:

```text
FDE_VIEWS
```

The raw telemetry table is:

```text
dbo.TBL_SC_FLEET_HIST_RAW
```

The application accesses the secured view:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

---

# 9. Secure Database Design

The application uses the least-privilege database account:

```text
USR_FDE_RO
```

The application account is intended to access the secure telemetry view rather than the raw telemetry table.

The architecture separates:

```text
Raw telemetry data
        |
        v
Secure database view
        |
        v
AI application
```

The raw table should not be directly accessible by the AI query tool.

The project also includes an audit table:

```text
FDE_VIEWS.AgentAuditLog
```

which supports operational traceability.

---

# 10. SQL Query Protection

The telemetry tool validates SQL queries before execution.

The application restricts queries to:

```text
SELECT
```

and requires:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

The tool blocks operations including:

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

Direct access to:

```text
TBL_SC_FLEET_HIST_RAW
```

is also rejected by the application layer.

The tool automatically limits returned records to a maximum of 10 rows for controlled tool responses.

---

# 11. AI Workflow

A typical dispatcher request follows this sequence:

```text
1. Dispatcher submits natural-language request
                  |
                  v
2. Intent is identified
                  |
                  v
3. LangGraph determines required tools
                  |
                  v
4. Telemetry is retrieved from secure SQL view
                  |
                  v
5. Relevant weather conditions are retrieved
                  |
                  v
6. SOP procedures are retrieved when required
                  |
                  v
7. Operational rules are evaluated
                  |
                  v
8. Final response is generated
                  |
                  v
9. Dispatcher receives operational assessment
```

---

# 12. Local LLM

The project uses Ollama for local LLM inference.

Current model:

```text
qwen2.5:1.5b
```

The model is configured through:

```text
src/llm.py
```

Using a local model allows the application to perform LLM inference locally rather than requiring an external OpenAI API for the primary conversational workflow.

---

# 13. Technology Stack

### Frontend

```text
Streamlit
```

### AI / Orchestration

```text
LangChain
LangGraph
Ollama
```

### Database

```text
Microsoft SQL Server
pyodbc
SQLAlchemy
```

### Retrieval

```text
Pinecone
Hugging Face Embeddings
FAISS
```

### External Data

```text
Open-Meteo API
```

### Programming Language

```text
Python
```

### Data Processing

```text
Pandas
```

---

# 14. Project Structure

```text
cold-chain-logistics-ai/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   ├── cache/
│   ├── policy/
│   ├── raw/
│   └── source/
│
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── testing.md
│
├── scripts/
│   ├── ingest_legacy_data.py
│   ├── ingest_sop_pinecone.py
│   └── setup_security_and_view.sql
│
├── sql/
│   └── setup_database.sql
│
├── src/
│   ├── prompts/
│   │   └── system_prompt.txt
│   │
│   ├── agent_tools.py
│   ├── intent_parser.py
│   ├── llm.py
│   ├── orchestrator.py
│   └── ui.py
│
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 15. Installation

## Step 1 — Clone the repository

```bash
git clone https://github.com/amityadav757330/Cold-Chain-Logistics-Ai.git
```

Move into the project directory:

```bash
cd Cold-Chain-Logistics-Ai
```

---

## Step 2 — Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\activate
```

---

## Step 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

---

# 16. Environment Configuration

Create a local `.env` file.

Example:

```text
FDE_DB_SERVER=localhost
FDE_DB_NAME=ColdChainLogistics
FDE_DB_USER=USR_FDE_RO
FDE_DB_PASSWORD=your_database_password_here

PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=your_pinecone_index_name_here

LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=cold-chain-logistics-ai
```

Do not commit the real `.env` file to GitHub.

The repository includes:

```text
.env.example
```

as a template.

---

# 17. Database Setup

The SQL Server database should contain:

```text
ColdChainLogistics
```

with the required telemetry table, secure view, application user, and audit infrastructure.

The database setup scripts are located in:

```text
sql/
scripts/
```

The secure telemetry view used by the application is:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

The application database user is:

```text
USR_FDE_RO
```

---

# 18. Pinecone Setup

Configure the following environment variables:

```text
PINECONE_API_KEY
PINECONE_INDEX
```

The SOP ingestion script can be found in:

```text
scripts/ingest_sop_pinecone.py
```

The assistant uses the configured Pinecone index for SOP retrieval.

---

# 19. Running the Application

From the project root:

```powershell
.\.venv\Scripts\activate
```

Then:

```powershell
python -m streamlit run src/ui.py
```

Streamlit will start the application locally.

The default application address is:

```text
http://localhost:8501
```

---

# 20. Example Dispatcher Queries

The dispatcher can use natural-language requests such as:

### Temperature Breach

```text
Show me all vehicles with temperature above 4°C and tell me what action is required.
```

### Port Congestion

```text
Show me all vehicles affected by port congestion above 7 and tell me what routing action is required.
```

### Delay Risk

```text
Show me all vehicles with delay risk and tell me which vehicles require diversion to emergency cold storage.
```

### High-Risk Escalation

```text
Show me all High Risk vehicles with delay probability above 0.65 and tell me which vehicles require Tier 2 Logistics Manager escalation.
```

### Weather

```text
Check the current weather conditions for the active fleet and identify vehicles operating in higher disruption conditions.
```

### Combined Operational Assessment

```text
Check the active fleet. Identify all vehicles with:

1. Temperature above 4°C,
2. Port congestion above 7,
3. High Risk classification with delay probability above 0.65.

For each vehicle, provide the telemetry values, applicable SOP rule, and required operational action.

Also check the current weather conditions for the relevant vehicle locations.
```

---

# 21. Testing

The project includes automated tests covering the main application components.

Run the test suite with:

```powershell
pytest -q
```

The current project test suite has been validated with:

```text
9 passed
```

Tests cover areas including:

- Intent parsing
- Operational workflow
- Database tool behavior
- Weather integration behavior
- Security-related tool restrictions
- Application workflow

---

# 22. Security Design

Security is an important part of the project architecture.

The application follows a least-privilege approach.

Key principles include:

### Secure database access

The application uses:

```text
USR_FDE_RO
```

rather than unrestricted database credentials.

### Secure telemetry view

The application is designed around:

```text
FDE_VIEWS.VW_ACTIVE_FLEET
```

rather than direct raw-table access.

### SQL validation

The telemetry tool validates SQL queries before execution.

### Credential protection

Sensitive credentials are stored in:

```text
.env
```

and excluded from Git through:

```text
.gitignore
```

### Auditability

Operational activity can be recorded in:

```text
FDE_VIEWS.AgentAuditLog
```

More detailed security documentation is available in:

```text
docs/security.md
```

---

# 23. Documentation

Project documentation is maintained in the `docs/` directory.

### Architecture

```text
docs/architecture.md
```

Contains:

- System architecture
- Component responsibilities
- Data flow
- AI workflow
- Database architecture
- Security architecture
- Deployment information

### Security

```text
docs/security.md
```

Contains:

- Database security
- Least privilege
- SQL query protection
- Credential handling
- Auditability
- Security design principles

### Testing

```text
docs/testing.md
```

Contains:

- Test strategy
- Test categories
- Test execution
- Validation results

---

# 24. Development Principles

The project follows several design principles.

## Separation of Responsibilities

Different components have clearly defined responsibilities.

```text
UI
 ↓
Intent Parser
 ↓
Orchestrator
 ↓
Tools
 ↓
External Systems
```

---

## Least Privilege

The application should only receive the database permissions required for its operational role.

---

## Tool Grounding

Operational responses should be based on information retrieved from the appropriate tools.

The system should not invent:

- Telemetry values
- Weather values
- Database records
- SOP procedures

---

## Data Separation

Telemetry temperature and weather temperature are treated as separate values.

For example:

```text
Vehicle IoT Temperature
        ≠
Weather Temperature
```

The system should not interpret one as the other.

---

## Controlled SQL Access

The AI should interact with the database through a controlled tool rather than unrestricted database access.

---

# 25. Current Project Status

The project currently includes:

- Streamlit dispatcher interface
- Natural-language intent parsing
- LangGraph orchestration
- SQL Server telemetry integration
- Secure telemetry view
- Database least-privilege user
- SQL query protection
- Open-Meteo weather integration
- Pinecone SOP retrieval
- Local Ollama LLM
- Operational risk rules
- Audit infrastructure
- Automated tests
- Architecture documentation
- Security documentation
- GitHub repository

---

# 26. Future Enhancements

Potential future improvements include:

- Real-time fleet map visualization
- Historical temperature trend analysis
- Automated alerts
- Route optimization
- Predictive ETA analysis
- Advanced weather-risk modelling
- Automated incident creation
- Dispatcher notification system
- More detailed audit dashboards
- Role-based application access
- Production cloud deployment
- Improved evaluation datasets for the AI assistant

---

# 27. Project Repository

GitHub repository:

```text
https://github.com/amityadav757330/Cold-Chain-Logistics-Ai
```

---

# 28. Author

**Amit Yadav**

B.Tech Computer Science Engineering  
GL Bajaj Institute of Technology and Management

Areas of interest:

- Artificial Intelligence
- AI Agents
- SAP / ABAP
- Backend Development
- Databases
- Cloud & Deployment
- Cybersecurity
- Software Engineering

---

# 29. Summary

The **Cold-Chain Logistics AI Assistant** is an AI-assisted operational decision-support system for cold-chain fleet management.

It combines:

```text
Natural Language
      +
LangGraph
      +
SQL Server Telemetry
      +
Weather Data
      +
SOP Retrieval
      +
Local LLM
      |
      v
Operational Assessment
```

The goal is to help logistics dispatchers understand fleet conditions, identify cold-chain and logistics risks, retrieve relevant procedures, and receive structured operational guidance through a single interface.

---