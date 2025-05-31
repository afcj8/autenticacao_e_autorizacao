from typing import Optional
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel, model_validator

from api.security import criar_hash_senha

class UsuarioResponse(BaseModel):
    """Representa o modelo de resposta do usuário"""
    
    id: int
    nome_usuario: str
    nome_pessoa: str
    email: str
    avatar: Optional[str] = None
    ativo: bool
    
class UsuarioGrupoResponse(BaseModel):
    """Representa o modelo de resposta da ligação entre usuário e grupo"""
    
    id: int
    nome_usuario: str
    nome_pessoa: str
    email: str
    avatar: Optional[str] = None
    ativo: bool
    grupos: list[str] = []
    
class UsuarioRequest(BaseModel):
    """Representa o modelo de criação do usuário"""
    
    nome_usuario: str
    nome_pessoa: str
    senha: str
    email: str
    avatar: Optional[str] = None
    ativo: Optional[bool] = True
    grupos: list[int] = []
    data_criacao: Optional[datetime] = datetime.now()
    
class UsuarioPatchRequest(BaseModel):
    nome_pessoa: str
    email: str
    
class UsuarioSenhaPatchRequest(BaseModel):
    senha: str
    senha_confirmacao: str
    
    @model_validator(mode="before")
    @classmethod
    def verificar_senhas_iguais(cls, values):
        """Verifica se as senhas informadas são iguais"""
        
        if values.get("senha") != values.get("senha_confirmacao"):
            raise HTTPException(status_code=422, detail="As senhas informadas são diferentes")
        
        return values
    
    @property
    def senha_hash(self) -> str:
        return criar_hash_senha(self.senha)
    
class UsuarioAtivoPatchRequest(BaseModel):
    ativo: bool
    
class UsuarioGrupoPatchRequest(BaseModel):
    grupos: list[int]
    
class GrupoResponse(BaseModel):
    """Serializador para resposta do grupo"""

    id: int
    nome_grupo: str
    permissoes: list[dict] = []
    
class GrupoRequest(BaseModel):
    """Serializador para payload de criação de grupo"""

    nome_grupo: str
    permissoes_id: list[int] = []

class PermissaoResponse(BaseModel):
    """Serializador para resposta da permissão"""

    id: int
    nome_permissao: str
    
class PermissaoRequest(BaseModel):
    """Serializador para payload de criação de permissão"""

    nome_permissao: str