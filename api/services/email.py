from datetime import timedelta
from time import sleep

from sqlmodel import Session, select

from api.auth import criar_access_token
from api.models.usuario import Usuario
from api.database import engine

from api.config import RESET_TOKEN_EXPIRE_MINUTES, PWD_RESET_URL, smtp_sender
        
def _enviar_email_debug(email: str, subject: str, msg: str):
    """Simular o envio de email"""
    
    with open("email.log", "a") as f:
        sleep(3)
        f.write(f"--- INÍCIO DO EMAIL {email} ---\nSubject: {subject}\n" f"{msg}\n" f"--- FIM DO EMAIL ---\n")

def tenta_enviar_email_de_reset_de_senha(email):
    """Dado um endereço de e-mail, envia um e-mail se o usuário for encontrado"""
    
    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
        if not usuario:
            return
        
        sender = smtp_sender    # pyright: ignore
        url = PWD_RESET_URL   # pyright: ignore
        expire = RESET_TOKEN_EXPIRE_MINUTES    # pyright: ignore
        
        pwd_reset_token = criar_access_token(
            data={"sub": usuario.nome_usuario},
            expires_delta=timedelta(minutes=expire),
            scope="pwd_reset",
        )
        
        msg = MSG_RESET_SENHA.format(
            sender=sender,
            to=usuario.nome_pessoa,
            url=url,
            pwd_reset_token=pwd_reset_token,
            mens_expire=expire,
        )
        
        _enviar_email_debug(
            email=usuario.email,
            subject="API - Redefinição de senha",
            msg=msg,
        )

MSG_RESET_SENHA = """\
From: API <{sender}>
To: {to}
Assunto: Redefinição de senha

Use o link a seguir para redefinir sua senha:
{url}?token={pwd_reset_token}

Este link expirará em {mens_expire} minutos.
"""