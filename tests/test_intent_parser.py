from src.intent_parser import parse_intent


test_cases = [
    (
        "Which trucks need attention right now?",
        "risk_analysis",
    ),
    (
        "Are any shipments at risk because of congestion?",
        "port_congestion",
    ),
    (
        "Find vehicles that might require escalation.",
        "general",
    ),
    (
        "Check whether the cold chain is being maintained.",
        "temperature_breach",
    ),
    (
        "What should the dispatcher do about the risky vehicles?",
        "risk_analysis",
    ),
    (
        "Show vehicles with high risk.",
        "high_risk",
    ),
    (
        "Are there any delivery delays?",
        "delay_risk",
    ),
    (
        "Check route risk.",
        "route_risk",
    ),
]


for question, expected in test_cases:
    result = parse_intent(question)

    print(f"Question : {question}")
    print(f"Intent   : {result}")
    print(f"Expected : {expected}")
    print("-" * 50)

    assert result == expected


print("All intent parser tests passed.")