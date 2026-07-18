# fundcompass streamlit app; it lets someone enter their own investor profile and get a suitability recommendation via rules.py -> embedder.py -> recommender.py

import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
# these are the only functions the app actually needs to drive the full pipeline end to end
from src.rules import rule_based_recommend
from src.embedder import semantic_search
from src.recommender import get_recommendation

st.set_page_config(page_title="FundCompass", page_icon="assets/fundcompass_icon.png", layout="centered")

col_icon, col_title = st.columns([1, 6])
with col_icon:
    st.image("assets/fundcompass_icon.png", width=70)
with col_title:
    st.title("FundCompass")
st.caption("Mutual fund suitability recommendations for Canadian investors")

st.warning(
    "This is a portfolio project using synthetic fund data and a rule engine modeled on "
    "general CFR suitability principles. It is not real financial advice and has not been "
    "verified against a specific CIRO rulebook citation. Do not use for real investment decisions."
)

# cached so re-submitting the exact same profile doesn't re-hit the api unnecessarily so streamlit reruns the whole script on every interaction
@st.cache_data(show_spinner=False)
def get_cached_recommendation(profile, eligible_categories, fund_matches):
    return get_recommendation(profile, eligible_categories, fund_matches)

# the form has 6 questions in total, nothing submits or reruns until "get my recommendation" is clicked
with st.form("investor_form"):
    st.subheader("Tell us about yourself")

    name = st.text_input("Name (optional)", value="")
    age = st.number_input("Age", min_value=18, max_value=100, value=30)

    risk_tolerance = st.selectbox(
        "Risk tolerance",
        options=["Low", "Low Medium", "Medium", "High", "Aggressive"],
        index=2,
        help="How much fluctuation in value are you comfortable with?",
    )

    time_horizon_years = st.slider(
        "Time horizon (years)",
        min_value=1, max_value=40, value=10,
        help="How many years until you'll need this money?",
    )

    investment_objective = st.selectbox(
        "Investment objective",
        options=["preservation", "income", "growth"],
        index=2,
        format_func=lambda x: {
            "preservation": "Preservation — protect what I have, avoid losing money",
            "income": "Income — generate steady, regular payouts",
            "growth": "Growth — grow my money over time, can handle ups and downs",
        }[x],
    )

    goal_description = st.text_area(
        "In your own words, what are you hoping to achieve?",
        placeholder="e.g. I want steady income with very little risk since I'm close to retirement",
    )

    submitted = st.form_submit_button("Get my recommendation")


if submitted:
    if not goal_description.strip():
        st.error("Please describe your goal so we can find a relevant fund match.")
    else:
        profile = {
            "id": "APP001",
            "name": name.strip() or "Investor",
            "age": age,
            "risk_tolerance": risk_tolerance,
            "time_horizon_years": time_horizon_years,
            "investment_objective": investment_objective,
            "goal_description": goal_description.strip(),
        }

        with st.spinner("Finding your best-fit fund..."):
            rule_result = rule_based_recommend(profile)
            eligible_categories = rule_result["eligible_categories"]

            # no category survived the suitability filter; it is rare, but possible with an unusual combo of inputs, so handle it instead of letting the next line crash
            if not eligible_categories:
                st.error("No fund categories are eligible for this profile under current suitability rules.")
            else:
                matches = semantic_search(goal_description, eligible_categories=eligible_categories)
                result = get_cached_recommendation(profile, eligible_categories, matches)

                # the api came back but parse_response() couldn't turn it into valid json so show a clean message instead of a raw crash, with the raw text tucked away
                if "error" in result:
                    st.error("Couldn't generate a recommendation right now. Please try again.")
                    with st.expander("Details"):
                        st.text(result.get("raw", ""))
                else:
                    # everything worked, show the actual recommendation
                    st.success(f"Recommended: **{result['recommended_fund_name']}**")
                    st.write(result["explanation"])
                    st.info(result["risk_note"])

                    with st.expander("Why these categories were eligible"):
                        st.write(rule_result["reasoning"])
                        st.write(f"Eligible categories: {', '.join(eligible_categories)}")
