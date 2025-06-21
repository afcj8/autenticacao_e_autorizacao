<h1>Sistema de Autenticação e Autorização</h1>

<h2>⚡ Projeto</h2>

O Sistema de Autenticação e Autorização é uma API desenvolvida com **FastAPI** e **SQLite**, que fornece uma estrutura robusta para controle de acesso por meio de autenticação JWT e autorização baseada em permissões. A aplicação permite o gerenciamento de usuários, grupos e permissões, garantindo que apenas usuários com as credenciais corretas possam acessar rotas específicas.

Neste projeto, destacam-se as seguintes tecnologias:

- **FastAPI**: framework web moderno e de alto desempenho para construção de APIs com Python.
- **Pydantic**: utilizado para validação e serialização de dados de forma eficiente.
- **SQLite**: banco de dados leve, ideal para aplicações pequenas ou médias, com persistência automática em arquivo `.db`.
- **SQLAlchemy**: ferramenta ORM poderosa para comunicação com o banco de dados.
- **Uvicorn**: servidor responsável por executar a aplicação de forma rápida e eficiente.
- **JWT (JSON Web Tokens)**: responsável pelo mecanismo de autenticação e autorização segura via tokens.

Ao executar o servidor pela primeira vez, será criado automaticamente o arquivo `auth.db`, contendo o banco de dados, a estrutura de permissões, o grupo `admins` (com acesso total ao sistema) e um usuário administrador padrão:

- **Usuário**: `admin`
- **Senha**: `admin`

---

## 🔐 Autenticação (`/auth`)

### GET `/auth/token`
Valida um token de acesso.

### POST `/auth/token`
Gera um token de acesso a partir de `nome_usuario` e `senha`.

### POST `/auth/refresh-token`
Renova o token de acesso utilizando um token de refresh válido.

---

## 👤 Usuários (`/usuarios`)

| Método | Rota                    | Permissão Necessária           | Descrição |
|------- |------------------------ |------------------------------- |-----------|
| GET    | `/usuarios`             | `read:usuario`                 | Lista todos os usuários. |
| POST   | `/usuarios`             | `add:usuario`                  | Cria um novo usuário. |
| GET    | `/usuarios/me`          | —                              | Retorna os dados do usuário autenticado. |
| GET    | `/usuarios/{id}`        | `read:usuario`                 | Detalha os dados de um usuário específico. |
| PATCH  | `/usuarios/{id}/avatar` | `all:all` ou o próprio usuário | Altera o avatar do usuário. |
| PATCH  | `/usuarios/{id}/grupos` | `update:usuariogrupo`          | Atualiza os grupos de um usuário. |
| PATCH  | `/usuarios/{id}/status` | Apenas `admins`                | Ativa ou desativa um usuário. |
| POST   | `/usuarios/reset-senha` | —                              | Gera um token de redefinição de senha (simulado via arquivo `email.log`). |
| PATCH  | `/usuarios/{nome_usuario}/senha` | — (com token válido)  | Redefine a senha utilizando o token gerado. |

---

## 🛡️ Permissões (`/permissoes`)

| Método | Rota                 | Permissão Necessária  |
|--------|----------------------|------------------------|
| GET    | `/permissoes`       | `read:permissao`       |
| POST   | `/permissoes`       | `add:permissao`        |
| GET    | `/permissoes/{id}`  | `read:permissao`       |
| PATCH  | `/permissoes/{id}`  | `update:permissao`     |
| DELETE | `/permissoes/{id}`  | `delete:permissao`     |

---

## 👥 Grupos (`/grupos`)

| Método | Rota              | Permissão Necessária |
|------- |------------------ |--------------------- |
| GET    | `/grupos`         | `read:grupo`          |
| POST   | `/grupos`         | `add:grupo`           |
| GET    | `/grupos/{id}`    | `read:grupo`          |
| PATCH  | `/grupos/{id}`    | `update:grupo`        |
| DELETE | `/grupos/{id}`    | `delete:grupo`        |

---

## 🔑 Lista de Permissões

As permissões utilizam o formato `ação:recurso`, por exemplo:

```python
lista_permissoes = [
    "all:all",                 # Acesso total ao sistema
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
```

## 📌 Observações

- O reset de senha envia o token para o arquivo `email.log`, simulando o envio por e-mail.
- Apenas usuários com permissão `all:all` podem alterar o avatar de qualquer outro usuário.
- A ativação/desativação de usuários é restrita ao grupo `admins`.

## 🛠️ Manual do Desenvolvedor

1. Clone o repositório:
   ```bash
   git clone https://github.com/afcj8/autenticacao_e_autorizacao.git
   ```

2. Verifique se o Python está instalado em sua máquina:
   ```bash
   python --version
   ```

3. Navegue até o diretório clonado:
   ```bash
   cd autenticacao_e_autorizacao
   ```

4. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```

5. Ative o ambiente virtual:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

6. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

7. Execute a aplicação com o Uvicorn:
   ```bash
   uvicorn api.app:app --reload
   ```

8. Acesse a documentação (Swagger UI) no navegador com a seguinte URL:
   ```bash
   http://localhost:8000/docs
   ```