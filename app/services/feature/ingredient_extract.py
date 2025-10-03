import os
from typing import List, Dict, Any
import json
import re
from sqlmodel import Session
from datetime import date
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from app.db.database import DBService
from app.db.models.household_food import HouseholdFood, InsertHouseholdFood
from app.db.models.recipe_cache import GetRecipeCacheByName
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.schemas.request_model import FoodInput
from starlette.concurrency import run_in_threadpool
from decimal import Decimal


class IngredientExtract:
    def __init__(self, model="gemini-2.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key tidak ditemukan")

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0.4
        )

        self.index_name = "sicupang-rag-small"
        self.namespace = "recipes"
        self.db = DBService()

        self.embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorStore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embed_model,
            text_key="ingredients",
            namespace="recipes"
        )

    async def searchingFood(self, items: List[FoodInput], id_keluarga: int, session: Session):
        results = []
        today = date.today()
        for item in items:
            food_name = item.food_name.strip()
            portion_input = item.portion

            cache_entry = await run_in_threadpool(
                GetRecipeCacheByName,
                food_name,
                session
            )

            if cache_entry:
                print(f"✅ Ditemukan di cache: {food_name}")
                bahan_parsed: List[Dict[str, Any]] = json.loads(cache_entry.bahan_parsed)
                std_portion = cache_entry.standar_porsi

                if std_portion > 0:
                    faktor_skala = portion_input / std_portion
                else:
                    print(f"⚠️ Error: Estimasi porsi standar {food_name} adalah nol.")
                    continue

                for bahan in bahan_parsed:
                    berat_konsumsi = bahan["jumlah_standar"] * faktor_skala
                    berat_per_urt = bahan.get("berat_per_urt", 0)
                    if berat_per_urt == 0:
                        print(f"⚠️ Error: Berat per URT bahan ID {bahan.get('id_pangan')} adalah nol.")
                        continue

                    urt = berat_konsumsi / berat_per_urt
                    urt_value = Decimal(urt).quantize(Decimal('0.01'))

                    bahan_pangan = HouseholdFood(
                        id_keluarga=id_keluarga,
                        id_pangan=bahan["id_pangan"],
                        urt=urt_value,
                        tanggal=today
                    )

                    try:
                        inserted_record = await run_in_threadpool(
                            InsertHouseholdFood,
                            bahan_pangan,
                            session
                        )

                        results.append({
                            "food": food_name,
                            "id_pangan": inserted_record.id_pangan,
                            "urt": float(inserted_record.urt),
                            "status": "Sukses Insert dari Cache"
                        })
                    except Exception as e:
                        print(f"❌ Gagal insert data {bahan['id_pangan']} untuk {food_name}: {e}")
            else:
                print(f"❌ Tidak ditemukan di cache: {food_name}. Memulai RAG...")
                rag_prompt_content, resep_id_vdb = await self.build_augmented_message(
                    food_name=food_name,
                    session=session
                )
                if resep_id_vdb is not None:
                    print(f"➡️ Resep VDB ID {resep_id_vdb} ditemukan. Melanjutkan ke LLM Parsing...")

        return results

    async def build_augmented_message(self, food_name: str, session: Session, k: int = 1):
        query_vector = await run_in_threadpool(
            self.embed_model.embed_query,
            food_name
        )

        results = await run_in_threadpool(
            self.vectorStore._index.query,
            vector=query_vector,
            top_k=k,
            namespace="recipes",
            include_metadata=True
        )

        if not results['matches']:
            return "Resep tidak ditemukan di VDB.", None

        first_match = results['matches'][0]
        ingredients_text = first_match['metadata']['content']
        resep_id_vdb = first_match['id']
        resep_title = first_match['metadata']['title']

        bahan_mentah_list = [item.strip() for item in ingredients_text.split('--') if item.strip()]
        konteks_bahan = "\n".join([f"- {bahan}" for bahan in bahan_mentah_list])

        SYSTEM_INSTRUCTION = (
            "Anda adalah asisten ahli nutrisi yang bertugas memetakan bahan resep ke format data terstruktur. "
            "Untuk setiap bahan, ekstrak kuantitas mentah (misal: 1/4 kg menjadi 250 gram) dan siapkan dalam format JSON."
        )

        HUMAN_PROMPT = f"""
        Resep yang ditemukan untuk "{resep_title}" memiliki ID VDB: {resep_id_vdb}.
        
        Bahan-bahan mentah dari resep tersebut adalah:
        {konteks_bahan}
        
        Tugas Anda:
        1. Konversi semua kuantitas ke **gram** atau **mililiter** (gunakan konversi umum).
        2. Susun data dalam array JSON dengan format berikut:
        
        [
            {{
                "nama_bahan": "nama bahan yang diekstrak",
                "kuantitas_satuan": jumlah berat dalam gram/ml (float),
                "satuan_asli": "satuan asli di resep (cth: kg, siung, bungkus)"
            }},
            // ... untuk bahan lainnya
        ]
        
        Berikan HANYA array JSON, tanpa teks penjelasan apa pun.
        """

        messages = [
            SystemMessage(content=SYSTEM_INSTRUCTION),
            HumanMessage(content=HUMAN_PROMPT)
        ]

        response = await self.llm.ainvoke(messages)
        
        result = response.content
        
        match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
        json_str = match.group(1) if match else result
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f":warning: Gagal parse JSON: {e}")
            return None
