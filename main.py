from fastapi import FastAPI
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("Starting application...")

try:
    from app.routes import food_recommendation, chatbot, ingredient_extract
    logger.info("Routes imported successfully")
except Exception as e:
    logger.error(f"Error importing routes: {e}", exc_info=True)
    raise

try:
    from app.db.models.family import Family  
    from app.db.models.household_food import HouseholdFood
    from app.db.models.food_ingredient import FoodIngredient
    from app.db.models.food_recipe import FoodRecipe
    logger.info("Models imported successfully")
except Exception as e:
    logger.error(f"Error importing models: {e}", exc_info=True)
    raise

app = FastAPI(title="Sicupang API")

logger.info("FastAPI app created")

app.include_router(food_recommendation.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")
app.include_router(ingredient_extract.router, prefix="/api")

logger.info("Routers registered successfully")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}