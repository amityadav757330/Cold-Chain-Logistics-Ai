def parse_intent(user_request: str) -> str:
    """
    Convert a natural-language dispatcher request
    into a controlled operational intent.

    The intent parser identifies what information
    the dispatcher is asking for.

    It does NOT decide safety thresholds or
    operational actions.
    """

    query = user_request.lower().strip()

    # -------------------------------------------------
    # 1. Action / operational analysis
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "need attention",
            "needs attention",
            "what should",
            "what do i do",
            "what should the dispatcher",
            "what action",
            "what actions",
            "what do we do",
            "operational risk",
            "operational risks",
            "risk analysis",
            "check the fleet",
            "check fleet",
            "fleet status",
            "fleet health",
        ]
    ):
        return "risk_analysis"

    # -------------------------------------------------
    # 2. Temperature / cold-chain questions
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "temperature",
            "cold chain",
            "cold-chain",
            "too hot",
            "temperature breach",
            "temperature issue",
            "safe temperature",
        ]
    ):
        return "temperature_breach"

    # -------------------------------------------------
    # 3. Port congestion questions
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "port congestion",
            "port congested",
            "congestion",
            "port delay",
            "port risk",
        ]
    ):
        return "port_congestion"

    # -------------------------------------------------
    # 4. High-risk vehicle questions
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "high risk",
            "high-risk",
            "risky vehicles",
            "risky trucks",
            "vehicles at risk",
            "shipments at risk",
            "at risk",
        ]
    ):
        return "high_risk"

    # -------------------------------------------------
    # 5. Delay questions
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "delay",
            "delayed",
            "late",
            "delivery delay",
        ]
    ):
        return "delay_risk"

    # -------------------------------------------------
    # 6. Route-risk questions
    # -------------------------------------------------
    if any(
        phrase in query
        for phrase in [
            "route risk",
            "route risky",
            "risky route",
            "dangerous route",
        ]
    ):
        return "route_risk"

    # -------------------------------------------------
    # 7. Default
    # -------------------------------------------------
    return "general"