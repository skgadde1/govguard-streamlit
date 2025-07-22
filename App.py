import streamlit as st
import json
import pandas as pd
import plotly.express as px
import openai
import os

st.set_page_config(page_title="GovGuard AI", layout="wide")
st.title("🛡️ GovGuard AI – Rule-based Fraud Detection")

# =============================
# Load Rules
# =============================
with open("rules.json") as f:
    rules = json.load(f)

df = pd.DataFrame(rules)

# =============================
# Rule Editor
# =============================
st.subheader("📋 Rule Editor")
edited_df = st.data_editor(df, num_rows="dynamic", key="rules_edit")

if st.button("💾 Save Rules"):
    with open("rules.json", "w") as f:
        json.dump(edited_df.to_dict(orient="records"), f, indent=4)
    st.success("✅ Rules saved!")

# =============================
# Simulated Applicant (single test case)
# =============================
st.subheader("📊 Simulated Applicant")
applicant = {
    "SSN": "123-45-6789",
    "Bank_Account": "9876543210",
    "Income": 100000,
    "Address": "123 Elm St, FL",
    "Age": 17,
    "Program": "SNAP"
}
st.json(applicant)

# =============================
# Upload CSV and Score
# =============================
st.subheader("📥 Upload Applicant Dataset for Scoring")
uploaded_df = None
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    uploaded_df = pd.read_csv(uploaded_file)
    uploaded_df.fillna('', inplace=True)

    def score_row(row, rules):
        score = 0
        triggered = []
        for rule in rules:
            if not rule["Enabled"]:
                continue
            if "Duplicate SSN" in rule["Description"] and row.get("SSN") == "123-45-6789":
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "High income" in rule["Description"] and float(row.get("Monthly_Income", 0)) > 50000:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "Underage" in rule["Description"] and int(row.get("AGE", 0)) < 18:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
            if "Program mismatch" in rule["Description"] and row.get("Program") == "SNAP" and float(row.get("Monthly_Income", 0)) > 2500:
                score += rule["Score_Weight"]
                triggered.append(rule["Description"])
        return pd.Series([score, ', '.join(triggered)])

    uploaded_df[['Risk_Score', 'Triggered_Rules']] = uploaded_df.apply(score_row, axis=1, rules=rules)

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

# =============================
# Dashboard
# =============================
if uploaded_df is not None:
    st.header("📈 Dashboard")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Level Distribution")
        fig = px.histogram(uploaded_df, x="Risk_Level", color="Risk_Level")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Triggered Rules")
        exploded = uploaded_df['Triggered_Rules'].str.split(', ', expand=True).stack()
        rule_counts = exploded.value_counts().reset_index()
        rule_counts.columns = ['Rule', 'Count']
        fig2 = px.bar(rule_counts, x='Rule', y='Count', color='Rule')
        st.plotly_chart(fig2, use_container_width=True)

# =============================
# Chat with OpenAI
# =============================
st.header("💬 Chat with GovGuard AI")
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")
if openai_api_key:
    user_question = st.chat_input("Ask something about your data or rules")
    if user_question:
        if uploaded_df is None:
            st.error("Please upload a dataset first.")
        else:
            context = uploaded_df.head(10).to_string(index=False) + "\n\nRules:\n" + json.dumps(rules, indent=2)
            prompt = f"You are GovGuard AI. Based on the following data and rules, answer the user's question.\n\nData:\n{context}\n\nUser Question: {user_question}"
            try:
                openai.api_key = openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful fraud detection assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                st.write("🧠 GovGuard AI says:")
                st.success(response['choices'][0]['message']['content'])
            except Exception as e:
                st.error(f"API call failed: {e}")
