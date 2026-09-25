import os
import json
from dotenv import load_dotenv
from google.cloud import storage
import chromadb
from chromadb import PersistentClient

# -----------------------------
# STEP 1: Load Environment Variables from .env
# -----------------------------

# Load .env file
load_dotenv()

# Get values
gcs_credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
bucket_name = os.getenv("GCS_BUCKET_NAME")
file_name = os.getenv("GCS_EMBEDDING_FILE")

if not all([gcs_credentials_path, bucket_name, file_name]):
    raise Exception("One or more environment variables are missing in .env file!")

# Set GOOGLE_APPLICATION_CREDENTIALS so GCS SDK can use the credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcs_credentials_path

print("Environment variables loaded and GCS credentials set.")

# -----------------------------
# STEP 2: Initialize GCS Client
# -----------------------------

client = storage.Client()
bucket = client.bucket(bucket_name)
blob = bucket.blob(file_name)

# Download file content
data_bytes = blob.download_as_bytes()
print(f"Downloaded '{file_name}' from bucket '{bucket_name}'.")

# -----------------------------
# STEP 3: Load and Parse JSON data
# -----------------------------

# Convert bytes to JSON
data = json.loads(data_bytes)

print(f"Loaded JSON with {len(data)} records.")

# Expected structure per record:
# {
#     "id": "unique_id",
#     "document": "text content here",
#     "embedding": [0.123, 0.456, ...],
#     "metadata": {"source": "something", "page": 5}
# }

# Prepare lists for Chroma insertion
ids = []
documents = []
embeddings = []
metadatas = []

for record in data:
    ids.append(str(record['id']))  # Ensure ID is string
    documents.append(record['document'])
    embeddings.append(record['embedding'])
    
    # metadata is optional
    metadata = record.get("metadata", {})
    metadatas.append(metadata)

print(f"Prepared data for Chroma insert. Total documents: {len(documents)}")

# -----------------------------
# STEP 4: Initialize Chroma and Create Collection
# -----------------------------

# Initialize Chroma client
client_chroma = PersistentClient(path="./chroma_db")

# Create / Get collection
collection_name = "insurance_documents"
collection = client_chroma.get_or_create_collection(name=collection_name)

print(f"Chroma collection '{collection_name}' is ready.")

# -----------------------------
# STEP 5: Insert Data into Chroma
# -----------------------------

collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)

print("Data inserted into Chroma successfully!")

# Persist data
print("Chroma database persisted to disk (./chroma_db).")

# -----------------------------
# STEP 6: (Optional) Test a Query
# -----------------------------

# query = "What is covered under health insurance?"
# results = collection.query(
#     query_texts=[query],
#     n_results=3
# )

# print("\n📌 Example Query Results:")
# for i, doc in enumerate(results['documents'][0]):
#     print(f"{i+1}. {doc}")

# print("\n🎉 Done!")
