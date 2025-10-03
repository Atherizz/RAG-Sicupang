from sqlmodel import create_engine, Session, SQLModel
from langchain_community.utilities import SQLDatabase

from dotenv import load_dotenv
import os

load_dotenv()

class DBService:
    def __init__(self):
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")
        self.mysql_url = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        self.engine = create_engine(self.mysql_url, echo=True)
        
    def get_sql_database(self):
        db = SQLDatabase.from_uri(self.mysql_url)
        return db
    
    def get_session(self):
        with Session(self.engine) as session:
            yield session
            
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)
        
