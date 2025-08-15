from fastapi import APIRouter
from app.services.feature.ingredient_recommend import IngredientRecommend
from pydantic import BaseModel

router = APIRouter()
ingredientRecommend = IngredientRecommend()

class IngredientInput(BaseModel):
    jumlah_keluarga: int
    budget: int
    alergi: str
    

@router.post("/ingredient-recommend")
def get_recommendation(input: IngredientInput):
    result = ingredientRecommend.get_recommendation(input.jumlah_keluarga, input.budget, input.alergi)
    return {"response": result}

