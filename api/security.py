"""Utilitários de segurança"""

from typing import Any

from passlib.context import CryptContext
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha, hash_senha) -> bool:
    """Verifica se a senha informada é válida"""
    
    return pwd_context.verify(senha, hash_senha)

def criar_hash_senha(senha) -> str:
    """Cria um hash para a senha informada"""
    
    return pwd_context.hash(senha)

class HashedPassword(str):
    """Classe para representar uma senha criptografada"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))
        
    @classmethod
    def validate(cls, v, values=None, **kwargs):
        """Valida a senha informada"""
        
        if not isinstance(v, str):
            raise ValueError("Senha inválida")
        
        hashed_senha = criar_hash_senha(v)
        return cls(hashed_senha)