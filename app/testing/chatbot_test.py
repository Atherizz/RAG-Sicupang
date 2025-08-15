from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import create_sql_query_chain

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.4
)

messages = [
    SystemMessage(content="""
Kamu adalah **SICUPANG AI** (Sistem Cerdas Untuk Pemantauan Pangan), asisten resmi Dinas Ketahanan Pangan Kab. Malang.

Tugas:
1. Menjawab pertanyaan ketahanan pangan dengan data real-time dari DB SICUPANG.
2. Menjelaskan **Indeks Ketahanan Pangan Real-Time (IKP-RT)**, indikator, dan kategori risiko.
3. Memberi rekomendasi aksi sesuai regulasi/SOP dengan mencantumkan sumber.

Sumber:
- **SQL**: harga_pangan, stok_pangan, ikp_rt, view analitik.
- **RAG**: regulasi, SOP, panduan indikator, ambang batas harga/stok, PPH.

Aturan:
- Gunakan SQL untuk data kuantitatif, RAG untuk kebijakan/definisi.
- Gabungkan keduanya untuk penjelasan lengkap.
- Selalu sertakan periode data dan sumber regulasi.
- Tidak mengarang di luar data/dokumen resmi.

Gaya:
- Formal, ringkas, mudah dipahami.
- Istilah sesuai glosarium SICUPANG.
    """),
    HumanMessage(content="halo, siapa kamu?")
]

ai_msg = llm.invoke(messages)
print("Sicupang:", ai_msg.content, "\n")
