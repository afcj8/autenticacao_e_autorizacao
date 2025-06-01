from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from api.database import SessionDep
from api.models.usuario import Grupo, Permissao, UsuarioGrupoLink
from api.serializers.usuario import GrupoResponse, GrupoRequest

router = APIRouter()

@router.get(
    "", 
    response_model=List[GrupoResponse], 
)
async def listar_grupos(
    *, 
    session: Session = SessionDep
):
    """Lista todos os grupos"""
    
    # Exclui o grupo "admins" da lista de grupos
    # para evitar que usuários comuns vejam este grupo
    # e suas permissões.
    
    grupos = session.exec(select(Grupo).where(Grupo.nome_grupo != "admins")).all()
    response = []
    for grupo in grupos:
        response.append(
            GrupoResponse(
                id = grupo.id,
                nome_grupo = grupo.nome_grupo,
                permissoes = [{"id": permissao.id, "nome_permissao": permissao.nome_permissao} for permissao in grupo.permissoes]
            )
        )
    return response

@router.post(
    "", 
    response_model=GrupoResponse, 
    status_code=201, 
)
async def criar_grupo(
    *, 
    grupo: GrupoRequest, 
    session: Session = SessionDep
) -> GrupoResponse:
    """Cria um novo grupo"""
    
    if session.exec(select(Grupo).where(Grupo.nome_grupo == grupo.nome_grupo)).first():
        raise HTTPException(status_code=409, detail="Grupo já existe")
    
    permissoes = session.exec(select(Permissao).where(Permissao.id.in_(grupo.permissoes_id))).all()
    
    db_grupo = Grupo(nome_grupo=grupo.nome_grupo, permissoes=permissoes)
    session.add(db_grupo)
    session.commit()
    session.refresh(db_grupo)
    
    return GrupoResponse(
        id = db_grupo.id,
        nome_grupo = db_grupo.nome_grupo,
        permissoes = [{"id": permissao.id, "nome_permissao": permissao.nome_permissao} for permissao in permissoes],
    )
    
@router.patch(
    "/{id}", 
    response_model=GrupoResponse, 
)
async def atualizar_grupo(
    *, 
    id: int, 
    patch_data: GrupoRequest, 
    session: Session = SessionDep
) -> GrupoResponse:
    """Atualiza um grupo pelo ID"""
    
    grupo = session.get(Grupo, id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    nome_existente = session.exec(select(Grupo).where(Grupo.nome_grupo == patch_data.nome_grupo)).first()
    
    if nome_existente and nome_existente.id != id:
        raise HTTPException(status_code=409, detail="Grupo já existe")
    
    permissoes = session.exec(select(Permissao).where(Permissao.id.in_(patch_data.permissoes_id))).all()
    
    grupo.nome_grupo = patch_data.nome_grupo
    grupo.permissoes = permissoes
    
    session.add(grupo)
    session.commit()
    
    return GrupoResponse(
        id = grupo.id,
        nome_grupo = grupo.nome_grupo,
        permissoes = [{"id": permissao.id, "nome_permissao": permissao.nome_permissao} for permissao in permissoes],
    )
    
@router.delete(
    "/{id}", 
)
async def deletar_grupo(
    *, 
    id: int, 
    session: Session = SessionDep
):
    """Deleta um grupo pelo ID"""
    
    grupo = session.get(Grupo, id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    usuario_link = session.exec(select(UsuarioGrupoLink).where(UsuarioGrupoLink.grupo_id == id)).all()
    
    if len(usuario_link) > 0:
        raise HTTPException(status_code=409, detail="Grupo possui usuários vinculados")
    
    session.delete(grupo)
    session.commit()
    return {"detail": "Grupo deletado com sucesso"}