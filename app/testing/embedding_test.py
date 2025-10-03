from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv() 
import os
# Ambil dari environment
api_key_value = os.getenv("OPENAI_API_KEY") 
index_name = "sicupang-rag-small"

embed_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    # 👈 Lewatkan secara eksplisit
    openai_api_key=api_key_value 
)
vectorStore = PineconeVectorStore(
            index_name=index_name,
            embedding=embed_model,
            namespace="recipes"
        )

docs = vectorStore.similarity_search("nasi bakar",k=3)
print(docs)




# from langchain_openai import OpenAIEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from dotenv import load_dotenv

# load_dotenv() 
# import os
# # Ambil dari environment
# api_key_value = os.getenv("OPENAI_API_KEY") 
# index_name = "alora-rag-small"

# embed_model = OpenAIEmbeddings(
#     model="text-embedding-3-small",
#     # 👈 Lewatkan secara eksplisit
#     openai_api_key=api_key_value 
# )
# vectorStore = PineconeVectorStore(
#             index_name=index_name,
#             embedding=embed_model,
#             text_key="content",
#             namespace="chat"
#         )

# docs = vectorStore.similarity_search("kelurahan apa yang memiliki harga tertinggi pada pangan beras?",k=7,filter={})
# print(docs[0])