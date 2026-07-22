# fundcompass streamlit app; it lets someone enter their own investor profile and get a suitability recommendation via rules.py -> embedder.py -> recommender.py

import sys
import os
import base64

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
# these are the only functions the app actually needs to drive the full pipeline end to end
from src.rules import rule_based_recommend
from src.embedder import semantic_search
from src.recommender import get_recommendation

st.set_page_config(page_title="FundCompass", page_icon="assets/fundcompass_icon.png", layout="centered")

def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

        :root {
            --navy: #0B1B33;
            --paper: #F6F7F5;
            --green: #1E7F5C;
            --brass: #B08D57;
            --slate: #64748B;
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: var(--paper); }

        h1, h2, h3 { font-family: 'Fraunces', serif; color: var(--navy); }
        .fc-header { display: flex; align-items: center; gap: 14px; margin-bottom: 2px; }
        .fc-header img { height: 2.3em; }
        .fc-header h1 { margin: 0; font-size: 2.1rem; font-weight: 600; line-height: 1; }
        .fc-tagline { color: var(--slate); font-size: 0.95rem; margin: 4px 0 22px 0; }

        /* form container */
        div[data-testid="stForm"] {
            background: white;
            border: 1px solid rgba(11,27,51,0.08);
            border-radius: 12px;
            padding: 28px 28px 12px 28px;
            box-shadow: 0 1px 3px rgba(11,27,51,0.05);
        }
        div[data-testid="stForm"] h3 {
            font-size: 1.15rem;
            margin-bottom: 18px;
        }

        /* inputs */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea {
            border-radius: 8px !important;
            border: 1px solid rgba(11,27,51,0.15) !important;
        }
        div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid rgba(11,27,51,0.15) !important;
        }

        /* submit button */
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stFormSubmitButton"] button p {
            color: white !important;
        }
        div[data-testid="stFormSubmitButton"] button {
            background: var(--navy) !important;
            border-radius: 8px;
            border: none !important;
            padding: 0.6rem 1.4rem;
            font-weight: 500;
            transition: background 0.15s ease, transform 0.1s ease;
        }
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:focus {
            background: var(--green) !important;
            color: white !important;
            transform: translateY(-1px);
        }

        /* compliance notice, quiet not alarming */
        .fc-notice {
            border-left: 3px solid var(--slate);
            background: rgba(100,116,139,0.06);
            padding: 10px 14px;
            font-size: 0.82rem;
            color: var(--slate);
            border-radius: 4px;
            margin-bottom: 28px;
        }

        /* input hover + focus feedback */
        div[data-testid="stTextInput"] input:hover,
        div[data-testid="stNumberInput"] input:hover,
        div[data-testid="stTextArea"] textarea:hover,
        div[data-baseweb="select"]:hover > div {
            border-color: var(--green) !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            outline: none !important;
            border-color: var(--green) !important;
            box-shadow: 0 0 0 2px rgba(30,127,92,0.15) !important;
        }

        /* pointer cursor for click-to-select controls, not text fields */
        div[data-baseweb="select"],
        div[data-baseweb="select"] * {
            cursor: pointer !important;
        }
        div[data-testid="stSlider"] * {
            cursor: pointer !important;
        }
        div[data-testid="stTooltipIcon"] {
            cursor: pointer !important;
        }

        /* recommendation card */
        .fc-card {
            background: white;
            border: 1px solid rgba(11,27,51,0.08);
            border-radius: 12px;
            padding: 28px 30px;
            margin-top: 24px;
            box-shadow: 0 1px 3px rgba(11,27,51,0.05);
            animation: fc-fade-in 0.4s ease;
        }
        @keyframes fc-fade-in {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fc-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            color: var(--green);
            font-weight: 600;
            margin-bottom: 6px;
        }
        .fc-fund-name {
            font-family: 'Fraunces', serif;
            font-size: 1.6rem;
            font-weight: 600;
            color: var(--navy);
            margin-bottom: 14px;
        }
        .fc-explanation {
            color: #333;
            line-height: 1.55;
            margin-bottom: 18px;
        }
        .fc-risk-note {
            border-left: 3px solid var(--brass);
            background: rgba(176,141,87,0.07);
            padding: 12px 16px;
            font-size: 0.9rem;
            color: var(--navy);
            border-radius: 4px;
            margin-bottom: 14px;
        }
        .fc-stat-row {
            display: flex; gap: 22px; margin-top: 18px; flex-wrap: wrap;
        }
        .fc-stat-label {
            font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em;
            color: var(--slate); display: block; font-family: 'IBM Plex Mono', monospace;
        }
        .fc-stat-value {
            font-size: 1rem; color: var(--navy); font-weight: 500; font-family: 'IBM Plex Mono', monospace;
        }
        .fc-pill {
            display: inline-block;
            background: rgba(30,127,92,0.08);
            color: var(--green);
            border-radius: 20px;
            padding: 3px 12px;
            font-size: 0.78rem;
            margin: 3px 4px 3px 0;
            font-family: 'IBM Plex Mono', monospace;
        }

        .fc-alt-section {
            margin-top: 20px;
        }
        .fc-alt-item {
            border: 1px solid rgba(11,27,51,0.08);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            background: rgba(11,27,51,0.02);
        }
        .fc-alt-name {
            font-family: 'Fraunces', serif;
            font-weight: 600;
            color: var(--navy);
            font-size: 1.1rem;
        }
        .fc-alt-reason {
            color: var(--slate);
            font-size: 0.85rem;
            margin-top: 2px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

def _icon_base64():
    with open(os.path.join(os.path.dirname(__file__), "assets", "fundcompass_icon.png"), "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_result(result, rule_result, eligible_categories):
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="fc-eyebrow">Recommended Fund</div>
            <div class="fc-fund-name">{result['recommended_fund_name']}</div>
            <div class="fc-explanation">{result['explanation']}</div>
            <div class="fc-risk-note">{result['risk_note']}</div>
            <div class="fc-stat-row">
                <div><span class="fc-stat-label">Fund ID</span><span class="fc-stat-value">{result['recommended_fund_id']}</span></div>
                <div><span class="fc-stat-label">Effective Risk Band</span><span class="fc-stat-value">{rule_result['effective_risk_band'].replace('_', ' ').title()}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        alternatives = result.get("alternatives", [])
        if alternatives:
            st.markdown('<div class="fc-eyebrow" style="margin-top:20px;">Other Reasonable Options</div>', unsafe_allow_html=True)
            for alt in alternatives:
                with st.expander(alt["fund_name"]):
                    st.write(alt.get("explanation", ""))
                    if alt.get("risk_note"):
                        st.markdown(f'<div class="fc-risk-note">{alt["risk_note"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="fc-eyebrow" style="margin-top:18px;">Eligible Categories</div>', unsafe_allow_html=True)
    pills = "".join(f'<span class="fc-pill">{c.replace("_", " ")}</span>' for c in eligible_categories)
    st.markdown(pills, unsafe_allow_html=True)
    with st.expander("Why these categories were eligible"):
        st.write(rule_result["reasoning"])
inject_css()


st.markdown(
    f"""
    <div class="fc-header">
        <img src="data:image/png;base64,{_icon_base64()}">
        <h1>FundCompass</h1>
    </div>
    <div class="fc-tagline">Suitability-driven mutual fund guidance for Canadian investors</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="fc-notice">
        Portfolio project using synthetic fund data and a rule engine modeled on general CFR
        suitability principles. Not real financial advice; not verified against a specific
        CIRO rulebook citation. Do not use for real investment decisions.
    </div>
    """,
    unsafe_allow_html=True,
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
        options=["low", "low_medium", "medium", "high", "aggressive"],
        index=2,
        format_func=lambda x: x.replace("_", " ").title(),
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

result_area = st.empty()

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

        result_area.empty()
        with st.spinner("Finding your best-fit fund..."):
            rule_result = rule_based_recommend(profile)
            eligible_categories = rule_result["eligible_categories"]

            # no category survived the suitability filter; it is rare, but possible with an unusual combo of inputs, so handle it instead of letting the next line crash
            with result_area.container():
                if not eligible_categories:
                    st.error("No fund categories are eligible for this profile under current suitability rules.")
                else:
                    matches = semantic_search(goal_description, eligible_categories=eligible_categories)
                    result = get_cached_recommendation(profile, eligible_categories, matches)

                    if "error" in result:
                        st.error("Couldn't generate a recommendation right now. Please try again.")
                        with st.expander("Details"):
                            st.text(result.get("raw", ""))
                    else:
                        render_result(result, rule_result, eligible_categories)
