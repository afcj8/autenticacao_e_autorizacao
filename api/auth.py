"""Token baseado no auth"""

from datetime import datetime, timedelta
from dateutil import tz
from typing import Optional, Union
from functools import partial

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from api.services.usuario import get_usuario, get_usuario_grupos_permissoes
from api.models.usuario import Usuario
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

async def buscar_usuario_se_alterar_senha_for_permitido(
    *, 
    request: Request, 
    pwd_reset_token: Optional[str] = None, 
    nome_usuario: str
) -> Usuario:
    
    usuario_alvo = get_usuario(nome_usuario)
    if not usuario_alvo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
        
    # Decodifica o token antes de passar para buscar_usuario_atual
    try:
        token_data = valida_token(token=pwd_reset_token) if pwd_reset_token else None
        valida_senha_reset = (
            buscar_usuario_atual(token_data=token_data) == usuario_alvo
        )
    except (HTTPException, JWTError):
        valida_senha_reset = False

    try:
        usuario_autenticado = buscar_usuario_atual(token_data="", request=request)
    except HTTPException:
        usuario_autenticado = None
        
    if any(
        [
            valida_senha_reset,
            usuario_autenticado and usuario_autenticado.id == usuario_alvo.id
        ]
    ):
        return usuario_alvo

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Você não tem permissão de mudar a senha deste usuário"
    )
    
PodeAlterarSenha = Depends(buscar_usuario_se_alterar_senha_for_permitido)

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

class ValidarPermissoes:
    def __init__(
        self, permissoes_requeridas: list[str], permissoes_usuario: bool = False
    ):
        self.permissoes_requeridas = permissoes_requeridas
        self.permissoes_usuario = permissoes_usuario
        
    async def __call__(
        self,
        token: str = Depends(oauth2_scheme),
        request: Request = None,
    ):
        if request:
            if authorization := request.headers.get("Authorization"):
                try:
                    token = authorization.split(" ")[1]
                except IndexError:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Os dados informados estão incorretos. Por favor, verifique e tente novamente.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            else:
                try:
                    token = request.query_params["token"]
                except KeyError:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Os dados informados estão incorretos. Por favor, verifique e tente novamente.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY,  # pyright: ignore
                algorithms=[ALGORITHM]  # pyright: ignore
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seu acesso não pôde ser validado. Tente fazer login novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
                
        if payload["scope"] == "auto_cadastro_usuario":
            return True
        else:
            permissoes_usuario = payload.get("permissoes")
            token_permissoes_set = set(permissoes_usuario)
            permissoes_requeridas_set = set(self.permissoes_requeridas)
            
            if set(["all:all"]).issubset(token_permissoes_set) or permissoes_requeridas_set.issubset(token_permissoes_set):
                return True
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Você não tem permissão para acessar este recurso. Verifique suas credenciais ou entre em contato com o administrador do sistema.",
                    headers={"WWW-Authenticate": "Bearer"},
            )