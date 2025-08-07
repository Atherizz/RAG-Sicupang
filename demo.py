import os
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

load_dotenv()
apiKey = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.2
)

def load_and_prepare_price_context(file_path: str, province: str) -> str:
    print("--- Membaca dan memproses file CSV ---")
    try:
        df = pd.read_csv(file_path)

        df_province = df[df['Nama Provinsi'].str.strip().str.lower() == province.lower()].copy()
        if df_province.empty:
            return "Data harga untuk provinsi yang diminta tidak ditemukan."

        df_province['Harga'] = df_province['Harga'].astype(str)
        df_province['Harga'] = df_province['Harga'].str.replace("Rp", "", regex=False)
        df_province['Harga'] = df_province['Harga'].str.replace(",", "", regex=False)
        df_province['Harga'] = df_province['Harga'].str.strip()
        df_province['Harga'] = pd.to_numeric(df_province['Harga'], errors='coerce')  
        df_province = df_province.dropna(subset=['Harga']) 
        df_province['Harga'] = df_province['Harga'].astype(int)

        df_province = df_province.sort_values(by=['Tahun', 'Bulan'], ascending=[False, False])
        latest_prices = df_province.drop_duplicates(subset=['Komoditas'], keep='first')

        price_list = [f"{row['Komoditas']}: Rp{row['Harga']}" for _, row in latest_prices.iterrows()]
        print("--- Konteks harga berhasil dibuat dan disimpan di memori. ---")
        return ", ".join(price_list)

    except FileNotFoundError:
        return "File data harga tidak ditemukan."
    except Exception as e:
        print(f"{e}")
        return "Gagal memproses data harga."

price_context = load_and_prepare_price_context('data/dataset.csv', 'JAWA TIMUR')

prompt_template_recommendation = PromptTemplate(
    input_variables=['budget', 'price_context'],
    template="""
Anda adalah asisten gizi. Buat rencana bahan makanan bergizi (karbohidrat, protein, sayur, buah, pelengkap) untuk 4 orang selama 1 bulan, dengan budget Rp{budget}.
Gunakan data harga Jawa Timur berikut sebagai acuan: {price_context} dan pertimbangkan konsumsi kalori harian manusia, jangan yang berlebihan.
Balas hanya dengan JSON valid. Struktur:
- Object luar: "bahan_makanan"
- Di dalamnya: "karbohidrat", "protein", "sayuran", "buah", "pelengkap"
- Tiap item: "nama", "jumlah", "harga" (integer), "manfaat"
- Tambahkan: "total_perkiraan_pengeluaran" di akhir
Jangan sertakan teks di luar JSON.
"""
)

chain = prompt_template_recommendation | llm

def get_recommendation(budget: str):
    
    print(f"\n🧠 Membuat rekomendasi untuk budget: Rp{budget}...")
    if "tidak ditemukan" in price_context or "Gagal" in price_context:
        print("🚫 Gagal membuat rekomendasi karena masalah data harga.")
        return

    result = chain.invoke({
        "budget": budget,
        "price_context": price_context
    })

    print("✅ Rekomendasi berhasil dibuat:")
    print(result.content)

print(price_context)

get_recommendation("20000000")

