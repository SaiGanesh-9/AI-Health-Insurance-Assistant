from fastapi import FastAPI
from pydantic import BaseModel
from chromadb import PersistentClient
from dotenv import load_dotenv
import os
import google.generativeai as genai

# -------------------------------
# STEP 1: Load environment variables
# -------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file!")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------------
# STEP 2: Initialize FastAPI and Chroma Client
# -------------------------------

app = FastAPI()

client_chroma = PersistentClient(path="./chroma_db")
collection_name = "insurance_documents"
collection = client_chroma.get_or_create_collection(name=collection_name)

print(f"Connected to Chroma collection '{collection_name}'.")

# -------------------------------
# STEP 3: Define Request/Response Models
# -------------------------------

class AskRequest(BaseModel):
    query: str
    n_results: int = 3

class AskResponse(BaseModel):
    query: str
    answer: str
    context: list

# -------------------------------
# STEP 4: Define API Endpoints
# -------------------------------

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    query_text = request.query
    n_results = request.n_results

    # Query Chroma collection
    search_results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )

    documents = search_results['documents'][0]

    # Prepare context for Gemini
    context_text = "\n\n".join(documents)

    # Prepare the prompt
    prompt = f"""
You are a helpful assistant for health insurance questions.
Use the below context to answer the user's query in simple and clear language.
If the context does not have enough information, say "I could not find this information in my documents."

Context:
{context_text}

User Question:
{query_text}

Answer:
"""

    # Correct way for 0.8.5 → GenerativeModel
    model = genai.GenerativeModel("models/gemini-1.5-pro")


    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            top_p=1
        )
    )

    answer = response.text.strip()

    return AskResponse(
        query=query_text,
        answer=answer,
        context=documents
    )