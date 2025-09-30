from fastapi import APIRouter
from app.services.feature.ingredient_extract import IngredientExtract
from pydantic import BaseModel
from typing import List

router = APIRouter()

class FoodInput(BaseModel):
    food_name: str
    portion: int
    
class FoodBatchRequest(BaseModel):
    family_id : int
    items: List[FoodInput]
    
@router.post("/ingredient-extract")
async def ingredient_extract(request: FoodBatchRequest):
    svc = IngredientExtract()
    results = await svc.extract_batch(request.family_id, request.items) 
    return {"response": results}