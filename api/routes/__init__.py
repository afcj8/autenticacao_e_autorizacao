from fastapi import APIRouter

from .permissao import router as permissao_router

main_router = APIRouter()

main_router.include_router(permissao_router, prefix="/permissoes", tags=["permissoes"])