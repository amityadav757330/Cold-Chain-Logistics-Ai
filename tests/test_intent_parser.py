from src.intent_parser import parse_intent


def test_temperature_queries():
    queries = [
        "Which vehicles have temperature breaches?",
        "Show me trucks with temperature issues",
        "Which vehicles are too hot?",
        "Show cold chain temperature problems",
    ]

    for query in queries:
        assert parse_intent(query) == "temperature_breach"


def test_port_congestion_queries():
    queries = [
        "Which vehicles have port congestion?",
        "Show me congested ports",
        "Which trucks are affected by port delays?",
        "Show port risk",
    ]

    for query in queries:
        assert parse_intent(query) == "port_congestion"


def test_high_risk_queries():
    queries = [
        "Show me high risk vehicles",
        "Which trucks are high-risk?",
        "Which vehicles are at risk?",
        "Show shipments at risk",
    ]

    for query in queries:
        assert parse_intent(query) == "high_risk"


def test_delay_queries():
    queries = [
        "Which vehicles are delayed?",
        "Show me trucks with delay risk",
        "Which shipments are late?",
        "Show delivery delays",
    ]

    for query in queries:
        assert parse_intent(query) == "delay_risk"


def test_route_risk_queries():
    queries = [
        "Which routes are risky?",
        "Show route risk",
        "Which vehicles have a risky route?",
        "Show dangerous routes",
    ]

    for query in queries:
        assert parse_intent(query) == "route_risk"


def test_general_risk_analysis_queries():
    queries = [
        "Which trucks need attention right now?",
        "What should the dispatcher do?",
        "What action should we take?",
        "Show operational risks",
        "Check the fleet",
        "Show fleet status",
        "What should I do about the risky vehicles?",
    ]

    for query in queries:
        assert parse_intent(query) == "risk_analysis"


def test_general_queries():
    queries = [
        "Hello",
        "Give me an overview",
        "Tell me something",
        "What is the current situation?",
    ]

    for query in queries:
        assert parse_intent(query) == "general"


def test_case_insensitivity():
    assert (
        parse_intent("WHICH TRUCKS NEED ATTENTION?")
        == "risk_analysis"
    )

    assert (
        parse_intent("SHOW HIGH RISK VEHICLES")
        == "high_risk"
    )

    assert (
        parse_intent("TEMPERATURE BREACHES")
        == "temperature_breach"
    )


def test_priority_of_risk_analysis():
    """
    Operational/action questions should be classified
    as risk_analysis before narrower risk keywords.
    """

    assert (
        parse_intent(
            "What should the dispatcher do about the risky vehicles?"
        )
        == "risk_analysis"
    )

    assert (
        parse_intent(
            "What action should we take for the temperature issues?"
        )
        == "risk_analysis"
    )


if __name__ == "__main__":

    test_temperature_queries()
    test_port_congestion_queries()
    test_high_risk_queries()
    test_delay_queries()
    test_route_risk_queries()
    test_general_risk_analysis_queries()
    test_general_queries()
    test_case_insensitivity()
    test_priority_of_risk_analysis()

    print(
        "All intent parser tests passed successfully."
    )