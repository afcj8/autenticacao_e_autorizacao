from fastapi import FastAPI

app = FastAPI(
    title="API de Autenticação e Autorização",
    version="0.1.0",
    description="API para gerenciamento de usuários, grupos e permissões, com autenticação e controle de acesso.",
)