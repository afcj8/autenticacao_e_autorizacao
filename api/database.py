"""Conexão com o banco de dados"""

from sqlmodel import Session, SQLModel , create_engine, select
from fastapi import Depends

from api.models.usuario import Grupo, Permissao, Usuario
from api.security import criar_hash_senha

sqlite_file_name = "auth.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    """Cria as tabelas, se não existirem."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Cria uma sessão com o banco de dados."""
    with Session(engine) as session:
        yield session
        
SessionDep = Depends(get_session)

lista_permissoes = [
    "all:all",
    "add:permissao",
    "read:permissao",
    "update:permissao",
    "delete:permissao",
    "add:grupo",
    "read:grupo",
    "update:grupo",
    "delete:grupo",
    "add:usuario",
    "read:usuario",
    "update:usuario",
    "update:usuariogrupo"
]

grupos = [
    {"nome_grupo": "admins", "permissoes": [
        "all:all"
    ]},
]

def create_default_groups_and_permissions():
    """Cria grupos e permissões padrão."""

    with Session(engine) as session:
        
        # Verifica se já existe o grupo "admins"
        grupo_existente = session.exec(select(Grupo).where(Grupo.nome_grupo == "admins")).first()
        if grupo_existente:
            return
        
        for p in lista_permissoes:
            permissao = Permissao(nome_permissao=p)
            session.add(permissao)

        for g in grupos:
            if g["permissoes"]:
                permissoes = session.exec(select(Permissao).where(Permissao.nome_permissao.in_(g["permissoes"]))).all()
            else:
                permissoes = []
            
            
            grupo = Grupo(nome_grupo=g["nome_grupo"], permissoes=permissoes)
            session.add(grupo)

        session.commit()
    
    print("Grupos e permissões padrão criados com sucesso!")
        
def create_user_admin():
    """Cria o usuário admin padrão."""
    
    with Session(engine) as session:
        admin_grupo = session.exec(select(Grupo).where(Grupo.nome_grupo == "admins")).first()
        if not admin_grupo:
            raise ValueError("Grupo 'admins' não encontrado")
        
        user_admin = session.exec(select(Usuario).where(Usuario.nome_usuario == "admin")).first()
        if user_admin:
            return
        
        admin = Usuario(
            nome_usuario="admin",
            nome_pessoa="Administrador",
            email="adm@email.com",
            senha=criar_hash_senha("admin"),
            grupos=[admin_grupo],
            ativo=True
        )
        session.add(admin)
        session.commit()
        print("Usuário admin criado com sucesso!")