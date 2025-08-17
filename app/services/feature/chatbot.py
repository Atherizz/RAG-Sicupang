from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from app.db.database import get_sql_database
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from app.helper.clean_sql import extract_select, sanitize_sql
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import json

load_dotenv()

class Chatbot:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.4
        )
        # self.llm = ChatOpenAI(
        # model="gpt-4o-mini",
        # temperature=0.4
        # )
        self.index_name = "sicupang-rag-small"
        self.text_field = "text"
        self.embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorStore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embed_model,
            text_key=self.text_field,
            namespace="docs"
        )
        self.db = get_sql_database()

        self.write_query = create_sql_query_chain(self.llm, self.db)
        
        self.router_prompt = PromptTemplate(
            input_variables=["question"],
            template=(
                "Kamu adalah router untuk SICUPANG AI.\n"
                "Tentukan jalur terbaik menjawab pertanyaan berikut.\n\n"
                "Database SQL tersedia dengan tabel-tabel berikut:"
                "desa, harga_pangan, jenis_pangan, kader, kecamatan, keluarga, pangan, pangan_keluarga, rentang_uang, stok_pangan, takaran"
                "Aturan cepat:\n"
                "- Pilih 'sql' jika pertanyaan meminta angka, agregasi, ranking, tren yang jelas ada di database terstruktur atau jika pertanyaan meminta data dari tabel-tabel di atas\n"
                "- Pilih 'rag' jika pertanyaan perlu konteks kebijakan, definisi, penjelasan naratif dari dokumen/laporan.\n"
                "- Pilih 'both' jika butuh angka dari DB sekaligus narasi/konteks/interpretasi kebijakan dari dokumen.\n"
                "- Jika ragu, pilih 'both'.\n\n"
                "Keluarkan JSON valid satu baris, tanpa penjelasan lain, format:\n"
                "{{\"route\":\"sql|rag|both\",\"reason\":\"alasan singkat\"}}\n\n"
                "Pertanyaan: {question}"
            )
        )
        
        self.route_chain = self.router_prompt | self.llm | StrOutputParser()

        self.prompt_template = PromptTemplate(
            input_variables=["question", "query", "context", "result"],
            template=(
                "Kamu adalah SICUPANG AI, asisten Dinas Ketahanan Pangan Kab. Malang.\n"
                "Tugasmu: Jika contextnya sql maka menjawab pertanyaan dengan data hasil SQL secara ringkas, akurat, dan actionable dan jika contextnya rag maka menjawab berdasarkan dokumen yang tersedia"
                "Beri saran atau opini jika memang ditanyakan (membantu pengambilan keputusan pemerintah). "
                "Jangan mengarang di luar hasil SQL/dokumen resmi.\n\n"

                "# Context Route (JSON)\n"
                "{context}\n\n"

                "# Instruksi Wajib Berdasarkan Route\n"
                "- Jika route == 'sql': Jawab HANYA berdasarkan hasil SQL.\n"
                "- Jika route == 'rag': Jawab HANYA berdasarkan konteks dokumen resmi (RAG). "
                "Gunakan definisi, indikator, kebijakan, atau pedoman teknis dari dokumen tersebut. "
                "Abaikan hasil SQL.\n"
                "- Jika route == 'both': Gabungkan jawaban inti dari SQL dan konteks dari dokumen resmi (RAG). "
                "SQL dipakai untuk angka/rekap, RAG dipakai untuk definisi/interpretasi/kebijakan.\n\n"

                "# Input\n"
                "Info tambahan: mata uang pakai Rupiah (Rp.)\n"
                "Pertanyaan Pengguna: {question}\n"
                
                "SQL Query (hanya relevan jika route == 'sql' atau 'both'):\n"
                "{query}\n\n"
                "Hasil SQL (hanya relevan jika route == 'sql' atau 'both'): atau Hasil RAG (jika route == 'rag'\n"
                "{result}"
            )
        )

        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def ask(self, question: str):
        context = self.route_chain.invoke({
            "question": question,
        })
        
        sql_clean = "-"
        query_result = "Tidak ada hasil (karena route bukan SQL)"
        
        try:
            route_data = json.loads(context.strip())
            route = route_data.get("route", "sql")  
        except Exception:
            route = "sql"

        if route in ["sql"]:
            sql_raw = self.write_query.invoke({"question": question})
            sql_sel = extract_select(sql_raw)
            sql_clean = sanitize_sql(sql_sel)

            try:
                query_result = self.db.run(sql_clean)
            except Exception as e:
                query_result = f"ERROR SQL: {e}"

        elif route in ["rag", "both"]:
            sql_clean = "-"
            query_result = self.vectorStore.similarity_search(query=question, k=3, namespace="docs")
        
        print("Route context:", context) 

        final_answer = self.chain.invoke({
            "question": question,
            "context": context,
            "query": sql_clean,
            "result": query_result
        })
        return final_answer
