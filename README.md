# fund-compass

AI-powered mutual fund suitability engine for Canadian investors

## ⚠️ Disclaimer

This is a portfolio/learning project, not a compliance-verified financial tool.

- **KYC profiles** (`data/kyc_profiles.json`) are synthetic — invented for testing, not real investors.
- **Fund data** (`data/funds/fund_descriptions.json`) is synthetic. Fund *family* names (RBC, TD, Mackenzie, Fidelity, etc.) are real Canadian asset managers, but the specific fund names, MERs, benchmarks, and descriptions attached to them are fabricated for this project and do not represent actual current products, pricing, or Fund Facts data.
- **Suitability logic** (`src/rules.py`) is modeled on general IFC (Investment Funds in Canada) course principles and CSA Client Focused Reform concepts (e.g., time horizon capping stated risk tolerance, objective-based filtering). It has **not** been verified against a specific CIRO rulebook citation or audited for regulatory compliance.
- Nothing in this repo should be used to make actual investment or suitability decisions.
