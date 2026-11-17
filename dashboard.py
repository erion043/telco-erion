import os

import requests
import streamlit as st

DEV_API = "http://127.0.0.1:8000/predict"

# The address of your Azure Function is read from the .env file.
# It contains your function key. Never write it in this file.
PROD_API = os.environ.get("PROD_API", "")


def fetch_prediction(payload: dict) -> dict:
    """Call the prediction API and return the JSON response"""
    response = requests.post(DEV_API, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def fetch_prediction_from_production(params: dict) -> requests.Response:
    """Call the production API and return the response.

    Our serverless function doesnt support JSON in or out
    Plus we need to increase the timeout for cold starts.
    """
    if not PROD_API:
        raise RuntimeError("PROD_API is not set. Start with --env-file .env")
    url = PROD_API + "&" + "&".join(f"{k}={v}" for k, v in params.items())
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response


### Streamlit Dashboard for Telco Churn Prediction

HIGH_RISK = 0.5
MEDIUM_RISK = 0.3


def risk_label(probability: float) -> tuple[str, str]:
    """Return a risk label and Streamlit colour for a churn probability."""
    if probability >= HIGH_RISK:
        return "High risk", "red"
    if probability >= MEDIUM_RISK:
        return "Medium risk", "orange"
    return "Low risk", "green"


def copy_value(source: str, target: str) -> None:
    st.session_state[target] = st.session_state[source]


def slider_with_input(label: str, max_value: int, step: int, default: int) -> int:
    """Show a slider and a number box that stay in sync, capped at max_value."""
    slider_key, input_key = f"{label}_slider", f"{label}_input"
    st.session_state.setdefault(slider_key, default)
    st.session_state.setdefault(input_key, default)

    slider_col, input_col = st.columns([3, 2], vertical_alignment="bottom")
    slider_col.slider(
        label,
        min_value=0,
        max_value=max_value,
        step=step,
        key=slider_key,
        on_change=copy_value,
        args=(slider_key, input_key),
    )
    input_col.number_input(
        label,
        min_value=0,
        max_value=max_value,
        step=step,
        key=input_key,
        on_change=copy_value,
        args=(input_key, slider_key),
        label_visibility="collapsed",
    )
    return st.session_state[slider_key]


st.set_page_config(page_title="Telco Churn Predictor", page_icon="📊", layout="wide")

st.title("📊 Telco Churn Predictor")
st.caption("Set the customer details on the left to see how likely they are to churn.")

with st.sidebar:
    st.header("Customer")
    tenure = slider_with_input("Tenure (months)", max_value=120, step=1, default=12)
    monthly = slider_with_input(
        "Monthly charges ($)", max_value=1000, step=5, default=70
    )
    techsupport = st.toggle("Tech support", value=False)

payload = {
    "tenure": tenure,
    "monthly": int(monthly),
    "techsupport": int(techsupport),
}

try:
    with st.spinner("Asking the model..."):
        probability = fetch_prediction(payload)["prediction"]
except requests.RequestException as e:
    st.error(f"Could not reach the API. Is it running?\n\n{e}")
    st.stop()

label, colour = risk_label(probability)

col_prob, col_risk, col_tenure, col_charges = st.columns(4)
col_prob.metric("Churn probability", f"{probability:.0%}")
col_risk.metric("Risk", label)
col_tenure.metric("Tenure", f"{tenure} mths")
col_charges.metric("Monthly charges", f"${monthly}")

st.progress(probability)
st.markdown(f"### :{colour}[{label}]")

with st.expander("Request and response"):
    st.json({"request": payload, "response": {"prediction": probability}})
