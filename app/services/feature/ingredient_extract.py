import os
from typing import List
import json
from sqlmodel import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from app.db.database import get_sql_database
from app.db.models.household_food import InsertHouseholdFood
from app.db.models.recipe_cache import GetRecipeCacheByName
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.routes.ingredient_extract import FoodInput
from starlette.concurrency import run_in_threadpool
from typing import List, Dict, Any
from decimal import Decimal


class IngredientExtract:
    def __init__(self, model="gemini-1.5-flash-latest"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key tidak ditemukan")

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0.4
        )
        
        self.index_name = "sicupang-rag-small"
        self.namespace = "recipes"
        self.db = get_sql_database()
        
        self.embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorStore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embed_model,
            text_key="ingredients",
            namespace="recipes"
        )

    async def searchingFood(self, items: List[FoodInput], session: Session):
        
        results = []
        for item in items:
            # mengambil data olahan makanan
            food_name = item.food_name.strip()
            portion_input = item.portion

            # memeriksa cache olahan makanan
            cache_entry = await run_in_threadpool(
                GetRecipeCacheByName, 
                food_name, 
                session
            )
            
            if cache_entry:
                print(f"✅ Ditemukan di cache: {food_name}")
                # parsing json pada record recipe_cache
                bahan_parsed: List[Dict[str, Any]] = json.loads(cache_entry.bahan_parsed)
                std_portion = cache_entry.standar_porsi
                
                # pembagian skala
                if std_portion > 0:
                    faktor_skala = portion_input / std_portion
                else:
                    print(f"⚠️ Error: Estimasi porsi standar {food_name} adalah nol.")
                    continue
                
                # perhitungan urt
                for bahan in bahan_parsed:
                    berat_konsumsi = bahan["jumlah_standar"] * faktor_skala
                    urt = berat_konsumsi / bahan["berat_per_urt"]
                    urt_value = Decimal(urt)
                    
                    
            else:
                print(f"❌ Tidak ditemukan di cache: {food_name}. ")
                
                
        return results