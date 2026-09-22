# 🚚 Cold-Chain Logistics AI Assistant

An enterprise-style AI-powered operational assistant for monitoring cold-chain logistics, analyzing fleet telemetry, evaluating environmental conditions, retrieving compliance procedures, and generating SOP-based operational actions.

The system is designed for logistics dispatchers who need a single interface to understand fleet risk and determine which operational actions require attention.

---

## 🎯 Project Objective

Cold-chain logistics requires continuous monitoring of:

- Vehicle temperature
- Cargo condition
- Delay probability
- Port congestion
- Route risk
- Environmental conditions
- Operational compliance

This project combines structured fleet telemetry, real-time weather information, and cold-chain SOP knowledge into an operational AI workflow.

The assistant provides:

1. Natural-language dispatcher queries
2. Fleet telemetry analysis
3. Weather analysis
4. SOP retrieval
5. Deterministic risk evaluation
6. SOP-based operational actions
7. Operational reporting
8. Enterprise audit and traceability

---

# 🏗️ Architecture

```text
                         Dispatcher
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Streamlit UI       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Intent Parser     │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ LangGraph Workflow  │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ SQL Server  │   │ Open-Meteo  │   │  Pinecone   │
   │ Telemetry   │   │   Weather   │   │    SOP      │
   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Deterministic Risk  │
                  │      Engine         │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Operational Audit   │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Operational Report  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Streamlit Dashboard │
                  └─────────────────────┘