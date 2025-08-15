import re

def extract_select(sql: str) -> str:
    sql = re.sub(r"^```[\w-]*\s*", "", sql.strip(), flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql.strip())
    
    m = re.search(r"\bSELECT\b.*", sql, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError(f"Tidak ditemukan SELECT di output LLM:\n{sql}")
    sel = m.group(0).strip()

    if ";" in sel:
        sel = sel.split(";", 1)[0] + ";"
    return sel

def sanitize_sql(sql: str, limit_default: int = 200) -> str:
    sql = re.sub(r"\s+", " ", sql).strip()
    if not re.match(r"^\s*SELECT\b", sql, flags=re.IGNORECASE):
        raise ValueError(f"Query bukan SELECT:\n{sql}")

    if re.search(r"\blimit\b\s+\d+", sql, flags=re.IGNORECASE):
        sql = re.sub(r"\blimit\b\s+\d+", f"LIMIT {limit_default}", sql, flags=re.IGNORECASE)
    elif not re.search(r"\bgroup\s+by\b", sql, flags=re.IGNORECASE):

        sql = sql.rstrip(";") + f" LIMIT {limit_default};"
    else:
        sql = sql.rstrip(";") + ";"
    return sql