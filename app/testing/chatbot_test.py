import os
from typing import List, Dict, Any, Optional
import json
import re
from sqlmodel import Session
from datetime import date
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from app.db.database import DBService
from app.db.models.household_food import HouseholdFood, InsertHouseholdFood
from app.db.models.food_recipe import GetRecipeCacheByName
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

    async def _process_and_insert_ingredients(
        self, 
        food_name: str, 
        portion_input: float, 
        resep_data: Dict[str, Any], 
        id_keluarga: int, 
        today: date, 
        session: Session
    ) -> List[Dict[str, Any]]:
        
        bahan_parsed: List[Dict[str, Any]] = resep_data.get("bahan_parsed", [])
        std_portion = resep_data.get("standar_porsi", 0)

        if std_portion <= 0:
            print(f"⚠️ Error: Estimasi porsi standar {food_name} adalah nol setelah RAG.")
            return []

        faktor_skala = portion_input / std_portion
        temp_results = []

        for bahan in bahan_parsed:
            berat_konsumsi = bahan.get("jumlah_standar", 0) * faktor_skala
            berat_per_urt = bahan.get("berat_per_urt", 0) 
            id_pangan = bahan.get("id_pangan", None)

            if berat_per_urt == 0 or id_pangan is None:
                print(f"⚠️ Error: Data porsi atau ID Pangan bahan tidak lengkap untuk {food_name}.")
                continue

            urt = berat_konsumsi / berat_per_urt
            urt_value = Decimal(str(urt)).quantize(Decimal('0.01')) 

            bahan_pangan = HouseholdFood(
                id_keluarga=id_keluarga,
                id_pangan=id_pangan,
                urt=urt_value,
                tanggal=today
            )

            try:
                inserted_record = await run_in_threadpool(
                    InsertHouseholdFood,
                    bahan_pangan,
                    session
                )

                temp_results.append({
                    "food": food_name,
                    "id_pangan": inserted_record.id_pangan,
                    "urt": float(inserted_record.urt),
                    "status": "Sukses Insert"
                })
            except Exception as e:
                print(f"❌ Gagal insert data {id_pangan} untuk {food_name}: {e}")
                
        return temp_results

    async def searchingFood(self, items: List[FoodInput], id_keluarga: int, session: Session):
        results = []
        uncached_items: List[FoodInput] = [] 
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
                    urt_value = Decimal(str(urt)).quantize(Decimal('0.01')) 

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
                print(f"❌ Tidak ditemukan di cache: {food_name}. Ditambahkan ke antrian RAG.")
                uncached_items.append(item)

        if uncached_items:
            food_names_to_rag = [item.food_name.strip() for item in uncached_items]
            print(f"\n🚀 Memulai Bulk RAG untuk {len(food_names_to_rag)} makanan...")

            bulk_rag_results = await self.build_augmented_message_bulk( 
                food_names=food_names_to_rag, 
                session=session
            )
            
            for item in uncached_items:
                food_name = item.food_name.strip()
                portion_input = item.portion
                
                rag_data_for_food = bulk_rag_results.get(food_name) 

                if rag_data_for_food:
                    print(f"✅ Hasil RAG ditemukan untuk: {food_name}. Memproses...")
                    
                    new_records = await self._process_and_insert_ingredients(
                        food_name, 
                        portion_input, 
                        rag_data_for_food, 
                        id_keluarga, 
                        today, 
                        session
                    )
                    results.extend(new_records)
                else:
                    print(f"❌ Gagal mendapatkan hasil RAG untuk: {food_name}")

        return results

async def build_augmented_message_bulk(self, food_names: List[str], session: Session, k: int = 1) -> Dict[str, Optional[Dict[str, Any]]]:
    combined_vdb_context = ""
    vdb_data_map = {} # Untuk menyimpan metadata dan konteks VDB per makanan

    # 1. RETRIEVAL: Kumpulkan semua konteks VDB
    for food_name in food_names:
        # Panggilan VDB tetap satu per satu per makanan (atau bisa diparalelkan)
        query_vector = await run_in_threadpool(self.embed_model.embed_query, food_name)
        results = await run_in_threadpool(
            self.vectorStore._index.query,
            vector=query_vector,
            top_k=k,
            namespace="recipes",
            include_metadata=True
        )

        if results['matches']:
            first_match = results['matches'][0]
            ingredients_text = first_match['metadata']['content']
            resep_title = first_match['metadata']['title']
            resep_id_vdb = first_match['id']

            bahan_mentah_list = [item.strip() for item in ingredients_text.split('--') if item.strip()]
            konteks_bahan = "\n".join([f"- {bahan}" for bahan in bahan_mentah_list])
            
            # Gabungkan konteks ke dalam satu string besar
            combined_vdb_context += f"""
            --- START RESEP: {resep_title} ---
            NAMA MAKANAN ASLI: {food_name}
            ID VDB: {resep_id_vdb}
            BAHAN MENTAH:\n{konteks_bahan}
            --- END RESEP: {resep_title} ---
            """
            vdb_data_map[food_name] = {"resep_id_vdb": resep_id_vdb, "resep_title": resep_title}
        else:
            vdb_data_map[food_name] = None
    
    if not combined_vdb_context:
        return {name: None for name in food_names} # Tidak ada resep ditemukan sama sekali

    # 2. GENERATION: Satu Panggilan LLM untuk semua konteks
    
    SYSTEM_INSTRUCTION = (
        "Anda adalah asisten ahli nutrisi. Tugas Anda adalah memetakan semua resep yang diberikan "
        "ke format data terstruktur JSON. Berikan HANYA satu objek JSON di seluruh output Anda."
    )

    HUMAN_PROMPT = f"""
    Di bawah ini adalah daftar resep. Untuk setiap resep, ekstrak bahan-bahannya, konversi kuantitasnya 
    ke **gram/mililiter**, dan masukkan ke dalam struktur JSON tunggal. Gunakan 'NAMA MAKANAN ASLI' sebagai kunci utama.

    KONTEKS RESEP YANG DISEDIAKAN:
    {combined_vdb_context}

    FORMAT JSON YANG DIHARAPKAN:

    {{
        "hasil_analisis": [
            {{
                "food_name_asli": "Nama Makanan Asli dari Konteks",
                "resep_id_vdb": "ID VDB dari Konteks",
                "standar_porsi": 100, // Tentukan nilai standar porsi di sini
                "bahan_parsed": [
                    {{
                        "nama_bahan": "nama bahan",
                        "jumlah_standar": 0.0, // Kuantitas dalam gram/ml
                        "satuan_asli": "satuan asli",
                        "id_pangan": 0, // Placeholder, harus diisi setelah pemetaan ke DB
                        "berat_per_urt": 0.0 // Placeholder, harus diisi setelah pemetaan ke DB
                    }}
                ]
            }},
            // ... untuk resep berikutnya
        ]
    }}
    
    Berikan HANYA objek JSON, tanpa teks penjelasan apa pun.
    """

    response = await self.llm.ainvoke([SystemMessage(content=SYSTEM_INSTRUCTION), HumanMessage(content=HUMAN_PROMPT)])
    
    # 3. PARSING & PEMETAAN
    result = response.content
    match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
    json_str = match.group(1) if match else result
    
    final_results = {name: None for name in food_names}
    
    try:
        bulk_data = json.loads(json_str)
        # Peta hasil dari JSON massal ke format dictionary yang diharapkan
        for item in bulk_data.get("hasil_analisis", []):
            food_name = item.pop("food_name_asli", None)
            if food_name in final_results:
                final_results[food_name] = item # Simpan data resep yang sudah diparsing
                
    except json.JSONDecodeError as e:
        print(f":warning: Gagal parse JSON Massal: {e}")
    
    return final_results