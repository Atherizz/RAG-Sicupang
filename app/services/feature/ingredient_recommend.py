import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain.prompts import PromptTemplate
from app.db.database import get_sql_database
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
        #     model="gpt-4o-mini",  # atau "gpt-3.5-turbo"
        #     temperature=0.4
        # )
        # self.price_context = None
        self.db = get_sql_database()
        self.write_query = create_sql_query_chain(self.llm, self.db)

        self.prompt_template_recommendation = PromptTemplate(
            input_variables=['jumlah_keluarga', 'budget', 'price_context', 'alergi'],
            template="""
Anda adalah asisten gizi. Buat rencana bahan makanan bergizi untuk {jumlah_keluarga} orang selama 1 bulan, dengan total budget Rp{budget}.
Gunakan data harga bahan makanan sesuai isi tabel berikut sebagai acuan: {price_context}, jangan mengarang data bahan pangan yang tidak ada pada query.

Perhatikan kebutuhan kalori harian rata-rata manusia (sekitar 2000–2500 kkal), pikirkan secara logis.

Perhatikan juga kondisi berikut:
- Alergi makanan yang harus dihindari: {alergi}

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
        question = "tampilkan seluruh data harga pangan"
        sql_raw = self.write_query.invoke({"question": question})
        sql_sel = extract_select(sql_raw)
        sql_clean = sanitize_sql(sql_sel)

        query_result = self.db.run(sql_clean)
        result = self.chain.invoke({
            "jumlah_keluarga": jumlah_keluarga,
            "budget": budget,
            "price_context": query_result,
            "alergi": alergi
        })

        match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"⚠️ Gagal parse JSON: {e}")
                return None
        else:
            print("⚠️ Format response tidak sesuai. Tidak ditemukan blok ```json ... ```.")
            return None
