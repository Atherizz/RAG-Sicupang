from fastapi import FastAPI
from app.routes import ingredient_extract
from app.db.models.family import Family 
from app.db.models.household_food import HouseholdFood
from app.db.models.food_ingredient import FoodIngredient
from app.db.models.food_recipe import FoodRecipe


app = FastAPI(title="Emolog API")

app.include_router(ingredient_extract.router, prefix="/api")