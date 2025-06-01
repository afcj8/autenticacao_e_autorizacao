"""Conexão com o banco de dados"""

from sqlmodel import Session, SQLModel , create_engine
from fastapi import Depends

sqlite_file_name = "auth.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    """Cria as tabelas, se não existirem."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Cria uma sessão com o banco de dados."""
    with Session(engine) as session:
        yield session
        
SessionDep = Depends(get_session)