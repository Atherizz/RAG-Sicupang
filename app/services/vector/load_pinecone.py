import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings


def loadPinecone(index_name: str, dimension: int, metric: str = "cosine", region: str = "us-east-1"):
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY tidak ditemukan di environment/.env")

    pc = Pinecone(api_key=api_key)

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region=region),
        )
        while not pc.describe_index(index_name).status["ready"]:
            print(f"⏳ Menunggu index '{index_name}' siap...")
            time.sleep(1)

    return pc.Index(index_name)