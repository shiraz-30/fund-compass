# FundCompass

AI-powered mutual fund suitability engine for Canadian investors — matches investors to Canadian mutual funds based on their risk profile, time horizon, investment objective, and their own stated goals, then explains the recommendation in plain language.

**🔗 Live app: [fund-compass.streamlit.app](https://fund-compass.streamlit.app)**

## How it works

**1. Suitability rules** (`src/rules.py`)
Applies logic modeled on CSA Client Focused Reform (CFR) principles — the same kind of reasoning a real advisor uses to narrow down appropriate fund categories. A short time horizon or a conservative investment objective will limit risk even if an investor says they're comfortable with more, since capacity to absorb losses matters as much as stated preference.

**2. Semantic search** (`src/embedder.py`)
Within whatever categories the rules allow, this layer ranks funds by how closely their descriptions match what the investor actually said in their own words — not just their risk score. It uses sentence-transformer embeddings and a ChromaDB vector index over a 32-fund catalogue, so a goal like "steady income with very little risk" surfaces genuinely relevant funds rather than a generic category default.

**3. Recommendation generation** (`src/recommender.py`)
Takes the investor's profile and the top-ranked fund matches and sends them to the Anthropic API, which picks the single best-fit fund, explains why in plain language specific to that investor, and surfaces 2 reasonable alternatives with their own brief reasoning — so the output reads like guidance, not a database lookup.

**4. Interface** (`app.py`)
A Streamlit app where an investor fills in a short form (age, risk tolerance, time horizon, objective, and a sentence about their goals) and sees the recommendation, alternatives, and eligible categories in a styled result.

## Built with

Python, Streamlit, sentence-transformer embeddings, ChromaDB, Anthropic API

## Running it locally
```bash

git clone https://github.com/shiraz-30/fund-compass.git
cd fund-compass
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You'll need your own Anthropic API key to run this locally — the deployed version already has one configured, but a fresh clone doesn't come with one built in (for security, API keys are never stored in the code itself). Add your key to a new `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Then run:
```bash
streamlit run app.py
```

## ⚠️ Disclaimer

This is a portfolio/learning project, not a compliance-verified financial tool.

- **KYC profiles** (`data/kyc_profiles.json`) are synthetic — invented for testing, not real investors.
- **Fund data** (`data/funds/fund_descriptions.json`) is synthetic. Fund *family* names (RBC, TD, Mackenzie, Fidelity, etc.) are real Canadian asset managers, but the specific fund names, MERs, benchmarks, and descriptions attached to them are fabricated for this project and do not represent actual current products, pricing, or Fund Facts data.
- **Suitability logic** (`src/rules.py`) is modeled on general CSA Client Focused Reform concepts (e.g., time horizon capping stated risk tolerance, objective-based filtering). It has **not** been verified against a specific CIRO rulebook citation or audited for regulatory compliance.
- Nothing in this repo should be used to make actual investment or suitability decisions.

