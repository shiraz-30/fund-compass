# Suitability rule engine for FundCompass
# Maps KYC profile attributes to eligible CIFSC fund categories
# Based on IFC suitability framework and CSA Client Focused Reforms

CIFSC_CATEGORIES = {
    "money_market": {
        "label": "Money Market",
        "description": "Canadian money market funds investing in short-term government and corporate debt.",
        "risk_level": "low",
        "typical_return": "2-3%",
        "suitable_horizons": [1, 2, 3]
    },
    "canadian_fixed_income": {
        "label": "Canadian Fixed Income",
        "description": "Bond funds focused on Canadian government and investment-grade corporate bonds.",
        "risk_level": "low_medium",
        "typical_return": "3-5%",
        "suitable_horizons": [3, 5, 7]
    },
    "global_fixed_income": {
        "label": "Global Fixed Income",
        "description": "Bond funds with international exposure including sovereign and corporate debt.",
        "risk_level": "medium",
        "typical_return": "4-6%",
        "suitable_horizons": [3, 5, 7]
    },
    "canadian_balanced": {
        "label": "Canadian Balanced",
        "description": "Mix of Canadian equities and bonds, typically 60/40 split.",
        "risk_level": "medium",
        "typical_return": "5-7%",
        "suitable_horizons": [5, 7, 10]
    },
    "global_balanced": {
        "label": "Global Balanced",
        "description": "Mix of global equities and bonds with geographic diversification.",
        "risk_level": "medium",
        "typical_return": "5-8%",
        "suitable_horizons": [5, 7, 10]
    },
    "canadian_equity": {
        "label": "Canadian Equity",
        "description": "Equity funds focused on TSX-listed Canadian companies.",
        "risk_level": "medium_high",
        "typical_return": "7-10%",
        "suitable_horizons": [7, 10, 15]
    },
    "global_equity": {
        "label": "Global Equity",
        "description": "Broadly diversified equity funds with worldwide exposure.",
        "risk_level": "medium_high",
        "typical_return": "7-11%",
        "suitable_horizons": [7, 10, 15]
    },
    "emerging_markets": {
        "label": "Emerging Markets",
        "description": "Equity funds investing in developing economies with higher growth and risk.",
        "risk_level": "high",
        "typical_return": "8-14%",
        "suitable_horizons": [10, 15, 20]
    }
}

# Maps each risk band to eligible fund categories
RISK_ELIGIBLE = {
    "low":        ["money_market", "canadian_fixed_income"],
    "low_medium": ["money_market", "canadian_fixed_income", "global_fixed_income", "canadian_balanced"],
    "medium":     ["canadian_fixed_income", "global_fixed_income", "canadian_balanced", "global_balanced", "canadian_equity"],
    "high":       ["canadian_balanced", "global_balanced", "canadian_equity", "global_equity", "emerging_markets"],
    "aggressive": ["canadian_equity", "global_equity", "emerging_markets"]
}


def get_risk_band(risk_tolerance: str, time_horizon_years: int) -> str:
    # IFC principle: short time horizon constrains max risk regardless of what the investor says they can tolerate
    stated = risk_tolerance.lower()
    if time_horizon_years <= 2:
        return "low"
    if time_horizon_years <= 4:
        return min_risk(stated, "low_medium")
    if time_horizon_years <= 7:
        return min_risk(stated, "medium")
    return stated


def min_risk(a: str, b: str) -> str:
    # returns whichever risk band is more conservative
    order = ["low", "low_medium", "medium", "high", "aggressive"]
    return a if order.index(a) <= order.index(b) else b


def apply_objective_filter(categories: list, objective: str) -> list:
    # further narrows eligible categories based on investment objective
    if objective == "preservation":
        return [c for c in categories if CIFSC_CATEGORIES[c]["risk_level"] in ["low"]]
    if objective == "income":
        return [c for c in categories if CIFSC_CATEGORIES[c]["risk_level"] in ["low", "low_medium"]]
    return categories


def rule_based_recommend(profile: dict) -> dict:
    risk_band = get_risk_band(profile["risk_tolerance"], profile["time_horizon_years"])
    eligible = RISK_ELIGIBLE.get(risk_band, [])
    eligible = apply_objective_filter(eligible, profile["investment_objective"])

    reasoning = (
        f"Stated risk tolerance is '{profile['risk_tolerance']}' with a "
        f"{profile['time_horizon_years']}-year horizon — effective risk band: '{risk_band}'. "
        f"After filtering for objective '{profile['investment_objective']}', "
        f"{len(eligible)} CIFSC categories are eligible."
    )

    return {
        "investor_id": profile["id"],
        "investor_name": profile["name"],
        "effective_risk_band": risk_band,
        "eligible_categories": eligible,
        "reasoning": reasoning
    }


if __name__ == "__main__":
    import json

    with open("data/kyc_profiles.json") as f:
        profiles = json.load(f)

    for p in profiles:
        result = rule_based_recommend(p)
        print(f"\n{result['investor_name']} (ID: {result['investor_id']})")
        print(f"  Risk band : {result['effective_risk_band']}")
        print(f"  Eligible  : {result['eligible_categories']}")
        print(f"  Reasoning : {result['reasoning']}")

