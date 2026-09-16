import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
)

print("Connecting to Pinecone...")

vectorstore = PineconeVectorStore(
    index_name=os.getenv("PINECONE_INDEX"),
    embedding=embeddings
)

query = "What should be done if the vehicle temperature exceeds 4 degrees Celsius?"

print("\nSearching SOP...")
print("Query:", query)

results = vectorstore.similarity_search(
    query,
    k=2
)

print("\n===== SOP SEARCH RESULTS =====\n")

for i, document in enumerate(results, start=1):
    print(f"--- Result {i} ---")
    print(document.page_content)
    print()