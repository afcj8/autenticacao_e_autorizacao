from fastapi import APIRouter

from .auth import router as auth_router
from .grupo import router as grupo_router
from .permissao import router as permissao_router
from .usuario import router as usuario_router

main_router = APIRouter()

main_router.include_router(auth_router, tags=["auth"])
main_router.include_router(usuario_router, prefix="/usuarios", tags=["usuarios"])
main_router.include_router(grupo_router, prefix="/grupos", tags=["grupos"])
main_router.include_router(permissao_router, prefix="/permissoes", tags=["permissoes"])