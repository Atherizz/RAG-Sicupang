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
from app.db.models.food_recipe import get_resep_by_nama, InsertFoodRecipe, FoodRecipe
from app.db.models.food_ingredient import get_pangan_by_nama_fuzzy
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.schemas.request_model import FoodInput
from starlette.concurrency import run_in_threadpool
from decimal import Decimal


class IngredientExtract:
    def __init__(self, model="gemini-2.5-flash"):
        self.api_key = os.getenv("OPENAI_API_KEY")
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

    async def _process_and_insert_ingredients_from_cache(
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

        # membagi porsi inputan dengan standar porsi yang ada pada suatu resep
        faktor_skala = portion_input / std_portion
        temp_results = []

        for bahan in bahan_parsed:
            # mengambil json pada json bahan_parsed
            nama_bahan = bahan.get("nama_bahan", 0)
            berat_konsumsi = bahan.get("jumlah_standar", 0) * faktor_skala
            berat_per_urt = bahan.get("berat_per_urt", 0) 
            id_pangan = bahan.get("id_pangan", None)

            if berat_per_urt == 0 or id_pangan is None:
                print(f"⚠️ Error: Data porsi atau ID Pangan bahan tidak lengkap untuk {food_name}.")
                continue

            # perhitungan urt
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
                        "food_name" : food_name,
                        "ingredient_name": nama_bahan,
                        "id_pangan": inserted_record.id_pangan,
                        "urt": float(inserted_record.urt),
                        "status": "Sukses Insert"
                    })
            except Exception as e:
                print(f"❌ Gagal insert data {id_pangan} untuk {food_name}: {e}")
                
        return temp_results
    
    async def _process_and_insert_ingredients_from_rag(
        self, 
        food_name: str, 
        portion_input: float, 
        resep_data: Dict[str, Any], 
        id_keluarga: int, 
        today: date, 
        session: Session
    ) -> List[Dict[str, Any]]:
       
        bahan_parsed: List[Dict[str, Any]] = resep_data.get('bahan_parsed', [])
        resep_id_vdb = resep_data['resep_id_vdb']
        std_portion = resep_data['standar_porsi']
        
        if std_portion <= 0:
            print(f"⚠️ Error: Estimasi porsi standar {food_name} adalah nol setelah RAG.")
            return []

        faktor_skala = portion_input / std_portion
        
        uraian_bahan_json: Dict[str, Any] = {
        "resep_id_vdb": resep_id_vdb,
        "standar_porsi": std_portion,
        "bahan_parsed": []
        }
        
        temp_results = [] 
        
        for item in bahan_parsed:
            nama_bahan = item['nama_bahan']
            jumlah_standar = item['jumlah_standar']
            satuan_konversi = item['satuan_konversi']
            
            bahan_entry = await run_in_threadpool(
                get_pangan_by_nama_fuzzy,
                nama_bahan,
                session
            )
            
            if bahan_entry:
                print(f"✅ Ditemukan pada id_pangan: {bahan_entry.id_pangan}")
                
                berat_konsumsi = jumlah_standar * faktor_skala
                berat_per_urt = getattr(bahan_entry, 'referensi_gram_berat', 0)
                id_pangan = bahan_entry.id_pangan
                
                if berat_per_urt == 0 or id_pangan is None:
                    print(f"⚠️ Error: Data porsi atau ID Pangan bahan tidak lengkap untuk {food_name}.")
                    continue

                urt = berat_konsumsi / berat_per_urt
                urt_value = Decimal(str(urt)).quantize(Decimal('0.01'))
                
                bahan_enriched = {
                "nama_bahan": nama_bahan,
                "jumlah_standar": jumlah_standar,
                "satuan_konversi": satuan_konversi,
                "id_pangan": id_pangan,
                "berat_per_urt": berat_per_urt 
                }
                
                uraian_bahan_json['bahan_parsed'].append(bahan_enriched) 
                
                new_pangan_keluarga = HouseholdFood(
                id_keluarga=id_keluarga,
                id_pangan=id_pangan,
                urt=urt_value,
                tanggal=today
                )
        
                
                try:
                    inserted_record = await run_in_threadpool(
                        InsertHouseholdFood,
                        new_pangan_keluarga,
                        session
                    )
                    
                    temp_results.append({
                        "food_name" : food_name,
                        "ingredient_name": bahan_entry.nama_pangan,
                        "id_pangan": inserted_record.id_pangan,
                        "urt": float(inserted_record.urt),
                        "status": "Sukses Insert"
                    })
                except Exception as e:
                    print(f"❌ Gagal insert data {id_pangan} untuk {food_name}: {e}")
                    
        recipe_cache = FoodRecipe(
            nama_olahan=food_name,
            id_resep_vektor_db=resep_id_vdb,
            uraian_bahan=uraian_bahan_json,
            standar_porsi=std_portion,
        )
                    
        await run_in_threadpool(
            InsertFoodRecipe,
            recipe_cache,
            session
        )
        
        return temp_results
         
    async def searchingFood(self, items: List[FoodInput], id_keluarga: int, session: Session):
        results = []
        uncached_items: List[FoodInput] = [] 
        today = date.today()

        for item in items:
            food_name = item.food_name.strip()
            portion_input = item.portion

            cache_entry = await run_in_threadpool(
                get_resep_by_nama,
                food_name,
                session
            )

            if cache_entry:
                print(f"✅ Ditemukan di cache: {food_name}")
                
                bahan_parsed: List[Dict[str, Any]] = cache_entry.uraian_bahan
                
                cache_insert_results = await self._process_and_insert_ingredients_from_cache(
                    food_name,
                    portion_input,
                    bahan_parsed,
                    id_keluarga,
                    today,
                    session    
                    )
                

                results.append(cache_insert_results)
                        

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
                    
                    rag_insert_result = await self._process_and_insert_ingredients_from_rag(
                    food_name=food_name,
                    portion_input=portion_input,
                    resep_data=rag_data_for_food,
                    id_keluarga=id_keluarga,
                    today=today,
                    session=session
                )
            
                    results.append(rag_insert_result)
                    
                else:
                    print(f"❌ Gagal mendapatkan hasil RAG untuk: {food_name}")

        return results

    async def build_augmented_message_bulk(self, food_names: List[str], session: Session, k: int = 1) -> Dict[str, Optional[Dict[str, Any]]]:
        combined_vdb_context = ""
        vdb_data_map = {} 

        for food_name in food_names:
            
            query_base = re.sub(r'\b(nasi|ketupat|lontong|)\b', '', food_name, flags=re.IGNORECASE).strip()
            
            if not query_base or len(query_base) < 3:
                query_vdb = food_name
            else:
                query_vdb = query_base
            
            query_vector = await run_in_threadpool(self.embed_model.embed_query, query_vdb)
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
            return {name: None for name in food_names} 

        
        SYSTEM_INSTRUCTION = (
    "Anda adalah asisten ahli nutrisi. Tugas Anda adalah memetakan semua resep yang diberikan "
    "ke format data terstruktur JSON. Berikan HANYA satu objek JSON di seluruh output Anda. "
                
    "ATURAN PENENTUAN PORSI KRITIS: Nilai 'standar_porsi' harus merepresentasikan **TOTAL JUMLAH PORSI** (misal 4.0 porsi) "
    "yang dihasilkan resep. Infer nilai ini secara logis berdasarkan **kuantitas total bahan utama** (misal: total 1 kg daging/ayam biasanya menghasilkan 4.0 porsi, 500 gram ayam menghasilkan 2.0 porsi). Jika sulit diinfer, gunakan nilai default 1.0. "
    "Semua nilai 'jumlah_standar' di 'bahan_parsed' HARUS TOTAL BERAT BAHAN yang diperlukan untuk membuat "
    "seluruh resep yang menghasilkan 'standar_porsi' tersebut. "
                
    "ATURAN KONVERSI KRITIS: Konversi kuantitas bahan sebagai berikut: "
    "1. Satuan berat massal (cth: kg, ons, gr) HARUS dikonversi ke **gram (g)**. "
    "2. Satuan volume (cth: liter, ml) HARUS dikonversi ke **mililiter (ml)**. "
    "3. Satuan hitungan atau non-standar (cth: siung, biji, batang, secukupnya) HARUS dipertahankan sebagai satuan konversi. "
    "4. Kasus Khusus: Jika satuan asli adalah 'piring' (biasanya untuk Nasi), konversi nilainya menjadi 200.0 gram. "

    "ATURAN ESTIMASI KUANTITAS BAHAN UTAMA (NON-STANDAR): "
    "JIKA bahan utama (Daging, Ikan, Ayam, Tahu, Tempe, Santan/Kara) dicantumkan TANPA kuantitas berat terukur (misal hanya '1 ekor lele' atau '1 bungkus kara'), "
    "LLM HARUS mengestimasi kuantitas standarnya dan mengonversinya ke **gram** untuk 'jumlah_standar', dan 'satuan_konversi' diisi dengan 'g'. "
    "Contoh Estimasi Dasar: 1 ekor ikan/ayam sedang = 200.0 g; 1 bungkus santan/kara = 65.0 g. ESTIMASI INI WAJIB dilakukan untuk menghindari nilai 0.0 gram."
    
    "ATURAN ESTIMASI BUMBU ESENSIAL: "
    "Untuk bumbu bubuk dan zat aditif yang dicantumkan sebagai 'secukupnya' atau tanpa kuantitas terukur (cth: Garam, Merica, Kaldu Bubuk, Ketumbar), LLM HARUS mengestimasi kuantitas minimal **2.0 gram** dan mengonversinya ke 'g'. ESTIMASI INI WAJIB dilakukan untuk menghindari nilai 0.0 gram."
    )

        HUMAN_PROMPT = f"""
        Di bawah ini adalah daftar resep. Untuk setiap resep, ekstrak bahan-bahannya, konversi kuantitasnya 
        ke satuan standar, dan masukkan ke dalam struktur JSON tunggal. Gunakan 'NAMA MAKANAN ASLI' sebagai kunci utama.
        
        INPUT MAKANAN:
        {food_name}

        KONTEKS RESEP YANG DISEDIAKAN:
        {combined_vdb_context}

        FORMAT JSON YANG DIHARAPKAN:

        {{
            "hasil_analisis": [
                {{
                    "food_name_asli": "[AMBIL NAMA ASLI DARI INPUT MAKANAN DI ATAS]",
                    "resep_id_vdb": "ID VDB dari Konteks",
                    "standar_porsi": dari standarisasi berdasarkan banyaknya kuantitas bahan, 
                    "bahan_parsed": [
                        {{
                            "nama_bahan": "nama bahan yang diekstrak",
                            "jumlah_standar": 0.0
                            "satuan_konversi": "satuan asli (contoh: kg, siung, sdm)"
                        }}
                    ]
                }}
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
            for item in bulk_data.get("hasil_analisis", []):
                food_name_asli = item.pop("food_name_asli", None)
                if food_name_asli and 'bahan_parsed' in item:
                    is_carbo_dish = re.search(r'\b(nasi|ketupat|lontong)\b', food_name_asli, flags=re.IGNORECASE)
                    
                    has_main_carbo = any(
                        re.search(r'\b(nasi|beras|ketupat|lontong|ubi|kentang)\b', bahan['nama_bahan'], flags=re.IGNORECASE)
                        for bahan in item['bahan_parsed']
                    )
                    
                    if is_carbo_dish and not has_main_carbo:
                        print(f"Adding Nasi fallback to: {food_name_asli}")
                    
                        nasi_fallback = {
                        "nama_bahan": "Beras Putih Mentah", 
                        "jumlah_standar": 200.0, 
                        "satuan_konversi": "g",
                        }
                    
                        item['bahan_parsed'].insert(0, nasi_fallback)
                    
                    if food_name_asli in final_results:
                        final_results[food_name_asli] = item

                    
        except json.JSONDecodeError as e:
            print(f":warning: Gagal parse JSON Massal: {e}")
        
        return final_results