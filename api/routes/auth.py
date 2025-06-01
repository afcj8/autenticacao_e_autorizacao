from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.auth import (
    Token,
    RefreshToken,
    Usuario,
    criar_access_token,
    criar_refresh_token,
    autenticar_usuario,
    valida_token,
    buscar_usuario_atual_ativo,
)

from api.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES

from api.serializers.usuario import UsuarioResponse

router = APIRouter()

@router.get(
    "/token", 
    response_model=UsuarioResponse
)
async def validar_token_usuario_autenticado(
    *, 
    usuario: Usuario = Depends(buscar_usuario_atual_ativo)
):
    """Valida o token do usuário autenticado"""
    
    if usuario:
        return UsuarioResponse(
            id=usuario.id,
            nome_usuario=usuario.nome_usuario,
            nome_pessoa=usuario.nome_pessoa,
            email=usuario.email,
            avatar=usuario.avatar,
            ativo=usuario.ativo,
        )


@router.post(
    "/token", 
    response_model=Token
)
async def login_de_acesso(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Realiza o login de acesso"""
    
    usuario_auth = autenticar_usuario(form_data.username, form_data.password)
    
    if usuario_auth:
        usuario = usuario_auth[0]
        grupos = usuario_auth[1]
        permissoes = usuario_auth[2]
    
        if not usuario or not isinstance(usuario, Usuario):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nome de usuário ou senha inválidos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # pyright: ignore
        access_token = criar_access_token(
            data={
                "sub": usuario.nome_usuario, 
                "grupos": grupos,
                "permissoes": permissoes,
                "fresh": True
                },
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES) # pyright: ignore
        refresh_token = criar_refresh_token(
            data={"sub": usuario.nome_usuario}, expires_delta=refresh_token_expires
        )

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
@router.post(
    "/refresh-token", 
    response_model=Token
)
async def refresh_token(
    form_data: RefreshToken
):
    """Atualiza o token de acesso"""
    
    usuario = valida_token(token = form_data.refresh_token)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # pyright: ignore
    access_token = criar_access_token(
        data={"sub": usuario.nome_usuario, "fresh": True}, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES) # pyright: ignore
    refresh_token = criar_refresh_token(
        data={"sub": usuario.nome_usuario}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }