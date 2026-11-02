---
mocs:
  - "[[MOC_Carreira_e_Tecnologia]]"
tags:
  - arquitetura
  - oauth2
  - gcp
  - streamlit
  - cloud-run
  - seguranca
fontes:
  - "https://cloud.google.com/secret-manager/docs"
  - "https://developers.google.com/identity/protocols/oauth2"
atualizado: 2026-11-02
---

# Autenticação OAuth 2.0 / OIDC e Secret Manager para Aplicações Serverless no GCP

Modelo de segurança na camada de aplicação para restringir sistemas pessoais *serverless* a um único usuário autenticado via **Google OAuth 2.0 / OpenID Connect (OIDC)** e montagem de volumes do **Google Cloud Secret Manager**, eliminando o custo fixo mensal de componentes gerenciados de borda (*Application Load Balancer* e *Cloud Identity-Aware Proxy*).

## 1. Configuração de Credenciais OAuth no Google Cloud Console

Para habilitar a autenticação federada com conta Google em ambientes de desenvolvimento e produção:

1. **Tela de Consentimento OAuth**:
   - No Google Cloud Console, acessar **APIs e Serviços > Tela de consentimento OAuth**.
   - Selecionar **Tipo de usuário: Externo**.
   - Na seção **Usuários de teste (*Test users*)**, adicionar estritamente o próprio endereço de e-mail (`seu_email@gmail.com`).
2. **Emissão do Client ID**:
   - Navegar até **Credenciais > Criar Credenciais > ID do cliente OAuth**.
   - Definir **Tipo de aplicativo: Aplicativo da Web**.
   - Cadastrar os dois **URIs de redirecionamento autorizados** (incluindo a barra final):
     - `http://localhost:8501/` (execução local durante desenvolvimento)
     - `https://<URL_DO_APP>.a.run.app/` (endpoint HTTPS de produção no Cloud Run)
   - Exportar e preservar o **Client ID** e o **Client Secret** resultantes (utilizados em `google_credentials.json`).

## 2. Gate de Autenticação e Whitelist Estrita em Python (`app.py`)

A biblioteca `streamlit-google-auth` gerencia o handshake OAuth 2.0 e o cookie de sessão assinado, enquanto uma verificação explícita de identidade (`EMAIL_PERMITIDO`) interrompe imediatamente a árvore de renderização (`st.stop()`) para qualquer credencial divergente:

```python
import streamlit as st
from streamlit_google_auth import Authenticate
from google import genai

st.set_page_config(page_title="Agente Pessoal", layout="wide")

# Configuracao OAuth
authenticator = Authenticate(
    secret_credentials_path="google_credentials.json",
    cookie_name="agente_cookie",
    cookie_key=st.secrets["COOKIE_SECRET"],
    redirect_uri=st.secrets["REDIRECT_URI"],
)
authenticator.check_authentification()

# Tela de bloqueio
if not st.session_state.get("connected"):
    st.title("Sistema Pessoal Seguro")
    st.info("Autenticação necessária.")
    st.link_button("Entrar com o Google", authenticator.get_authorization_url())
    st.stop()

# Validacao do usuario (Whitelist estrita)
user_email = st.session_state.get("user_info", {}).get("email")
EMAIL_PERMITIDO = "seu_email_aqui@gmail.com"
if user_email != EMAIL_PERMITIDO:
    st.error("Acesso não autorizado.")
    if st.button("Sair"):
        authenticator.logout()
    st.stop()

# Area restrita
st.sidebar.write(f"Conectado: **{user_email}**")
if st.sidebar.button("Logout"):
    authenticator.logout()

st.title("Painel do Agente")
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
prompt = st.text_input("Comando:")
if prompt:
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt
    )
    st.markdown(response.text)
```

## 3. Gestão de Segredos via Google Cloud Secret Manager

| Artefato Sensível | Regra de Versionamento | Estratégia de Injeção em Produção (Cloud Run) |
| :--- | :--- | :--- |
| `.streamlit/secrets.toml` | **Proibido no Git** (`.gitignore`) | Criar segredo **`APP_SECRETS`** no Secret Manager (contendo `COOKIE_SECRET`, `REDIRECT_URI` e `GEMINI_API_KEY`) e mapeá-lo como **volume montado** em `/app/.streamlit/secrets.toml`. |
| `google_credentials.json` | **Proibido no Git** (`.gitignore`) | Armazenar o JSON do Client OAuth no Secret Manager e montar em tempo de execução no diretório de trabalho `/app/` do container. |

- **Leitura transparente**: Como o Secret Manager projeta o conteúdo de `APP_SECRETS` diretamente no sistema de arquivos em memória no caminho `/app/.streamlit/secrets.toml`, o Streamlit resolve `st.secrets[...]` nativamente sem exigir SDK adicional de leitura de segredos no código-fonte.

> [!tip] Defesa em Dupla Barreira (Google OAuth + Código)
> Manter o aplicativo OAuth em modo **Teste** no Console do GCP faz com que o próprio servidor de identidade do Google recuse o login de qualquer conta fora da lista de *Test users* antes mesmo do redirecionamento, funcionando como primeira barreira anterior à *whitelist* `EMAIL_PERMITIDO` no Python.

> [!warning] Isolamento de Camadas Docker
> Jamais injete `.streamlit/secrets.toml` ou `google_credentials.json` durante o `docker build`. Qualquer segredo copiado na imagem permanece extraível no histórico de camadas do Artifact Registry; utilize exclusivamente montagem de volumes do Secret Manager em *runtime*.

### Conexões Transversais
- **Infraestrutura e Deploy Serverless**: Empacotamento em `Dockerfile` (`python:3.11-slim`), dependências e pipelines de entrega contínua no Cloud Run detalhados em [[Arquitetura_Streamlit_Serverless_Cloud_Run]].
