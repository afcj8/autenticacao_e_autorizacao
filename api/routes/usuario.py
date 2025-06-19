import uuid

from fastapi import APIRouter, File, UploadFile, Form, status, Depends
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from api.database import SessionDep
from api.models.usuario import Usuario, Grupo, get_permissoes
from api.security import criar_hash_senha

from api.serializers.usuario import (
    UsuarioResponse,
    UsuarioGrupoResponse,
    UsuarioAtivoPatchRequest,
    UsuarioGrupoPatchRequest
)

from api.auth import (
    UsuarioAutenticado,
    buscar_super_usuario, 
    buscar_usuario_atual_ativo
)

tipos_imagem_permitidos =  ["image/jpeg", "image/png"]

router = APIRouter()

@router.get(
    "", 
    response_model=list[UsuarioGrupoResponse], 
)
async def listar_usuarios(
    *,
    session: Session = SessionDep
):
    """Lista todos os usuários com seus grupos"""
    
    usuarios = session.exec(select(Usuario).order_by(Usuario.id)).all()
    
    response = []
    for usuario in usuarios:
        grupos = [grupo.nome_grupo for grupo in usuario.grupos]
        response.append(
            UsuarioGrupoResponse(
                id=usuario.id,
                nome_usuario=usuario.nome_usuario,
                nome_pessoa=usuario.nome_pessoa,
                email=usuario.email,
                avatar=usuario.avatar,
                ativo=usuario.ativo,
                grupos=grupos
            )
        )
    
    return response

@router.post(
    "", 
    status_code=201, 
)
async def criar_usuario(
    *,
    nome_usuario: str = Form(...),
    nome_pessoa: str = Form(...),
    senha: str = Form(...),
    email: str = Form(...),
    avatar: UploadFile = File(None),
    grupos: list[int] = Form(...),
    session: Session = SessionDep
) -> UsuarioGrupoResponse:
    """Cria um novo usuário"""
    
    email_existente = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if email_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")
    
    nome_usuario_existente = session.exec(select(Usuario).where(Usuario.nome_usuario == nome_usuario)).first()
    if nome_usuario_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já cadastrado")
    
    grupos_db = session.exec(select(Grupo).where(Grupo.id.in_(grupos))).all()
    print(f"Grupos encontrados: {[grupo.id for grupo in grupos_db]}")
    if len(grupos_db) != len(grupos):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alguns grupos não foram encontrados")
    
    db_usuario = Usuario(
        nome_usuario=nome_usuario,
        nome_pessoa=nome_pessoa,
        senha=criar_hash_senha(senha),
        email=email,
        grupos=grupos_db
    )
    
    if avatar:
        print(f"Avatar recebido: {avatar.filename}, tipo: {avatar.content_type}")
        if avatar.content_type not in tipos_imagem_permitidos:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Tipo de imagem não permitido, deve ser uma imagem do tipo: " + ", ".join(tipos_imagem_permitidos))
        avatar_nome = f"avatar_{uuid.uuid4()}.{avatar.filename.split('.')[-1]}"
        db_usuario.avatar = avatar_nome
        
    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)
    return UsuarioGrupoResponse(
        id=db_usuario.id,
        nome_usuario=db_usuario.nome_usuario,
        nome_pessoa=db_usuario.nome_pessoa,
        email=db_usuario.email,
        avatar=db_usuario.avatar,
        ativo=db_usuario.ativo,
        grupos=[grupo.id for grupo in db_usuario.grupos]
    )

@router.get(
    "/me", 
    response_model=UsuarioGrupoResponse
)
async def buscar_usuario_logado(
    *, 
    session: Session = SessionDep, 
    usuario: Usuario = UsuarioAutenticado
):
    """Retorna dados do usuário autenticado"""
    
    with session:
        usuario = session.exec(select(Usuario).where(Usuario.id == usuario.id)).first()
        if usuario:
            grupos = [grupo.nome_grupo for grupo in usuario.grupos]
            return UsuarioGrupoResponse(
                id=usuario.id,
                nome_usuario=usuario.nome_usuario,
                nome_pessoa=usuario.nome_pessoa,
                email=usuario.email,
                avatar=usuario.avatar,
                ativo=usuario.ativo,
                grupos=grupos
            )   
            
@router.patch(
    "/{id}/avatar",
    status_code=200,
)
async def atualizar_avatar_usuario(
    *,
    session: Session = SessionDep,
    id: int,
    avatar: UploadFile = File(...),
    usuario: Usuario = Depends(buscar_usuario_atual_ativo),
) -> UsuarioResponse:
    """Atualiza o avatar de um usuário"""
    
    permissoes_usuario = get_permissoes(usuario.nome_usuario)
    
    usuario_buscado = session.get(Usuario, id)
    if not usuario_buscado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if usuario.id != id and "all:all" not in permissoes_usuario:
        raise HTTPException(status_code=403, detail="Você não tem permissão para atualizar o avatar de outro usuário")
     
    if avatar.content_type not in tipos_imagem_permitidos:
        raise HTTPException(status_code=415, detail="Tipo de imagem não permitido, deve ser uma imagem do tipo: " + ", ".join(tipos_imagem_permitidos))
    
    avatar_nome = f"{uuid.uuid4()}{avatar.filename}"
    usuario_buscado.avatar = avatar_nome
    
    session.add(usuario_buscado)
    session.commit()
    session.refresh(usuario_buscado)
    return usuario_buscado

@router.patch(
    "/{id}/grupos", 
    status_code=200,
)
async def atualizar_grupos_usuario(
    *,
    session: Session = SessionDep,
    id: int,
    patch_data: UsuarioGrupoPatchRequest,
) -> UsuarioGrupoResponse:
    """Atualiza os grupos de um usuário"""
    
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    grupos = session.exec(select(Grupo).where(Grupo.id.in_(patch_data.grupos))).all()
    usuario.grupos = grupos
    
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return UsuarioGrupoResponse(
        id=usuario.id,
        nome_usuario=usuario.nome_usuario,
        nome_pessoa=usuario.nome_pessoa,
        email=usuario.email,
        avatar=usuario.avatar,
        ativo=usuario.ativo,
        grupos=[grupo.nome_grupo for grupo in usuario.grupos]
    )

@router.patch(
    "/{id}/status",
    status_code=200,
)
async def atualizar_status_usuario(
    *,
    id: int,
    patch_data: UsuarioAtivoPatchRequest,
    session: Session = SessionDep,
    usuario: Usuario = Depends(buscar_super_usuario)
):
    """Ativa ou desativa um usuário, apenas superusuários podem fazer isso"""
    
    db_usuario = session.get(Usuario, id)
    if not db_usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    
    db_usuario.ativo = patch_data.ativo
    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)
    
    return UsuarioGrupoResponse(
        id=db_usuario.id,
        nome_usuario=db_usuario.nome_usuario,
        nome_pessoa=db_usuario.nome_pessoa,
        email=db_usuario.email,
        avatar=db_usuario.avatar,
        ativo=db_usuario.ativo,
        grupos=[grupo.nome_grupo for grupo in db_usuario.grupos]
    )