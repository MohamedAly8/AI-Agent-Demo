import os
import streamlit as st
import requests
import json
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.utilities import RequestsWrapper
from langchain_community.callbacks import StreamlitCallbackHandler


API_URL = os.getenv("API_URL", "http://localhost:8000")
OPENAPI_SPEC_URL = f"{API_URL}/openapi.json"

st.set_page_config(page_title="Enterprise AI Agent", layout="wide")
st.title("VaultCRM Service Center Agent")

with st.sidebar:
    st.markdown("### Agent Capabilities")
    st.markdown("""
    - **User Profiles**: Tier, Churn Risk
    - **Order History**: Dates, Prices
    - **Case History**: Past incidents, Sentiment
    - **Knowledge Base**: Company Policies
    """)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📩 Incoming Email")
    default_body = (
        "Hi, \n\n"
        "I bought a Gaming Monitor from you guys back in October. It keeps flickering and I'm sick of it. "
        "I know it's been a few weeks, but I want to return it for a full refund immediately.\n\n"
        "Alice"
    )
    
    email_sender = st.text_input("Sender", value="alice@example.com")
    email_body = st.text_area("Message", height=200, value=default_body)
    analyze_btn = st.button("Generate Response & Insights", type="primary")
def run_agent(sender, body):
    try:
        response = requests.get(OPENAPI_SPEC_URL)
        raw_spec = response.json()
        spec = reduce_openapi_spec(raw_spec)
    except Exception as e:
        return f"Connection Error: {e}"
    

    requests_wrapper = RequestsWrapper(headers={})
    llm = ChatOpenAI(model_name="gpt-4", temperature=0)
    
    agent = planner.create_openapi_agent(
        api_spec=spec, 
        requests_wrapper=requests_wrapper,
        llm=llm,
        allow_dangerous_requests=True
    )

  
    query = (
        f"You are a senior customer support agent. \n"
        f"--- INCOMING CONTEXT ---\n"
        f"CUSTOMER_EMAIL: '{sender}'\n" 
        f"EMAIL_BODY: '{body}'\n"
        f"------------------------\n\n"
        f"YOUR GOAL: Investigate the user and the issue to determine if we can grant their request based on our policies.\n\n"
        f"REQUIRED STEPS:\n"
        f"1. LOOKUP the user profile using the CUSTOMER_EMAIL '{sender}' (Do NOT use their name, use the exact email string).\n"
        f"2. CHECK orders for this user to verify when they bought the item mentioned.\n"
        f"3. SEARCH documents to find the specific policy for Returns or Warranty (check for Tier exceptions!).\n"
        f"4. CHECK past cases to see if they reported this before.\n\n"
        f"OUTPUT FORMAT:\n"
        f"Please provide your final answer in two distinct sections:\n"
        f"--- INSIGHTS ---\n"
        f"(Bullet points of facts: Customer Tier, Order Date, Policy Rule Applied, Decision)\n"
        f"--- DRAFT REPLY ---\n"
        f"(A polite, professional email response based on your decision)"
      )

    st_callback = StreamlitCallbackHandler(
        st.container(),
        collapse_completed_thoughts=False
    )
    

    result = agent.invoke(query, config={"callbacks": [st_callback]})
    return result['output']

with col2:
    st.subheader("Agent Analysis")
    if analyze_btn:
        response_text = run_agent(email_sender, email_body)
        
        if response_text:
            if "--- DRAFT REPLY ---" in response_text:
                insights, reply = response_text.split("--- DRAFT REPLY ---")
                st.markdown("### 🔍 Strategic Insights")
                st.info(insights.replace("--- INSIGHTS ---", "").strip())
                st.markdown("### 📝 Suggested Reply")
                st.success(reply.strip())
            else:
                st.write(response_text)
