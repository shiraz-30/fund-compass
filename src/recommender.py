# Turns rules.py + embedder.py output into a natural language recommendation via the Anthropic API

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

MODEL_NAME = "claude-sonnet-5"  # good cost balance for this kind of short explanation task

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment automatically


def build_prompt(profile, eligible_categories, fund_matches):
    funds_text = "\n".join(
        f"- {m['fund_id']} | {m['fund_name']} | category: {m['cifsc_category']} | "
        f"risk: {m['risk_rating']} | MER: {m['mer']}%"
        for m in fund_matches
    )

    # f-string fills in the actual profile/fund values below
    # doubled {{ }} around the json example is on purpose, just means "literal brace, not a variable"
    
    return f"""You are helping explain a mutual fund suitability match to a Canadian investor.
Investor profile:
- Age: {profile['age']}
- Risk tolerance: {profile['risk_tolerance']}
- Time horizon: {profile['time_horizon_years']} years
- Investment objective: {profile['investment_objective']}
- Stated goal: "{profile['goal_description']}"

This investor's suitability rules narrowed eligible fund categories to: {', '.join(eligible_categories)}.
Within those categories, the top semantic matches to their stated goal are:
{funds_text}

Pick the single best fund from the list above and explain why it fits this investor.
Respond with ONLY valid JSON, no other text, in exactly this shape:
{{
  "recommended_fund_id": "...",
  "recommended_fund_name": "...",
  "explanation": "2-3 sentences on why this fund fits this specific investor",
  "risk_note": "1 sentence noting the fund's risk/MER in plain language"
}}

This is a synthetic demo dataset, not real financial advice -- keep the explanation
educational in tone, not a real recommendation."""


def call_claude(prompt):
    # the actual api call -- client picks up the key from env, prompt goes in as a single user message
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    # response.content is a list of blocks -- some models include a thinking block
    # before the actual text, so find the text block instead of assuming index [0]
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError("no text block found in response")


def parse_response(raw_text):
    # models occasionally wrap json in ```json fences even when told not to so strip those first
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "could not parse model response as JSON", "raw": raw_text}


def get_recommendation(profile, eligible_categories, fund_matches):
    # single entry point everything else should call: build prompt, send it, parse what comes back
    prompt = build_prompt(profile, eligible_categories, fund_matches)
    raw = call_claude(prompt)
    return parse_response(raw)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.rules import rule_based_recommend
    from src.embedder import semantic_search

    profiles = json.load(open("data/kyc_profiles.json"))
    p = profiles[0]

    rule_result = rule_based_recommend(p)
    matches = semantic_search(p["goal_description"], eligible_categories=rule_result["eligible_categories"])

    # runs the full chain for real: rules -> embeddings -> prompt -> live API call -> parsed json
    result = get_recommendation(p, rule_result["eligible_categories"], matches)
    print(json.dumps(result, indent=2))
