from app.db.database import get_sql_database
from sqlalchemy import text
import json

db = get_sql_database()

sql_query = """
SELECT JSON_ARRAYAGG(
         JSON_OBJECT(
           'nama', nama_pangan,
           'harga', CAST(harga_satuan AS DECIMAL(12,2))
         )
       ) AS price_context_json
FROM (
  WITH hp_rank AS (
    SELECT
      id_pangan,
      harga_satuan,
      tanggal,
      ROW_NUMBER() OVER (
        PARTITION BY id_pangan
        ORDER BY tanggal DESC, id_harga DESC
      ) AS rn
    FROM harga_pangan
  )
  SELECT p.nama_pangan, h.harga_satuan
  FROM pangan p
  JOIN hp_rank h
    ON h.id_pangan = p.id_pangan AND h.rn = 1
  ORDER BY p.nama_pangan
) q;
"""

# Ambil engine dari objek LangChain SQLDatabase (nama atribut bisa "engine" atau "_engine")
engine = getattr(db, "engine", None) or getattr(db, "_engine", None)
if engine is None:
    raise RuntimeError("SQLAlchemy engine tidak ditemukan dari SQLDatabase")

with engine.connect() as conn:
    json_str = conn.execute(text(sql_query)).scalar()
    if not json_str:
        json_str = "[]"

data = json.loads(json_str)
# Parse dan tampilkan FULL tanpa kepotong
# print(f"Total item: {len(data)}")
print(data)
# print(json.dumps(data, indent=2, ensure_ascii=False))
