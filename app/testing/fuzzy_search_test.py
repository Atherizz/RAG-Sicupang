from app.db.models.food_ingredient import get_pangan_by_nama_fuzzy
from app.db.database import DBService

db = DBService()

if __name__ == "__main__":
    try:
        session_generator = db.get_session()
        session_obj = next(session_generator)
        print("✅ Session berhasil diinisialisasi.")

        result = get_pangan_by_nama_fuzzy("gurame", session=session_obj)
         
        if result:
            print(f"Hasil pencocokan: {result.nama_pangan}")
        else:
            print("Tidak ditemukan hasil yang cocok.")

    except Exception as e:
        print(f"❌ Terjadi kesalahan saat testing: {e}")
        if 'session_generator' in locals():
            try:
                session_generator.close()
            except Exception:
                pass
