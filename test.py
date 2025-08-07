from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import pandas as pd


df = pd.read_csv('data/dataset.csv')
print(df.head())


load_dotenv()
apiKey = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.6
    )


# prompt_template_recommendation = PromptTemplate(
#     input_variables= ['budget'],
#     template="""
# Buat daftar bahan makanan bergizi (karbo, protein, sayur, buah) untuk 4 orang, untuk 1 bulan, dengan budget Rp{budget}.
# Kelompokkan dalam format JSON dengan  paling luar bahan_makanan, lalu dilanjutkan karbohidrat, protein, sayuran, buah, pelengkap
# Setiap item berisi: nama, jumlah, harga (Rp), manfaat singkat. Tambahkan total_pengeluaran di akhir, tidak perlu catatan di akhir hanya berikan format json
# """
# )

# chain = LLMChain(llm=llm, prompt=prompt_template_recommendation)
# result = chain.run("1 juta")
# print(result)


response = llm.invoke("""
Anda adalah asisten gizi. Buat rencana bahan makanan bergizi (karbohidrat, protein, sayur, buah, pelengkap) untuk 4 orang selama 1 bulan, dengan budget Rp.1000.000.
Gunakan data harga bahan pokok di Jawa Timur sebagai patokan dan pertimbangkan konsumsi kalori harian manusia, jangan yang berlebihan.
Balas hanya dengan JSON valid. Struktur:
- Object luar: "bahan_makanan"
- Di dalamnya: "karbohidrat", "protein", "sayuran", "buah", "pelengkap"
- Tiap item: "nama", "jumlah", "harga" (integer), "manfaat"
- Tambahkan: "total_perkiraan_pengeluaran" di akhir
Jangan sertakan teks di luar JSON.
""")
print(response.content)

# response = prompt_template_recommendation.format(budget="3000000")