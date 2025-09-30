import os
import logging
from dotenv import load_dotenv
from datasets import load_dataset
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from load_pinecone import loadPinecone
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
pineconeApiKey = os.getenv("PINECONE_API_KEY")
openAIApiKey = os.getenv("OPENAI_API_KEY")

if not pineconeApiKey or not openAIApiKey:
    raise ValueError("Missing required API keys in environment variables")

try:
    ds = load_dataset(
        "csv",
        data_files={"train": "datasets/*.csv"},
        delimiter=",",
        encoding="utf-8"
    )["train"]
    logger.info(f"Dataset loaded successfully. Total rows: {len(ds)}")
    logger.info(f"Available columns: {ds.column_names}")
except Exception as e:
    logger.error(f"Failed to load dataset: {e}")
    raise

TITLE_COL = "Title"
ING_COL = "Ingredients"
STEPS_COL = "Steps"
URL_COL = "URL"

missing = [c for c in (TITLE_COL, ING_COL) if c not in ds.column_names]
if missing:
    raise KeyError(f"Required columns not found in CSV: {missing}. Available columns: {ds.column_names}")

index_name = "sicupang-rag-small"
model_name = "text-embedding-3-small"
dimension = 1536
NAMESPACE = "recipes"

try:
    pc = Pinecone(api_key=pineconeApiKey)
    index = loadPinecone(index_name, dimension)
    embed = OpenAIEmbeddings(model=model_name, openai_api_key=openAIApiKey)
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

batch_size = 100
batch_ids, batch_texts, batch_metas = [], [], []
processed_count = 0
error_count = 0

def flush_batch():
    global processed_count, error_count

    if not batch_texts:
        return

    try:
        logger.info(f"Generating embeddings for batch of {len(batch_texts)} items...")
        vectors = embed.embed_documents(batch_texts)
        upsert_data = list(zip(batch_ids, vectors, batch_metas))
        logger.info(f"Upserting batch to Pinecone namespace '{NAMESPACE}'...")
        index.upsert(vectors=upsert_data, namespace=NAMESPACE)
        processed_count += len(batch_texts)
        logger.info(f"✅ Batch upserted successfully. Total processed: {processed_count}")
    except Exception as e:
        error_count += len(batch_texts)
        logger.error(f"❌ Failed to upsert batch: {e}")
        raise
    finally:
        batch_ids.clear()
        batch_texts.clear()
        batch_metas.clear()

def clean_text(text):
    if text is None:
        return ""
    if isinstance(text, list):
        text = ", ".join(str(x).strip() for x in text if x)
    return str(text).strip()

logger.info("Starting dataset processing...")

for i, row in enumerate(ds):
    try:
        title = clean_text(row.get(TITLE_COL))
        ingredients = clean_text(row.get(ING_COL))
        steps = clean_text(row.get(STEPS_COL, "")) if STEPS_COL in ds.column_names else ""
        url = clean_text(row.get(URL_COL, "")) if URL_COL in ds.column_names else ""

        if not title and not ingredients:
            logger.warning(f"Skipping row {i}: both title and ingredients are empty")
            continue

        content_parts = []
        if title:
            content_parts.append(f"Title: {title}")
        if ingredients:
            content_parts.append(f"Ingredients: {ingredients}")
        if steps:
            content_parts.append(f"Steps: {steps}")

        content = "\n".join(content_parts)

        metadata = {
            "title": title[:256] if title else "",
            "ingredients": ingredients[:4000] if ingredients else ""
        }

        batch_ids.append(f"recipe_{i:08d}")
        batch_texts.append(content)
        batch_metas.append(metadata)

        if len(batch_texts) >= batch_size:
            flush_batch()
            time.sleep(0.1)
    except Exception as e:
        logger.error(f"Error processing row {i}: {e}")
        error_count += 1
        continue

flush_batch()

logger.info("=" * 50)
logger.info("UPSERT SUMMARY")
logger.info("=" * 50)
logger.info(f"✅ Total rows processed successfully: {processed_count}")
logger.info(f"❌ Total errors: {error_count}")
logger.info(f"📊 Total dataset rows: {len(ds)}")
logger.info(f"🎯 Namespace: '{NAMESPACE}'")
logger.info(f"🔍 Index: '{index_name}'")
logger.info("=" * 50)

if error_count > 0:
    logger.warning(f"⚠️  {error_count} rows had errors during processing")

print(f"✅ Upsert completed! Processed {processed_count} recipes to namespace '{NAMESPACE}'")