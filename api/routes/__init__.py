from fastapi import APIRouter

from .permissao import router as permissao_router
from .grupo import router as grupo_router

main_router = APIRouter()

main_router.include_router(grupo_router, prefix="/grupos", tags=["grupos"])
main_router.include_router(permissao_router, prefix="/permissoes", tags=["permissoes"])