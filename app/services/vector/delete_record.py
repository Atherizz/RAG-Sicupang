import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load API key dari .env
load_dotenv()
pineconeApiKey = os.getenv("PINECONE_API_KEY")

# Inisialisasi client
pc = Pinecone(api_key=pineconeApiKey)

# Nama index dan namespace
index_name = "sicupang-rag-small"
namespace = "recipes"

# Connect ke index
index = pc.Index(index_name)

# Delete semua vector di namespace 'recipes'
index.delete(delete_all=True, namespace=namespace)

print(f"✅ Semua record di namespace '{namespace}' berhasil dihapus dari index '{index_name}'")
