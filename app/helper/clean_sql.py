import re, json



def parse_route_safely(raw: str) -> str:
    # Ambil objek {...} pertama (menghindari ```json ... ``` dan embel-embel lain)
    m = re.search(r"\{.*?\}", raw, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            route = str(data.get("route", "")).strip().lower()
            if route in {"sql", "rag", "both"}:
                return route
        except Exception:
            pass
    # Heuristik darurat kalau JSON gagal tapi kata kunci kebaca
    low = raw.lower()
    if '"rag"' in low or " route " in low and "rag" in low:
        return "rag"
    if '"both"' in low or "both" in low:
        return "both"
    if '"sql"' in low or "sql" in low:
        return "sql"
    # Default paling aman (pilih yang minim side-effect)
    return "rag"  # ← lebih aman daripada "sql" supaya gak manggil extract_select tanpa perlu

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