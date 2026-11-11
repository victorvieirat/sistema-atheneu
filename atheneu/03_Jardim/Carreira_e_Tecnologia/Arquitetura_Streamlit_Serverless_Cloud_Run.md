---
mocs:
  - "[[MOC_Carreira_e_Tecnologia]]"
tags:
  - arquitetura
  - streamlit
  - cloud-run
  - gcp
  - gemini
fontes:
  - "https://cloud.google.com/run/docs"
  - "https://ai.google.dev/gemini-api/docs"
status: em-estudo
atualizado: 2026-11-02
---

# Arquitetura Streamlit Serverless no Google Cloud Run

## Resumo Feynman (Minhas Palavras)

> [!note] Síntese Pessoal (Preencher após estudo ativo)
> *Explique aqui com suas próprias palavras a ideia central desta nota, sem jargões, e registre dúvidas ou contra-argumentos para testar depois.*

Estratégia arquitetural para hospedar uma aplicação pessoal em **Streamlit** integrada ao SDK oficial **`google-genai`** (**`gemini-2.5-pro`**) no **Google Cloud Run**, combinando **escala automática para zero (`min-instances 0`)**, controle estrito de usuário único na camada da aplicação e **custo fixo mensal de R$ 0,00** dentro da franquia gratuita do GCP.

## 1. Visão Geral e Decisões de Infraestrutura

| Camada Arquitetural | Tecnologia / Configuração | Justificativa Técnica e Financeira |
| :--- | :--- | :--- |
| **Computação Serverless** | **Google Cloud Run** (`managed`, `us-central1`) | Escala para zero na ausência de tráfego (`--min-instances 0`) e trava teto de concorrência (`--max-instances 1`). |
| **Motor de IA** | SDK **`google-genai`** (`gemini-2.5-pro`) | Integração direta via chave de API injetada em tempo de execução. |
| **Segurança e Acesso** | Google OAuth 2.0 / OIDC + *Whitelist* em Python | Dispensa *Application Load Balancer* e *Cloud IAP* pagos, mantendo custo fixo em **R$ 0,00** (ver [[Autenticacao_OAuth2_OIDC_e_Secret_Manager_GCP]]). |
| **Segredos** | **Google Cloud Secret Manager** (`APP_SECRETS`) | Montado em memória como volume em `/app/.streamlit/secrets.toml`, sem gravar credenciais na imagem Docker. |
| **Entrega Contínua (CI/CD)** | GitHub privado + Cloud Build ou GitHub Actions | Promoção automatizada a cada *push* ou *merge* na branch `main` sem chaves JSON estáticas. |

## 2. Dependências e Estrutura da Aplicação

O ambiente Python enxuto requer apenas três pacotes principais declarados em `requirements.txt`:

```txt
streamlit
google-genai
streamlit-google-auth
```

Na estrutura de `app.py`, a execução divide-se em duas etapas sequenciais:
1. **Barreira de autenticação e autorização**: Inicialização do fluxo OAuth 2.0 via `Authenticate`, bloqueio de sessões não conectadas com `st.stop()` e validação estrita do e-mail autenticado contra a *whitelist* individual (código integral documentado em [[Autenticacao_OAuth2_OIDC_e_Secret_Manager_GCP]]).
2. **Consumo autenticado do modelo Gemini**: Apenas após superar o *gate* OIDC, a interface instancia o cliente `genai.Client` lendo `st.secrets["GEMINI_API_KEY"]` e despacha comandos ao modelo `gemini-2.5-pro`:

```python
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

## 3. Containerização (`Dockerfile`)

O empacotamento utiliza imagem oficial `python:3.11-slim`, expondo a porta `8080` exigida pelo contrato HTTP/WebSocket do Cloud Run e vinculando o servidor Streamlit ao endereço `0.0.0.0`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

## 4. Promoção de Código e Pipelines de CI/CD

### Opção A: Integração Nativa do Cloud Run (Cloud Build)
- No console do Google Cloud Run, selecionar a opção **"Implantar continuamente a partir de um repositório"**.
- Conectar o repositório privado do GitHub apontando para a branch `main` e para o `Dockerfile` na raiz.
- Novos *builds* e *deploys* passam a executar automaticamente via **Cloud Build** a cada *push* na branch principal.

### Opção B: GitHub Actions com Workload Identity Federation
- Configurar o workflow `.github/workflows/deploy.yml` autenticando o *runner* do GitHub diretamente no GCP via **Workload Identity Federation** (eliminando o armazenamento de chaves estáticas de Service Account).
- A cada *merge* na branch `main`, o pipeline executa o comando declarativo de implantação:

```bash
gcloud run deploy agente-pessoal \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1
```

> [!tip] Por que usar `--allow-unauthenticated` em um Sistema Privado
> No Cloud Run, bloquear o tráfego na camada IAM do GCP exige um *Application Load Balancer* com *Identity-Aware Proxy (IAP)* para autenticar navegadores humanos, o que gera custo fixo mensal contínuo. Ao abrir o *ingress* HTTP com `--allow-unauthenticated` e delegar o bloqueio ao fluxo OAuth 2.0 dentro do `app.py`, obtém-se segurança criptográfica equivalente com **custo fixo zero**.

> [!warning] Proteção Financeira com `--max-instances 1`
> Em sistemas de uso estritamente individual, limitar `--max-instances 1` impede o escalonamento horizontal acidental em caso de varreduras automatizadas ou *loops* de requisição na URL pública `.a.run.app`.

### Conexões Transversais
- **Camada de Segurança e Segredos**: Configuração passo a passo da Tela de Consentimento OAuth, código completo de `app.py` com *whitelist* e montagem do Secret Manager em [[Autenticacao_OAuth2_OIDC_e_Secret_Manager_GCP]].
- **Alternativa SaaS sem Infraestrutura Própria**: Uso avançado da interface web do Gemini Pro integrada nativamente ao Google Drive e NotebookLM em [[Engenharia_Fluxo_Gemini_Pro_e_Workspace]].
