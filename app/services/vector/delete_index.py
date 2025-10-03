import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
if "sicupang-rag-small" in pc.list_indexes().names():
    print("Menghapus index sicupang-rag-small...")
    pc.delete_index("sicupang-rag-small")