# AI-Powered Health Insurance Support Assistant

An AI-powered health insurance chatbot designed to help customers understand their insurance policies without having to call customer support for every question.

The application uses **OCR, Retrieval-Augmented Generation (RAG), semantic search, and Large Language Models (LLMs)** to understand insurance documents and provide answers based on relevant policy information.

The main goal is simple:

> **Reduce repetitive insurance support calls while helping customers get faster and more relevant answers about their policies.**

---

## Why We Built This

Health insurance documents contain a lot of important information, but they are often long and difficult to understand.

Customers frequently contact insurance support teams for questions such as:

- Is maternity covered?
- What is my waiting period?
- Is OPD included?
- What is my sum insured?
- Are pre-existing conditions covered?
- Is dental treatment covered?
- What are my ambulance benefits?
- What is not covered?
- Can I cancel my policy and receive a refund?

Most of these answers already exist somewhere inside the customer's policy documents.

The problem is finding and understanding them.

Instead of expecting customers to read through dozens of pages or call an insurance representative, we wanted to create a system where they could simply **ask their policy a question**.

---

# How It Works

The user uploads their insurance policy and asks a question in normal conversational language.

For example:

```text
"Is maternity covered under my policy?"
```

The system processes the policy, searches the insurance knowledge base for relevant information, and provides the most relevant context to the language model.

The LLM then converts that information into a simple conversational response.

```text
Customer
   │
   ▼
Upload Insurance Policy
   │
   ▼
Extract Policy Information
   │
   ▼
Ask a Question
   │
   ▼
Find Relevant Insurance Information
   │
   ▼
Build Context
   │
   ▼
Generate Answer
   │
   ▼
Customer
```

This is different from simply asking an LLM a general insurance question.

The goal is to ground the response in **insurance documentation and the customer's policy context**.

---

# Architecture

```text
                       CUSTOMER
                          │
                          ▼
                 ┌─────────────────┐
                 │  Streamlit UI   │
                 └────────┬────────┘
                          │
                    Upload Policy
                    PDF / TXT File
                          │
                          ▼
              ┌──────────────────────┐
              │ Document Processing  │
              │                      │
              │ PyPDF2               │
              │ pytesseract OCR      │
              │ Text Preprocessing   │
              └──────────┬───────────┘
                         │
                         ▼
                 Extract Policy Data
                         │
                         ▼
                   User Question
                         │
                         ▼
               Identify / Use Provider
                         │
                         ▼
                  Semantic Search
                         │
                         ▼
                  ┌────────────┐
                  │  ChromaDB  │
                  └──────┬─────┘
                         │
                  Relevant Chunks
                         │
                         ▼
                     FastAPI
                         │
                         ▼
                 ┌──────────────┐
                 │Google Gemini │
                 └──────┬───────┘
                        │
                        ▼
                 Generated Answer
                        │
                        ▼
                     CUSTOMER
```

---

# Main Components

## 1. Document Processing

Insurance policies can come in different formats.

Some PDFs contain readable text, while others may contain scanned pages or images.

To handle both cases, the project uses:

**PyPDF2** for text-based PDF documents.

**pytesseract OCR** for scanned/image-based documents.

The preprocessing pipeline combines these approaches so that more information can be extracted from different types of insurance documents.

The application also attempts to identify useful policy information such as:

```text
Insurance Company
Policy Number
Plan Name
Sum Insured
```

The current version uses text extraction and pattern-based detection for these fields.

---

## 2. Chunking

Once text has been extracted, the insurance document is divided into smaller sections.

The project uses:

```text
RecursiveCharacterTextSplitter
```

with chunks of approximately **1,000 characters** and overlap between neighboring chunks.

Instead of searching an entire insurance document every time someone asks a question, the system can search smaller sections and retrieve only the ones that are relevant.

---

## 3. Embeddings

Each document chunk is converted into an embedding using:

```text
Sentence Transformers
all-MiniLM-L6-v2
```

The model generates **384-dimensional embeddings** representing the semantic meaning of the text.

This allows the system to search based on meaning rather than depending entirely on exact keyword matches.

For example:

```text
User:

"Will my policy pay for an ambulance?"
```

may still retrieve a section titled:

```text
Emergency Transportation Benefits
```

even though the wording is different.

---

## 4. ChromaDB

The embeddings are stored and searched using **ChromaDB**.

The project uses persistent ChromaDB storage, which means the embeddings remain available after the application restarts.

```text
Insurance Documents
        ↓
      Chunks
        ↓
    Embeddings
        ↓
     ChromaDB
        ↓
  Semantic Search
```

This avoids loading and rebuilding the entire knowledge base every time the chatbot starts.

---

# Provider-Focused Retrieval

One of the main ideas behind the project is to avoid searching unnecessary insurance-provider information.

Suppose the knowledge base contains information from:

```text
HDFC ERGO
ICICI Lombard
Care Health
Other Providers
```

and the customer's insurance is with:

```text
ICICI Lombard
```

Ideally, the retrieval pipeline should focus on:

```text
Customer
    ↓
ICICI Lombard Policy
    ↓
ICICI Knowledge
    ↓
Relevant Documents
```

instead of:

```text
Customer
    ↓
Search Every Insurance Company
    ↓
Remove Irrelevant Information
    ↓
Answer
```

This reduces irrelevant retrieval and also helps prevent information from one insurance provider from being confused with another provider's policy.

The project already stores company information as metadata with document embeddings, which provides the foundation for this approach.

Provider-level filtering is one of the areas being strengthened as the project develops.

---

# Retrieval-Augmented Generation (RAG)

The chatbot uses a **RAG architecture**.

Instead of depending entirely on what the LLM already knows, the system first searches the insurance knowledge base.

```text
User Question
      │
      ▼
Create Query Representation
      │
      ▼
Search ChromaDB
      │
      ▼
Retrieve Relevant Policy Sections
      │
      ▼
Build Context
      │
      ▼
Send Context + Question to LLM
      │
      ▼
Generate Answer
```

The current backend instructs Gemini to answer using the retrieved context and indicate when enough information is not available.

This makes the chatbot more controlled than simply sending insurance questions directly to a general-purpose LLM.

---

# Privacy and PII

Insurance documents may contain sensitive customer information.

Protecting that information is an important part of the project's design.

The intended architecture is to keep personally identifiable information separate from the information actually required by the LLM.

```text
Customer Policy
      │
      ▼
Local Processing
      │
      ▼
Detect Sensitive Information
      │
      ▼
Mask / Remove PII
      │
      ▼
Relevant Insurance Context
      │
      ▼
LLM
      │
      ▼
Response
```

Examples of information that should be protected include:

```text
Customer Name
Policy Number
Phone Number
Email
Address
Date of Birth
Personal Identifiers
```

The LLM usually does not need someone's name, phone number, email address, or complete policy identifier to answer a question such as:

```text
"What is my maternity waiting period?"
```

The goal is therefore to send **only the minimum information required to answer the question**.

The current POC still requires additional privacy hardening before claiming complete PII isolation from the external LLM.

---

# FastAPI Backend

The backend is built using **FastAPI**.

The current implementation provides two main endpoints.

### Health Check

```http
GET /health
```

Used to verify that the backend is running.

### Ask

```http
POST /ask
```

The `/ask` endpoint handles the main RAG workflow:

```text
Question
   ↓
ChromaDB Search
   ↓
Relevant Documents
   ↓
Context Preparation
   ↓
Gemini
   ↓
Answer
```

FastAPI provides a lightweight API layer between the user interface, vector database, and LLM.

---

# Streamlit Chatbot

The frontend is built using **Streamlit**.

Users can:

- Upload PDF or TXT insurance documents
- View detected policy information
- Ask questions in natural language
- Receive conversational responses
- Continue the conversation through chat history

The application combines information from the uploaded policy and the insurance knowledge base when preparing context for the chatbot.

---

# Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| PDF Processing | PyPDF2 |
| OCR | pytesseract |
| PDF/Image Processing | pdf2image |
| Text Chunking | RecursiveCharacterTextSplitter |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| LLM | Google Gemini |
| Cloud Storage | Google Cloud Storage |
| Environment Management | python-dotenv |

---

# Architecture Evolution

The current architecture was not our first approach.

Originally, the project was designed around **Google Cloud Vertex AI Vector Search**.

The initial architecture looked like:

```text
Insurance PDFs
      ↓
Text Extraction / OCR
      ↓
Preprocessing
      ↓
Chunking
      ↓
Embeddings
      ↓
Google Cloud Storage
      ↓
Vertex AI Vector Search
      ↓
Gemini
```

Document extraction, preprocessing, embedding generation, and creation of the Vertex AI vector index worked successfully.

However, we encountered reliability issues while querying the deployed Vertex AI index, including connection and index-readiness errors. Multiple troubleshooting attempts did not resolve the issue.

Instead of rebuilding everything, we changed only the retrieval layer.

```text
Existing Embeddings
       ↓
Download from GCS
       ↓
Store in ChromaDB
       ↓
Persistent Vector Search
```

This allowed us to reuse the embeddings that had already been generated while moving to a simpler retrieval architecture.

---

# Vertex AI vs ChromaDB

| Vertex AI Approach | ChromaDB Approach |
|---|---|
| Cloud-based vector search | Lightweight vector database |
| More infrastructure setup | Simpler POC setup |
| Managed cloud infrastructure | Local persistent storage |
| Query issues during development | Working semantic retrieval |
| Existing embeddings generated | Same embeddings reused |
| Original architecture | Current architecture |

The switch was mainly an engineering decision to make the POC easier to control and continue developing.

---

# Traditional Support vs Our Approach

| Traditional Insurance Support | AI-Assisted Support |
|---|---|
| Customer searches long documents | Customer asks a question |
| May require a phone call | Routine questions can be self-service |
| Agent searches documentation manually | Semantic search finds relevant sections |
| Repetitive questions consume support time | Common questions can be automated |
| Customer needs insurance terminology | Natural-language questions are supported |
| Information may take time to locate | Relevant sections are retrieved quickly |

The objective is **not to completely replace human insurance support**.

A better model is:

```text
                    Customer Question
                           │
                           ▼
                       Chatbot
                           │
               ┌───────────┴───────────┐
               │                       │
               ▼                       ▼
        Routine Question          Complex Case
               │                       │
               ▼                       ▼
         AI Response             Human Support
```

Human representatives remain important for claims disputes, complex policy situations, exceptions, and cases requiring judgment.

---

# Current Results

During testing, the chatbot was able to handle questions around topics such as:

- Claimable amount
- Maternity benefits
- OPD
- Waiting periods
- Pre-existing conditions
- Dental treatment
- Daycare procedures
- Cancer coverage
- Policy cancellation
- Pre-hospitalization
- ICU restrictions
- Ambulance coverage
- Congenital conditions
- Consumables

The project results show examples of the chatbot answering these types of questions using uploaded documents and the internal insurance knowledge base.

---

# Current vs Future Architecture

| Current POC | Future Improvement |
|---|---|
| Basic policy detection | Better structured policy extraction |
| Semantic search | Hybrid retrieval |
| Top-K retrieval | Retrieval + reranking |
| Provider metadata | Strict provider filtering |
| Basic RAG | Citation-aware RAG |
| Gemini generation | Validated grounded responses |
| Basic privacy controls | Dedicated PII gateway |
| Streamlit | Production web/mobile UI |
| Local ChromaDB | Scalable vector infrastructure |
| Basic chat history | Secure conversational memory |
| Chatbot answers | Chatbot + human escalation |

---

# Future Improvements

### Better Provider Filtering

The system should automatically identify the customer's insurance provider and apply that provider as a metadata filter before vector search.

```text
Question
   ↓
Identify Provider
   ↓
Filter Documents
   ↓
Semantic Search
```

This will reduce irrelevant results and prevent mixing information across insurance companies.

### Stronger PII Protection

A dedicated privacy layer should detect and redact sensitive information before anything is sent to an external LLM.

### Better Policy Extraction

Different insurers use different layouts and terminology.

Future versions can combine:

```text
OCR
+
Regex
+
Named Entity Recognition
+
Document Layout Understanding
```

to extract policy information more reliably.

### Hybrid Search

Semantic search can eventually be combined with keyword search.

```text
Vector Search
      +
Keyword Search
      +
Metadata Filtering
      ↓
Best Results
```

This can be particularly useful for exact clause names, product codes, and policy terminology.

### Reranking

Instead of immediately sending retrieved documents to the LLM:

```text
Retrieve Top 10
      ↓
Rerank
      ↓
Best 3–5
      ↓
LLM
```

This can improve the quality of context while reducing unnecessary tokens.

### Source Citations

Future answers should tell customers where the information came from.

For example:

```text
Your policy provides 60 days of
pre-hospitalization coverage.

Source:
Policy Document
Page 34
Pre-Hospitalization Benefits
```

### Confidence-Based Escalation

The chatbot should not guess when it cannot find reliable information.

```text
Question
   ↓
Retrieval
   ↓
Confidence
  /      \
High      Low
 │         │
 ▼         ▼
Answer   Human Support
```

### Multilingual Support

Future versions could allow customers to ask questions in multiple languages while retrieving information from the same policy knowledge base.

### Voice Support

The same architecture could eventually support:

```text
Customer Voice
      ↓
Speech-to-Text
      ↓
Insurance RAG
      ↓
Answer
      ↓
Text-to-Speech
```

This could extend the chatbot into an AI-assisted support channel.

---

# Project Structure

```text
Health_insurance_project/
│
├── api_server_gemini.py
├── chatbot_ui.py
├── load_embeddings.py
├── models_check.py
├── requirements.txt
├── chroma_db/
└── .env
```

Supporting notebooks include:

```text
preprocessing.ipynb
Embeddings_creation.ipynb
index.ipynb
```

---

# Running the Project

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start FastAPI

```bash
uvicorn api_server_gemini:app --reload
```

The API will run locally at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

These are the execution steps documented for the project.

### 4. Start Streamlit

Open another terminal:

```bash
streamlit run chatbot_ui.py
```

Upload an insurance policy and start asking questions.

---


# Security

Insurance documents can contain sensitive customer information.

For development:

```text
Do not commit:

.env
API keys
Service-account credentials
Customer policy documents
Customer PII
Private cloud credentials
```

The current application is a **Proof of Concept** and requires additional security and privacy controls before it should be used with real customer data in a production environment.

---

# Long-Term Vision

The long-term goal is not simply to build another chatbot.

We want to make insurance information easier for customers to understand while reducing repetitive work for support teams.

```text
                    CUSTOMER
                       │
                       ▼
                Ask a Question
                       │
                       ▼
               Understand Policy
                       │
                       ▼
               Identify Provider
                       │
                       ▼
              Retrieve Information
                       │
                       ▼
                  Protect PII
                       │
                       ▼
                Generate Answer
                       │
                       ▼
                Check Confidence
                  /           \
                 ▼             ▼
              Answer       Human Agent
```

The system should be able to handle routine policy questions quickly while recognizing when a question requires a human insurance professional.

The idea is simple:

> **Let AI handle repetitive information retrieval so that customers get faster answers and insurance support teams can spend more time on complex cases that actually need human attention.**

---

# Disclaimer

This project is currently intended for **AI/RAG research, software engineering, educational development, and proof-of-concept purposes**.

The chatbot's responses should not be treated as medical, legal, financial, claims, or insurance advice.

Coverage and claim decisions should always be verified against the official policy documentation and, where necessary, with the insurance provider.