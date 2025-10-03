from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

# Setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("sicupang-rag-small")
embed_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Generate embedding untuk query
query_text = "nasi tongseng kambing"
query_vector = embed_model.embed_query(query_text)

# Query langsung ke Pinecone
results = index.query(
    vector=query_vector,
    top_k=1,
    namespace="recipes",  # ⚠️ PENTING: Pastikan namespace sama
    include_metadata=True
)

print(f"Query: '{query_text}'")
print(f"Results found: {len(results['matches'])}")
for match in results['matches']:
    print(f"\nScore: {match['score']}")
    print(f"ID: {match['id']}")
    print(f"Metadata: {match['metadata']}")