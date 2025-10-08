from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import re
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


food_name = "nasi rawon"
query_base = re.sub(r'\b(nasi|ketupat|lontong|)\b', '', food_name, flags=re.IGNORECASE).strip()

query_vector = embed_model.embed_query(query_base)

# Query langsung ke Pinecone
results = index.query(
    vector=query_vector,
    top_k=1,
    namespace="recipes",  # ⚠️ PENTING: Pastikan namespace sama
    include_metadata=True
)

print(f"Query: '{query_base}'")
print(f"Results found: {len(results['matches'])}")
for match in results['matches']:
    print(f"\nScore: {match['score']}")
    print(f"ID: {match['id']}")
    print(f"Metadata: {match['metadata']}")