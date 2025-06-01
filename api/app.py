from fastapi import FastAPI
from api.database import create_db_and_tables
from .routes import main_router

def lifespan(app: FastAPI):
    """Função de ciclo de vida da aplicação."""
    
    # Executa na inicialização da aplicação
    create_db_and_tables()
    yield  # Separa a inicialização do encerramento
    # Executa no encerramento da aplicação
    pass

app = FastAPI(
    title="API de Autenticação e Autorização",
    version="0.1.0",
    description="API para gerenciamento de usuários, grupos e permissões, com autenticação e controle de acesso.",
    lifespan=lifespan,
)

# Inclui as rotas no app
app.include_router(main_router)