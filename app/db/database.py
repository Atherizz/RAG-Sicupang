from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

class DBService:
    def __init__(self):
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.DB_NAME = os.getenv("DB_NAME")
        
        self.INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
        
        if self.INSTANCE_CONNECTION_NAME:
            self.mysql_url = (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@/{self.DB_NAME}?unix_socket=/cloudsql/{self.INSTANCE_CONNECTION_NAME}"
            )
        else:
            self.DB_HOST = os.getenv("DB_HOST")
            self.DB_PORT = os.getenv("DB_PORT")
            self.mysql_url = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        self.engine = create_engine(self.mysql_url, echo=False)
        
    def get_session(self):
        with Session(self.engine) as session:
            yield session
            
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)