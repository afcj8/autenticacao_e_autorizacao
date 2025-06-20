from typing import Optional
from sqlmodel import Session, select

from api.database import engine
from api.models.usuario import Usuario

def get_usuario(nome_usuario: str) -> Optional[Usuario]:
    """Retorna um usuário pelo nome de usuário"""
    
    query = select(Usuario).where(Usuario.nome_usuario == nome_usuario)
    with Session(engine) as session:
        return session.exec(query).first()
    
def get_permissoes(nome_usuario: str) -> Optional[Usuario]:
    """Retorna as permissões de um usuário"""
    
    query = select(Usuario).where(Usuario.nome_usuario == nome_usuario)
    with Session(engine) as session:
        usuario = session.exec(query).one_or_none()
        if not usuario:
            return False
        permissoes = []
        for grupo in usuario.grupos:
            permissoes.extend(grupo.permissoes)
        permissoes_txt = [permissao.nome_permissao for permissao in permissoes]
        permissoes_usuario = list(set(permissoes_txt))
    return permissoes_usuario

def get_usuario_grupos_permissoes(nome_usuario: str) -> Optional[Usuario]:
    """Retorna as permissões de um grupo"""
    
    query = select(Usuario).where(Usuario.nome_usuario == nome_usuario)
    with Session(engine) as session:
        usuario = session.exec(query).one_or_none()
        if not usuario:
            return False
        permissoes = []
        grupos = []
        for grupo in usuario.grupos:
            grupos.append(grupo.nome_grupo)
            permissoes.extend(grupo.permissoes)
        permissoes_txt = [permissao.nome_permissao for permissao in permissoes]
        permissoes_usuario = list(set(permissoes_txt))
    return usuario, grupos, permissoes_usuario