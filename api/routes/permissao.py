from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from api.auth import ValidarPermissoes
from api.database import SessionDep
from api.models.usuario import Permissao, GrupoPermissaoLink
from api.serializers.usuario import PermissaoResponse, PermissaoRequest

router = APIRouter()

@router.get(
    "", 
    response_model=List[PermissaoResponse],
    dependencies=[Depends(ValidarPermissoes("read:permissao"))]
)
async def listar_permissoes(
    *, 
    session: Session = SessionDep
):
    """Lista todas as permissões"""
    
    # Exclui a permissão "all:all" da lista de permissões
    # para evitar que ela seja retornada em listagens
    # e também para evitar que ela seja criada ou atualizada
    # com o mesmo nome, já que é uma permissão especial para o grupo de 'admins'
    # e não deve ser manipulada diretamente.
    
    permissoes = session.exec(select(Permissao).where(Permissao.nome_permissao != "all:all")).all()
    return permissoes

@router.post(
    "", 
    response_model=PermissaoResponse, 
    status_code=201,
    dependencies=[Depends(ValidarPermissoes("add:permissao"))]
)
async def criar_permissao(
    *, 
    permissao: PermissaoRequest, 
    session: Session = SessionDep
):
    """Cria uma nova permissão"""
    
    permissao_existente = session.exec(select(Permissao).where(Permissao.nome_permissao == permissao.nome_permissao)).first()
    
    if permissao_existente:
        raise HTTPException(status_code=409, detail="Permissão já existe")
    
    db_permissao = Permissao.model_validate(permissao)
    session.add(db_permissao)
    session.commit()
    session.refresh(db_permissao)
    return db_permissao

@router.get(
    "/{id}", 
    response_model=PermissaoResponse,
    dependencies=[Depends(ValidarPermissoes("read:permissao"))]
)
async def buscar_permissao_por_id(
    *, 
    id: int, 
    session: Session = SessionDep
):
    """Busca uma permissão pelo ID"""
    
    permissao = session.get(Permissao, id)
    if not permissao:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    return permissao

@router.patch(
    "/{id}", 
    response_model=PermissaoResponse,
    dependencies=[Depends(ValidarPermissoes("update:permissao"))]
)
async def atualizar_permissao(
    *, 
    id: int, 
    patch_data: PermissaoRequest, 
    session: Session = SessionDep
):
    """Atualiza uma permissão pelo ID"""
    
    permissao = session.get(Permissao, id)
    if not permissao:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    if session.exec(select(Permissao).where(Permissao.nome_permissao == patch_data.nome_permissao)).first():
        raise HTTPException(status_code=409, detail="Permissão já existe")
    
    permissao.nome_permissao = patch_data.nome_permissao
    session.add(permissao)
    session.commit()
    session.refresh(permissao)
    return permissao

@router.delete(
    "/{id}",
    dependencies=[Depends(ValidarPermissoes("delete:permissao"))]
)
async def deletar_permissao(
    *, 
    id: int, 
    session: Session = SessionDep
):
    """Deleta uma permissão pelo ID"""
    
    permissao = session.get(Permissao, id)
    if not permissao:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    permissao_link = session.exec(select(GrupoPermissaoLink).where(GrupoPermissaoLink.permissao_id == id)).all()
    if len(permissao_link) > 0:
        raise HTTPException(status_code=409, detail="Permissão está vinculada a um grupo")
    
    session.delete(permissao)
    session.commit()
    return {"detail": "Permissão deletada com sucesso"}