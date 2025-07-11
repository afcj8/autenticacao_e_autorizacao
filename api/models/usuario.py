"""Modelos de dados relacionados ao usuário"""

from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
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