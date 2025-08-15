from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from app.db.database import get_sql_database
from app.helper.clean_sql import extract_select, sanitize_sql
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class Chatbot:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.4
        )
        
        self.db = get_sql_database()

        self.write_query = create_sql_query_chain(self.llm, self.db)

        self.prompt_template = PromptTemplate(
            input_variables=['question','query','result'],
            template=(
                "Kamu adalah SICUPANG AI, asisten Dinas Ketahanan Pangan Kab. Malang.\n"
                "Tugasmu: menjawab pertanyaan dengan data hasil SQL secara ringkas, akurat, dan actionable. Beri saran atau opini jika memang ditanyakan"
                "(membantu pengambilan keputusan pemerintah). Jangan mengarang di luar hasil SQL/dokumen resmi.\n"
                "# Input\n"
                "Info tambahan: mata uang pakai Rupiah (Rp.)"
                "Pertanyaan Pengguna: {question}\n"
                "SQL Query yang dipakai: {query}\n"
                "Hasil SQL (baris/kolom mentah): {result}"
            )
        )

        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def ask(self, question: str):

        sql_raw = self.write_query.invoke({"question": question})
        sql_sel = extract_select(sql_raw)
        sql_clean = sanitize_sql(sql_sel)
        
        query_result = self.db.run(sql_clean)

        final_answer = self.chain.invoke({
            "question": question,
            "query": sql_clean,
            "result": query_result
        })
        return final_answer

# if __name__ == "__main__":
#     bot = Chatbot()
#     q = "jenis pangan apa yang dikonsumsi paling banyak di kecamatan poncokusumo?"
#     try:
#         out = bot.ask(q)
#         print(":white_check_mark: RESULT:")
#         print(out)
#     except Exception as e:
#         print(":x: ERROR:", e)
