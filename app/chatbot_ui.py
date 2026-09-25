import streamlit as st
import requests
import os
import tempfile
import PyPDF2
from dotenv import load_dotenv
import chromadb

# Load env variables
load_dotenv()

# -------------------------------
# PAGE SETUP
# -------------------------------

st.set_page_config(page_title="Health Insurance Chatbot", page_icon="💬")
st.title("Health Insurance Chatbot")
st.write("Ask any health insurance related questions below:")

# -------------------------------
# SESSION STATE INIT
# -------------------------------

if "user_docs" not in st.session_state:
    st.session_state.user_docs = []

if "uploaded_policies" not in st.session_state:
    st.session_state.uploaded_policies = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# PDF POLICY DETECTION FUNCTION
# -------------------------------

def extract_policy_details(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

    policy_details = {}

    if "Policy Number" in text:
        policy_details["Policy Number"] = text.split("Policy Number")[1].split("\n")[0].strip()

    if "Plan" in text or "Plan Name" in text:
        if "Plan Name" in text:
            policy_details["Plan"] = text.split("Plan Name")[1].split("\n")[0].strip()
        else:
            policy_details["Plan"] = text.split("Plan")[1].split("\n")[0].strip()

    if "Sum Insured" in text:
        policy_details["Sum Insured"] = text.split("Sum Insured")[1].split("\n")[0].strip()

    return policy_details, text

# -------------------------------
# FILE UPLOAD
# -------------------------------

st.header("Upload your insurance policy documents (PDF or TXT)")
uploaded_files = st.file_uploader("Upload up to 3 Insurance Policies", type=["pdf", "txt"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 3:
        st.error("⚡ You can upload a maximum of 3 files only.")
    else:
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 3 * 1024 * 1024:
                st.error(f"❗ File {uploaded_file.name} exceeds 3MB limit and was not uploaded.")
                continue

            if uploaded_file.name not in st.session_state.uploaded_policies:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    policy_info, extracted_text = extract_policy_details(tmp_file.name)

                    st.session_state.uploaded_policies[uploaded_file.name] = policy_info
                    st.session_state.user_docs.append({
                        "filename": uploaded_file.name,
                        "content": extracted_text
                    })

st.success("Files uploaded and extracted successfully!")

# -------------------------------
# SHOW DETECTED POLICIES
# -------------------------------

if st.session_state.uploaded_policies:
    st.subheader("Detected Policies from Uploaded Documents:")
    for filename, policy in st.session_state.uploaded_policies.items():
        st.markdown(f"**{filename}** →")
        if policy:
            for k, v in policy.items():
                st.markdown(f"- {k}: {v}")
        else:
            st.markdown("- Policy plan not found clearly.")

# -------------------------------
# DISPLAY CHAT HISTORY
# -------------------------------

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Bot:** {message['content']}")

# -------------------------------
# USER INPUT (Using Form)
# -------------------------------

with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_input("Your question:", value="", key="input_box", label_visibility="collapsed")
    submit_button = st.form_submit_button(label='Send')

# -------------------------------
# HANDLE USER SUBMISSION
# -------------------------------

if submit_button and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare policy context
    policy_context = ""
    for policy in st.session_state.uploaded_policies.values():
        policy_context += "\n".join([f"{k}: {v}" for k, v in policy.items()]) + "\n\n"

    # Prepare uploaded document context
    policy_docs = ""
    if st.session_state.user_docs:
        policy_docs = "\n\n".join([f"Document ({doc['filename']}):\n{doc['content']}" for doc in st.session_state.user_docs])

    # Query Chroma for general knowledge
    try:
        client_chroma = chromadb.PersistentClient(path="./chroma_db")
        collection = client_chroma.get_or_create_collection(name="insurance_documents")

        search_results = collection.query(
            query_texts=[user_input],
            n_results=3
        )

        chroma_docs = search_results['documents'][0]
        chroma_context = "\n".join(chroma_docs)

    except Exception as e:
        chroma_context = "Could not retrieve general insurance info. Limited to uploaded documents only."

    # Build final prompt
    prompt = f"""
You are a health insurance assistant.

User Uploaded Policy Details:
{policy_context}

General Insurance Plan Info from Database:
{chroma_context}

User Uploaded Policy Documents:
{policy_docs}

User Question:
{user_input}

Answer:
"""

    # Send to FastAPI /ask
    try:
        with st.spinner("Thinking..."):
            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={"query": prompt, "n_results": 3}
            )

        if response.status_code == 200:
            answer = response.json()["answer"]
        else:
            answer = f"Backend error (Status Code: {response.status_code})"
            print(f"Backend error details: {response.text}")

    except requests.exceptions.ConnectionError:
        answer = "Error: Could not connect to backend API. Is FastAPI server running?"
    except Exception as e:
        answer = f"Unexpected error: {e}"

    st.session_state.messages.append({"role": "bot", "content": answer})
    st.rerun()
