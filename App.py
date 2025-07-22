import streamlit as st
import pandas as pd
import json
import altair as alt

st.set_page_config(page_title="GovGuard AI", layout="wide")
st.title("🛡️ GovGuard AI – Rule-based Fraud Detection")

# Load rules
with open("rules.json") as f:
    rules = json.load(f)

df = pd.DataFrame(rules)
st.subheader("📋 Rule Editor")
edited_df = st.data_editor(df, num_rows="dynamic", key="rules_edit")

if st.button("💾 Save Rules"):
    with open("rules.json", "w") as f:
        json.dump(edited_df.to_dict(orient="records"), f, indent=4)
    st.success("✅ Rules saved!")

# Upload CSV for scoring
st.subheader("📥 Upload Applicant Dataset")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
results_df = None

if uploaded_file:
    uploaded_df = pd.read_csv(uploaded_file)
    uploaded_df.fillna('', inplace=True)

    def score_row(row, rules):
        score = 0
        triggered = []
        for rule in rules:
            if not rule["Enabled"]:
                continue
            desc = rule["Description"]
            if "Duplicate SSN" in desc and row["SSN"] == "123-45-6789":
                score += rule["Score_Weight"]
                triggered.append(desc)
            if "High income" in desc and float(row["Monthly_Income"]) > 50000:
                score += rule["Score_Weight"]
                triggered.append(desc)
            if "Underage" in desc and "Age" in row and int(row["Age"]) < 18:
                score += rule["Score_Weight"]
                triggered.append(desc)
            if "Program mismatch" in desc and row["Program"] == "SNAP" and float(row["Monthly_Income"]) > 2500:
                score += rule["Score_Weight"]
                triggered.append(desc)
        return pd.Series([score, ', '.join(triggered)])

    uploaded_df[["Risk_Score", "Triggered_Rules"]] = uploaded_df.apply(score_row, axis=1, rules=rules)

    def risk_level(score):
        if score >= 9:
            return "High"
        elif score >= 5:
            return "Medium"
        else:
            return "Low"

    uploaded_df["Risk_Level"] = uploaded_df["Risk_Score"].apply(risk_level)
    results_df = uploaded_df
    st.success("✅ Scoring complete!")
    st.dataframe(uploaded_df[["Applicant_ID", "Name", "Risk_Level", "Risk_Score", "Triggered_Rules"]])

# ================================
# 📊 DASHBOARD SECTION
# ================================
if results_df is not None:
    st.header("📈 Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Level Distribution")
        risk_counts = results_df["Risk_Level"].value_counts().reset_index()
        risk_chart = alt.Chart(risk_counts).mark_bar().encode(
            x="index:N",
            y="Risk_Level:Q",
            color="index:N"
        ).properties(height=300)
        st.altair_chart(risk_chart, use_container_width=True)

    with col2:
        st.subheader("Top Triggered Rules")
        all_rules = results_df["Triggered_Rules"].str.split(', ').explode()
        rule_counts = all_rules.value_counts().reset_index().rename(columns={"index": "Rule", "Triggered_Rules": "Count"})
        rule_chart = alt.Chart(rule_counts).mark_bar().encode(
            x="Count:Q",
            y="Rule:N",
            color="Rule:N"
        ).properties(height=300)
        st.altair_chart(rule_chart, use_container_width=True)
