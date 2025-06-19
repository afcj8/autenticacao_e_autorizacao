# O ideal é que este arquivo esteja no .gitignore para não ser versionado
# mas para fins de exemplo, ficará aqui.

SECRET_KEY = "b9483cc8a0bad1c2fe31e6d9d6a36c4a96ac23859a264b69a0badb4b32c538f8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 600
RESET_TOKEN_EXPIRE_MINUTES = 60

# urls de exemplo para o frontend
PWD_RESET_URL = "http://localhost:5173/resetsenha"

smtp_sender = "no-reply@dm.com"
smtp_server = "localhost"