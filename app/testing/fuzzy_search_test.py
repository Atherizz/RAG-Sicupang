import logging
from typing import List, Dict, Any, Optional, Tuple
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from contextlib import contextmanager

# --- MOCK COMPONENTS (Untuk membuat kode ini runnable tanpa SQLModel/SQLAlchemy) ---

# Mock Model: Ganti dengan model FoodIngredient Anda yang sebenarnya
class MockFoodIngredient:
    def __init__(self, nama_pangan, id_pangan=None, referensi_gram_berat=None):
        self.nama_pangan = nama_pangan
        self.id_pangan = id_pangan or hash(nama_pangan) % 1000 
        self.referensi_gram_berat = referensi_gram_berat or 100

    @classmethod
    def get_all_names(cls):
        """Simulasi query SELECT pangan.nama_pangan FROM pangan"""
        return [data['nama_pangan'] for data in MOCK_FOOD_DATA]

    @classmethod
    def get_by_name(cls, name: str):
        """Simulasi query SELECT * FROM pangan WHERE nama_pangan == name"""
        for data in MOCK_FOOD_DATA:
            if data['nama_pangan'] == name:
                # Mengembalikan instance model FoodIngredient (mock)
                return cls(**data) 
        return None

# Mock Database Data
MOCK_FOOD_DATA = [
    {"nama_pangan": "Bawang Merah", "id_pangan": 310},
    {"nama_pangan": "Bawang Putih", "id_pangan": 311},
    {"nama_pangan": "Cabai Rawit Merah", "id_pangan": 401},
    {"nama_pangan": "Kentang", "id_pangan": 105},
    {"nama_pangan": "Tepung Terigu", "id_pangan": 502},
    {"nama_pangan": "Telur Ayam", "id_pangan": 205},
    {"nama_pangan": "Gula Pasir", "id_pangan": 601},
]

# Mock Database Session (Hanya untuk memenuhi signature fungsi)
@contextmanager
def MockSession():
    yield None # Dalam test ini, kita tidak menggunakan objek session

# Mock SQLAlchemy Select (Hanya untuk memenuhi signature fungsi)
def MockSelect(model):
    return model # Kita hanya perlu tahu model mana yang diakses

# Ganti dengan nilai threshold Anda yang sebenarnya
FUZZY_SCORE_THRESHOLD = 80 
FoodIngredient = MockFoodIngredient
Session = MockSession
select = MockSelect

# --- FUZZY SEARCH FUNCTION ---

def get_pangan_by_nama_fuzzy(nama_pangan: str, session: Any) -> Optional[FoodIngredient]:
    """
    Mencari FoodIngredient yang nama pangannya paling mirip menggunakan fuzzy matching.
    """
    
    # 1. Ambil semua nama pangan yang ada (Simulasi DB Query)
    # Catatan: Kita abaikan parameter 'session' dan 'select' di mock ini
    all_pangan_names: List[str] = FoodIngredient.get_all_names()
    
    if not all_pangan_names:
        return None

    # 2. Lakukan Fuzzy Matching
    best_match: Optional[Tuple[str, int]] = process.extractOne(
        nama_pangan, 
        all_pangan_names, 
        scorer=fuzz.ratio
    )
    
    if best_match is None:
        return None

    best_name, score = best_match
    
    # 3. Cek ambang batas (Threshold)
    if score >= FUZZY_SCORE_THRESHOLD:
        # Jika cocok, ambil objek FoodIngredient lengkap (Simulasi DB Query)
        return FoodIngredient.get_by_name(best_name)
    else:
        return None

# --- MAIN TEST BLOCK ---

def run_tests():
    print("--- Menjalankan Fuzzy Search Tests ---")
    
    test_cases = [
        # Input yang mirip (typo ringan) -> Harus cocok (Target: Bawang Merah)
        ("bawan mera", "Bawang Merah"),
        
        # Input typo di tengah kata -> Harus cocok (Target: Telur Ayam)
        ("telor ayem", "Telur Ayam"),
        
        # Input yang terlalu berbeda/score di bawah 80 -> Harus gagal
        ("knteng", None), 
        
        # Input mirip tapi ada huruf tambahan -> Harus cocok (Target: Gula Pasir)
        ("Gula passir", "Gula Pasir"),
        
        # Input yang cocok panjang -> Harus cocok (Target: Cabai Rawit Merah)
        ("cabai rawit meraj", "Cabai Rawit Merah"),
    ]

    for input_name, expected_name in test_cases:
        with MockSession() as session:
            found_item = get_pangan_by_nama_fuzzy(input_name, session)
            
            result_match = None
            if found_item:
                result_match = found_item.nama_pangan
                
            status = "✅ SUKSES" if result_match == expected_name else "❌ GAGAL"
            
            # Cari skor kemiripan untuk ditampilkan (untuk debugging)
            if expected_name:
                # Jika ada target yang diharapkan, hitung skornya
                score = fuzz.ratio(input_name, expected_name)
            else:
                # Jika target None (diharapkan gagal), cari skor terbaik yang ditemukan
                best_match_info = process.extractOne(input_name, MockFoodIngredient.get_all_names(), scorer=fuzz.ratio)
                score = best_match_info[1] if best_match_info else 0
            
            
            print(f"\n{status} | Input: '{input_name}'")
            print(f"       Hasil Cocok: {result_match}")
            print(f"       Target: {expected_name}")
            print(f"       Skor Fuzzy: {score} (Threshold: {FUZZY_SCORE_THRESHOLD})")


if __name__ == "__main__":
    # Matikan logging dari library yang mungkin mengganggu
    logging.getLogger('fuzzywuzzy').setLevel(logging.WARNING) 
    
    run_tests()
