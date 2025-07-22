import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="GovGuard AI", layout="wide")

st.title("🛡️ GovGuard AI – Rule-based Fraud Detection")

# Load rules
with open("rules.json") as f:
    rules = json.load(f)

df = pd.DataFrame(rules)

# Show rule editor
st.subheader("📋 Rule Editor")
edited_df = st.data_editor(df, num_rows="dynamic", key="rules_edit")

# Save back
if st.button("💾 Save Rules"):
    with open("rules.json", "w") as f:
        json.dump(edited_df.to_dict(orient="records"), f, indent=4)
    st.success("✅ Rules saved!")

# Dummy applicant data for scoring
st.subheader("📊 Simulated Applicant")
applicant = {
    "SSN": "123-45-6789",
    "Bank_Account": "9876543210",
    "Income": 100000,
    "Address": "123 Elm St, FL",
    "Age": 17,
    "Program": "SNAP"
}

# =============================
# 📤 CSV Upload and Bulk Scoring
# =============================
st.subheader("📥 Upload Applicant Dataset for Scoring")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    uploaded_df = pd.read_csv(uploaded_file)
    uploaded_df.fillna('', inplace=True)

    # Apply the same rule logic to each row
    def score_row(row, rules):
        score = 0
        triggered = []
        for rule in rules:
            if not rule["Enabled"]:
                continue
            if "Duplicate SSN" in rule["Description"] and row["SSN"] == "123-45-6789":
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "High income" in rule["Description"] and float(row["Monthly_Income"]) > 50000:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "Underage" in rule["Description"] and int(row["Age"]) < 18:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "Program mismatch" in rule["Description"] and row["Program"] == "SNAP" and float(row["Monthly_Income"]) > 2500:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
        return pd.Series([score, ', '.join(triggered)])

    uploaded_df[['Risk_Score', 'Triggered_Rules']] = uploaded_df.apply(score_row, axis=1, rules=rules)

    # Assign risk level
    def risk_level(score):
        if score >= 9:
            return "High"
        elif score >= 5:
            return "Medium"
        else:
            return "Low"

    uploaded_df['Risk_Level'] = uploaded_df['Risk_Score'].apply(risk_level)

    st.success("✅ Scoring complete!")
    st.dataframe(uploaded_df[['Applicant_ID', 'Name', 'Risk_Level', 'Risk_Score', 'Triggered_Rules']])

st.json(applicant)

# Score calculation
def apply_rules(applicant, rules):
    score = 0
    triggered = []
    for rule in rules:
        if not rule["Enabled"]:
            continue
        if "Duplicate SSN" in rule["Description"] and applicant["SSN"] == "123-45-6789":
            score += rule["Score_Weight"]
            triggered.append(rule["Description"])
        if "High income" in rule["Description"] and applicant["Income"] > 50000:
            score += rule["Score_Weight"]
            triggered.append(rule["Description"])
        if "Underage" in rule["Description"] and applicant["Age"] < 18:
            score += rule["Score_Weight"]
            triggered.append(rule["Description"])
        if "Program mismatch" in rule["Description"] and applicant["Program"] == "SNAP" and applicant["Income"] > 2500:
            score += rule["Score_Weight"]
            triggered.append(rule["Description"])
    return score, triggered

if st.button("🧮 Run Risk Scoring"):
    score, details = apply_rules(applicant, rules)
    st.metric("Fraud Risk Score", score)
    st.write("Triggered Rules:")
    st.write(details)
