import re

food_name = "Nasi Sate Ayam Madura"
query_base = re.sub(r'\b(nasi|ketupat|lontong|)\b', '', food_name, flags=re.IGNORECASE).strip()
print(query_base)