import os, uuid
import time
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from app.services.vector.load_pinecone import loadPinecone

load_dotenv()
pineconeApiKey = os.getenv("PINECONE_API_KEY")
openAIApiKey = os.getenv("OPENAI_API_KEY")

pdf_path = "data/Indeks Ketahanan Pangan Tahun 2023.pdf"
namespace = "docs"
index_name = "sicupang-rag-small"
model_name = "text-embedding-3-small"
dimension = 1536

pc = Pinecone(api_key=pineconeApiKey)

index = loadPinecone(index_name, dimension)

embed_model = OpenAIEmbeddings(model=model_name)

loader = PyPDFLoader(pdf_path)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200, chunk_overlap=200,
    separators=["\n\n", "\n", ".", " "]
)

splits = splitter.split_documents(docs)

for d in splits:
    d.metadata.update({
        "doc_type": "policy",
        "title": "Indeks Ketahanan Pangan 2023",
        "jurisdiction": "Kabupaten Malang",
        "year": 2023,
        "source_id": f"{os.path.basename(pdf_path)}#p{d.metadata.get('page', 0)}",
        "tags": ["ikp", "indeks ketahanan pangan"]
    })

# 3) vectorstore (auto-embed + batch upsert)
vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embed_model,
    namespace=namespace,
    text_key="text"
)

ids = [str(uuid.uuid4()) for _ in range(len(splits))]
vectorstore.add_documents(documents=splits, ids=ids, batch_size=64)


    
    
    