from app.services.feature.ingredient_extract import IngredientExtract
from app.db.database import DBService
from app.schemas.request_model import FoodBatchRequest, FoodInput
from fastapi import Depends
from sqlmodel import Session
from typing import List
from pydantic import BaseModel
import asyncio 

    
db = DBService()

async def run_rag_test(request: FoodBatchRequest, session: Session):
    svc = IngredientExtract()
    
    # 1. Ekstrak nama makanan
    food_names_to_rag = [item.food_name.strip() for item in request.items]
    
    dummy_session = session 
    
    print(f"🚀 Memulai Bulk RAG untuk makanan: {food_names_to_rag}")
    
    # 2. Panggil fungsi RAG asynchronous
    results = await svc.build_augmented_message_bulk(food_names_to_rag, dummy_session)
    
    print("\n✅ Hasil Bulk RAG Berhasil Diterima:")
    print(results)
    return results

# Simulasi Setup Dependensi dan Request untuk Testing
class DummyRequestContainer:
    def __init__(self):
        self.items = [
            FoodInput(food_name="Telur balado", portion=2),
            FoodInput(food_name="rawon", portion=1),
            FoodInput(food_name="soto lamongan", portion=3),
        ]
        self.family_id = 101

# --- FUNGSI UTAMA UNTUK MENJALANKAN KODE ASYNC ---
async def main():
    # 1. Buat request object dummy
    request = FoodBatchRequest(family_id=101, items=DummyRequestContainer().items)
    
    dummy_session_object = None 
    
    # 3. Jalankan fungsi utama
    await run_rag_test(request, dummy_session_object)

if __name__ == "__main__":
    asyncio.run(main())