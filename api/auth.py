"""Token baseado no auth"""

from datetime import datetime, timedelta
from dateutil import tz
from typing import Optional, Union
from functools import partial

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from api.models.usuario import Usuario, get_usuario, get_usuario_grupos_permissoes
from api.security import verificar_senha
from api.config import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    
class TokenData(BaseModel):
    nome_usuario: Optional[str] = None
    permissoes: list[str] = []

class RefreshToken(BaseModel):
    refresh_token: str

def criar_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None, 
    scope: str = "access_token"
) -> str:
    """Cria um token de acesso"""
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=tz.tzutc()) + expires_delta
    else:
        expire = datetime.now(tz=tz.tzutc()) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "scope": scope})
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY,  # pyright: ignore
        algorithm=ALGORITHM,  # pyright: ignore
    )
    return encoded_jwt

criar_refresh_token = partial(criar_access_token, scope="refresh_token")

def valida_token(
    token: str = Depends(oauth2_scheme), 
    request: Request = None # pyright: ignore
) -> TokenData:
    """Valida o token"""
    
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Os dados informados estão incorretos. Por favor, verifique e tente novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if request:
        if authorization := request.headers.get("authorization"):
            try:
                token = authorization.split(" ")[1]
            except IndexError:
                raise excecao_credenciais
    
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY,  # pyright: ignore
            algorithms=[ALGORITHM]  # pyright: ignore
        )
        nome_usuario: str = payload.get("sub")
        if nome_usuario is None:
            raise excecao_credenciais
        token_data = TokenData(nome_usuario=nome_usuario)
        usuario = get_usuario(nome_usuario=token_data.nome_usuario)
        if not usuario:
            raise excecao_credenciais
    except JWTError:
        raise excecao_credenciais
    return token_data

def autenticar_usuario(
    nome_usuario: str, 
    senha: str
) -> Union[Usuario, bool]:
    """Autentica o usuário"""
    
    usuario_grupo_permissoes = get_usuario_grupos_permissoes(nome_usuario)
    if not usuario_grupo_permissoes:
        return False
    usuario = usuario_grupo_permissoes[0]
    grupos = usuario_grupo_permissoes[1]
    permissoes = usuario_grupo_permissoes[2]
    if not usuario:
        return False
    if not verificar_senha(senha, usuario.senha):
        return False
    return usuario, grupos, permissoes

def buscar_usuario_atual(
    token_data: TokenData = Depends(valida_token), 
    request: Request = None,
) -> Usuario:
    """Retorna usuário autenticado"""
    
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Os dados informados estão incorretos. Por favor, verifique e tente novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if request:
        if authorization := request.headers.get("authorization"):
            try:
                token = authorization.split(" ")[1]
                token_data = valida_token(token=token)
                return get_usuario(nome_usuario=token_data.nome_usuario)
            except IndexError:
                raise excecao_credenciais
            
    if token_data:
        return get_usuario(nome_usuario=token_data.nome_usuario)
    
def buscar_usuario_grupo_permissoes_atual(
    token_data: TokenData = Depends(valida_token),
) -> tuple[Usuario, list[str], list[str]]:
    """Busca o usuário, grupo e permissões atuais"""
    
    usuario, grupos, permissoes = get_usuario_grupos_permissoes(nome_usuario=token_data.nome_usuario)
    return usuario, grupos, permissoes

async def buscar_usuario_atual_ativo(
    usuario_autenticado: Usuario = Depends(buscar_usuario_atual)
) -> Usuario:
    """Busca o usuário atual ativo"""
    
    if not usuario_autenticado.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário está desativado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario_autenticado

UsuarioAutenticado = Depends(buscar_usuario_atual_ativo)

async def buscar_super_usuario(
    usuario_atual: Usuario = Depends(buscar_usuario_atual)
) -> Usuario:
    """
    Verifica se o usuário atual pertence ao grupo 'admins'.
    Retorna o usuário se for super usuário, ou lança uma exceção HTTP 401.
    """
    grupos_usuario = [grupo.nome_grupo for grupo in usuario_atual.grupos]

    if 'admins' not in grupos_usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não é do grupo de administradores",
        )
    
    return usuario_atual

SuperUsuario = Depends(buscar_super_usuario)