"""Modelos de dados relacionados ao usuário"""

from typing import Optional
from sqlmodel import Field, Relationship, Session, SQLModel, select
from datetime import datetime
from api.database import engine
from api.security import HashedPassword

class UsuarioGrupoLink(SQLModel, table=True):
    """Representa o modelo de ligação entre usuário e grupo"""
    
    usuario_id: int = Field(default = None, foreign_key = "usuario.id", primary_key = True)
    grupo_id: int = Field(default = None, foreign_key = "grupo.id", primary_key = True)

class Usuario(SQLModel, table=True):
    """Representa o modelo do usuário"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome_usuario: str = Field(nullable=False)
    nome_pessoa: str = Field(nullable=False)
    senha: HashedPassword
    email: str = Field(unique=True, nullable=False)
    avatar: Optional[str] = None
    ativo: bool = Field(default=True)
    grupos: list["Grupo"] = Relationship(
        back_populates = "usuarios",
        link_model = UsuarioGrupoLink,
        sa_relationship_kwargs={
            "lazy": "selectin"
        },  # Evita a necessidade de conexão aberta para relationship
    )
    data_criacao: datetime = Field(default=datetime.now())
    
    @property
    def is_superusuario(self):
        return len([grupo.nome_grupo for grupo in self.grupos if grupo.nome_grupo == "admins"]) != 0
    
class GrupoPermissaoLink(SQLModel, table=True):
    """Representa o modelo de ligação entre grupo e permissão"""
    
    grupo_id: int = Field(default = None, foreign_key = "grupo.id", primary_key = True)
    permissao_id: int = Field(default = None, foreign_key = "permissao.id", primary_key = True)

class Grupo(SQLModel, table=True):
    """Representa o modelo do grupo"""

    id: Optional[int] = Field(default=None, primary_key=True)
    nome_grupo: str = Field(unique=True, nullable=False)
    permissoes: list["Permissao"] = Relationship(
        back_populates = "grupos", link_model = GrupoPermissaoLink
    )
    usuarios: list["Usuario"] = Relationship(
        back_populates = "grupos", link_model = UsuarioGrupoLink
    )
    
class Permissao(SQLModel, table=True):
    """Representa o modelo da permissão"""

    id: Optional[int] = Field(default=None, primary_key=True)
    nome_permissao: str = Field(unique=True, nullable=False)
    grupos: list[Grupo] = Relationship(
        back_populates = "permissoes", link_model = GrupoPermissaoLink
    )
    
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