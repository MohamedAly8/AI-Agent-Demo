import streamlit as st
import requests
import os
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.utilities import RequestsWrapper
from langchain_community.callbacks import StreamlitCallbackHandler

API_URL = os.getenv("API_URL", "http://localhost:8000")
OPENAPI_SPEC_URL = f"{API_URL}/openapi.json"

st.set_page_config(page_title="Enterprise AI Agent", layout="wide")
st.markdown(
    """
    <style>
    /* 1. Reduce the main page padding */
    div.block-container {
        padding-top: 2rem;    /* Reduced from default 6rem */
        padding-bottom: 1rem; /* Reduced from default 10rem */
        /* padding-left and padding-right are usually fine, but you can adjust them here too */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("VaultCRM Service Center Agent")

with st.sidebar:
    st.markdown("### Agent Status")
    st.success(f"Connected to VaultCRM API")
    st.markdown("---")
    st.markdown("### 🛠️ Developer Tools")
    st.link_button("📖 Open Swagger UI", "http://localhost:8000/docs") 

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
    email_body = st.text_area("Message", height=150, value=default_body)
    

    system_prompt = (
        f"You are a senior customer support agent. \n"
        f"--- INCOMING CONTEXT ---\n"
        f"CUSTOMER_EMAIL: '{email_sender}'\n"
        f"EMAIL_BODY: '{email_body}'\n"
        f"------------------------\n\n"
        f"YOUR GOAL: Investigate the user and the issue to determine if we can grant their request based on our policies.\n\n"
        f"REQUIRED STEPS:\n"
        f"1. LOOKUP the user profile using the CUSTOMER_EMAIL '{email_sender}'.\n"
        f"2. CHECK orders for this user to verify when they bought the item mentioned.\n"
        f"3. SEARCH documents to find the specific policy for Returns or Warranty.\n"
        f"4. CHECK past cases to see if they reported this before.\n\n"
        f"OUTPUT FORMAT:\n"
        f"When you have gathered all details, you MUST start your response with the phrase 'Final Answer:'.\n"
        f"The content after 'Final Answer:' should be exactly in this format:\n\n"
        f"--- INSIGHTS ---\n"
        f"(Bullet points of facts: Customer Tier, Order Date, Policy Rule Applied, Decision)\n"
        f"--- DRAFT REPLY ---\n"
        f"(A polite, professional email response based on your decision)"
    )

    with st.expander("View Agent Prompt", expanded=True):
        st.code(system_prompt, language="text")

    analyze_btn = st.button("Generate Response & Insights", type="primary")

def run_agent(query_text, log_container):
    try:
        response = requests.get(OPENAPI_SPEC_URL)
        raw_spec = response.json()
        spec = reduce_openapi_spec(raw_spec)
    except Exception as e:
        return f"Connection Error: {e}"

    requests_wrapper = RequestsWrapper(headers={})
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    
    agent = planner.create_openapi_agent(
        api_spec=spec, 
        requests_wrapper=requests_wrapper,
        llm=llm,
        allow_dangerous_requests=True,
        agent_executor_kwargs={"handle_parsing_errors": True}
    )

    st_callback = StreamlitCallbackHandler(
        parent_container=log_container,
        collapse_completed_thoughts=False
    )
    
    result = agent.invoke(query_text, config={"callbacks": [st_callback]})
    return result['output']

with col2:
    st.subheader("Agent Analysis")
    
    with st.container(height=900, border=True):
        
        if analyze_btn:            
            with st.status("🔍 Agent is investigating...", expanded=True) as status_box:
                st.write("Connecting with VaultCRM...")
                response_text = run_agent(system_prompt, status_box)
                status_box.update(label="✅ Investigation Complete", state="complete", expanded=True)
            
            st.divider()
            
            if response_text:
                if "--- DRAFT REPLY ---" in response_text:
                    try:
                        parts = response_text.split("--- DRAFT REPLY ---")
                        insights = parts[0].replace("Final Answer:", "").strip()
                        reply = parts[1].strip()
                        
                        st.markdown("### 🧠 Strategic Insights")
                        st.info(insights.replace("--- INSIGHTS ---", "").strip())
                        
                        st.markdown("### 📧 Suggested Reply")
                        st.success(reply)
                    except:
                        st.write(response_text)
                else:
                    st.write(response_text)
