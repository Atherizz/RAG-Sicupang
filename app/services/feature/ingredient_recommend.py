import os
import re
import json
from sqlalchemy import text
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.db.database import DBService
from app.helper.clean_sql import extract_select, sanitize_sql
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class IngredientRecommend:
    def __init__(self, model="gemini-1.5-flash-latest"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key tidak ditemukan")

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0.4
        )
        
        # self.llm = ChatOpenAI(
        # model="gpt-4o-mini",
        # temperature=0.4
        # )

        self.db = DBService().get_sql_database()
        self.write_query = create_sql_query_chain(self.llm, self.db)

        self.prompt_template_recommendation = PromptTemplate(
            input_variables=['jumlah_keluarga', 'budget', 'price_context', 'alergi'],
            template="""
    Anda adalah asisten gizi. Buat rencana bahan makanan bergizi untuk {jumlah_keluarga} orang selama 1 bulan, dengan total budget Rp{budget}.

    tugasmu adalah membaca keseluruhan data dalam bentuk list yang rapi secara lengkap sesuai
            dengan pertanyaan pengguna : {price_context} Anda harus membuat rencana ini HANYA dan HANYA MENGGUNAKAN bahan-bahan yang tercantum dalam data tersebut

**JANGAN MENGAMBIL INFORMASI atau MENCIPTAKAN BAHAN PANGAN yang tidak ada dalam daftar yang disediakan.**
Jika suatu bahan tidak ada di {price_context}, JANGAN masukkan ke hasil. 
Jangan improvisasi.
**ATURAN WAJIB:**
- HANYA gunakan bahan yang tercantum dalam data {price_context}
- Nama bahan HARUS sama persis dengan "nama_pangan" di data
- JANGAN buat nama bahan baru atau improvisasi
- MAKSIMALKAN budget (target: 90-100% dari budget total), apabila total_perkiraan_pengeluaran masih belum mencapai target budget, tambahkan kuantitas dari bahan yang sudah ada
- Pertimbangkan alergi: {alergi}

Perhatikan kebutuhan kalori harian rata-rata manusia (sekitar 2000–2500 kkal).

Perhatikan juga kondisi berikut:
- Alergi makanan yang harus dihindari: {alergi}
- Jangan melebihi batas budget pengguna tapi maksimalkan budgetnya

Balas hanya dalam format JSON valid dengan struktur:
{{
  "bahan_makanan": [
    {{
      "nama": "string",
      "jumlah": "string",
      "harga": int,
      "manfaat": "string"
    }}
  ],
  "total_perkiraan_pengeluaran": int
}}

Jangan sertakan teks lain di luar JSON.
"""
        )

        self.chain = self.prompt_template_recommendation | self.llm | StrOutputParser()

    def get_recommendation(self, jumlah_keluarga: int, budget: int, alergi: str):
        sql_query = """
        SELECT JSON_ARRAYAGG(
                 JSON_OBJECT(
                   'nama', nama_pangan,
                   'harga', CAST(harga_satuan AS DECIMAL(12,2))
                 )
               ) AS price_context_json
        FROM (
          WITH hp_rank AS (
            SELECT
              id_pangan,
              harga_satuan,
              tanggal,
              ROW_NUMBER() OVER (
                PARTITION BY id_pangan
                ORDER BY tanggal DESC, id_harga DESC
              ) AS rn
            FROM harga_pangan
          )
          SELECT p.nama_pangan, h.harga_satuan
          FROM pangan p
          JOIN hp_rank h
            ON h.id_pangan = p.id_pangan AND h.rn = 1
          ORDER BY p.nama_pangan
        ) q;
        """

        engine = getattr(self.db, "engine", None) or getattr(self.db, "_engine", None)
        if engine is None:
            raise RuntimeError("SQLAlchemy engine tidak ditemukan dari SQLDatabase")

        with engine.connect() as conn:
            json_str = conn.execute(text(sql_query)).scalar()
            if not json_str:
                json_str = "[]"

        price_context = json_str

        result = self.chain.invoke({
            "jumlah_keluarga": jumlah_keluarga,
            "budget": budget,
            "price_context": price_context,
            "alergi": alergi
        })
        
        match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
        json_str = match.group(1) if match else result
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f":warning: Gagal parse JSON: {e}")
            return None
