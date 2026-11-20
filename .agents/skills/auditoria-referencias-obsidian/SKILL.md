---
name: auditoria-referencias-obsidian
description: Auditoria e normalização de referências locais do Obsidian, prevenção de vazamento de informações pessoais/amigos próximos (PII) no repositório público e validação de formatação dual compatível com Obsidian Desktop e GitHub Pages (Quartz v5). Ative esta skill ao criar/editar notas, após movimentações de pastas, criação de mapas .canvas e obrigatoriamente antes de commits/pushes.
---

# Auditoria de Referências, Privacidade Pública e Compatibilidade Dual (Obsidian + Quartz)

Procedimento operacional e script utilitário para auditar e corrigir problemas de integridade de links internos, mapas visuais (`.canvas`), bases dinâmicas (`.base`), proteção contra exposição de informações pessoais/pessoas próximas no repositório público e compatibilidade de renderização com o **GitHub Pages (Quartz v5)**, em conformidade com o `AGENTS.md` e respeitando estritamente a barreira de `atheneu/98_Privado/`.

---

## 1. Quando Ativar esta Skill

- **Ao criar ou editar notas no cofre público (`01_Diario/`, `02_Fontes/`, `03_Jardim/`, `04_MOCs/`, `05_Esforcos/`)**: Para lembrar o usuário de não incluir dados de amigos próximos, familiares ou PII e aplicar a formatação dual compatível com Obsidian e Quartz.
- **Após reorganização ou renomeação de notas**: Sempre que arquivos forem movidos entre subpastas (ex.: de `03_Jardim/` para `03_Jardim/<Dominio>/` ou `05_Esforcos/`).
- **Após criar ou editar mapas `.canvas` em `04_MOCs/`**: Valida a sintaxe JSON Canvas 1.0, unicidade de IDs, existência real dos arquivos em nós `type: "file"`, resolução de `[[WikiLinks]]` dentro de nós `type: "text"` e integridade de `fromNode`/`toNode` em `edges`.
- **Ao detectar notas vazias inesperadas**: Quando um clique em WikiLink no Obsidian abrir uma nota nova em branco em vez da nota pretendida (indicativo de cache dessincronizado no app ou divergência de nome/caminho).
- **Antes de consolidar triagens do `01_Diario/` ou commits Git**: Para assegurar que nenhum dado pessoal/sensível, WikiLink quebrado, comentário `%%` aberto, placeholder `{{...}}` no YAML ou anexo sem `%% IA_CONTEXTO %%` seja publicado no GitHub Pages.

---

## 2. Como Executar a Auditoria

O script oficial localiza-se em `./scripts/auditar_referencias.py` e opera em modo duplo CLI (`argparse`):

### A. Modo Verificação (Somente Leitura — Padrão)

Execute o comando a partir da raiz do repositório:

```powershell
python .agents/skills/auditoria-referencias-obsidian/scripts/auditar_referencias.py --check
```

Para tratar avisos como erros bloqueantes (recomendado em CI ou validação final):

```powershell
python .agents/skills/auditoria-referencias-obsidian/scripts/auditar_referencias.py --check --strict
```

### B. Modo Correção Automática Segura (`--fix`)

Aplica correções determinísticas (substituição de prefixos frágeis `[[atheneu/.../arquivo.ext]]` pelo formato canônico `[[arquivo.ext]]` quando o nome é único no cofre, e escape de pipes `\|` em tabelas):

- **Modo Autônomo (IA / Scripts)**:
  ```powershell
  python .agents/skills/auditoria-referencias-obsidian/scripts/auditar_referencias.py --fix -y
  ```
- **Modo Humano (Interativo)**:
  ```powershell
  python .agents/skills/auditoria-referencias-obsidian/scripts/auditar_referencias.py --fix
  ```
  *(Exibe a lista dos arquivos afetados e solicita confirmação `[S/n]` antes de aplicar a gravação atômica em UTF-8).*

---

## 3. Diretriz de Privacidade Pública e Anonimização (Pessoas Próximas e PII)

Como o repositório Git e o site GitHub Pages (`https://victorvieirat.github.io/sistema-atheneu/`) são **públicos**:
1. **`01_Diario/` como Bloco de Anotações de Estudo**: A pasta `01_Diario/` é dedicada a capturas de estudo, links e rascunhos teóricos do dia a dia — nunca a relatos íntimos ou diário pessoal.
2. **Proibição de Dados de Amigos, Familiares e Terceiros**: Nunca registre nomes reais, apelidos identificáveis, histórias privadas ou situações pessoais de amigos próximos, familiares ou colegas fora de `atheneu/98_Privado/`.
3. **Filtro e Abstração Ativa pela IA**: Se o usuário fornecer um prompt com exemplo pessoal envolvendo amigos ou familiares para criar uma nota pública (ex.: em Filosofia, Família, Política ou Diário), **alerte o usuário** e **anonimize/abstraia o caso para o conceito geral** antes de salvar.
4. **Bloqueio de PII e Segredos**: O script `auditar_referencias.py` verifica automaticamente padrões de CPF, telefones pessoais, e-mails não-placeholder, chaves/tokens de API e marcadores de confidencialidade antes do commit.

---

## 4. Checklist de Formatação Dual (Obsidian Desktop + GitHub Pages / Quartz v5)

Ao redigir ou revisar notas futuras, garanta compatibilidade simultânea entre o app local e o build do Quartz (`npx quartz build -d atheneu`):
- **WikiLinks e Anexos Curtos (`shortest`)**: Use sempre `[[Nome_da_Nota]]` e `![[arquivo.ext]]`. Em tabelas Markdown, escape o pipe do alias: `[[Nome_da_Nota\|Texto Visível]]`.
- **Frontmatter YAML Limpo**: Coloque WikiLinks entre aspas (`"[[MOC_...]]"`) e jamais deixe placeholders de template como `{{date}}` fora de `99_Sistema/_templates/`.
- **Comentários Ocultos (`%% IA_CONTEXTO` ... `%%`)**: Abra o bloco com `%% IA_CONTEXTO` na primeira linha e feche com `%%` após a transcrição (nunca feche na mesma linha `%% IA_CONTEXTO %%`, pois isso deixaria a transcrição visível no Obsidian e no site público do Quartz).
- **LaTeX (KaTeX), Callouts e Mermaid**: Escape cifrões literais em prosa como `\$` (ou use backticks `` `R$ 100` ``); use callouts padrão (`[!note]`, `[!tip]`, `[!warning]`, `[!quote]`) e coloque rótulos Mermaid com parênteses/colchetes entre aspas duplas (`id["Rótulo (Detalhe)"]`).
- **Boas Práticas para Novos `.base` e `.canvas`**: Em novos arquivos `.base`, prefira filtros por propriedades/tags (`status`, `file.hasTag(...)`) ou combine `or` com e sem o prefixo `atheneu/` (`file.inFolder("atheneu/03_Jardim")` e `file.inFolder("03_Jardim")`); em novos `.canvas`, inclua sempre o `[[WikiLink]]` curto dentro dos cartões de texto.

---

## 5. Diretriz Crítica: Sincronização do Cache do Obsidian Desktop

Quando arquivos são movidos ou renomeados no disco através do terminal, Git ou agentes com o Obsidian Desktop aberto:
1. O Obsidian pode reter caminhos defasados em seu `metadataCache` em memória.
2. Nesses casos, clicar em uma nota existente que mudou de pasta pode levar o Obsidian a criar/abrir uma nota vazia.
3. **Instrução obrigatória**: oriente o usuário a pressionar `Ctrl+P` no Obsidian e executar **`Reload app without saving`** (ou acessar *Configurações → Arquivos e links → Reconstruir cache do cofre*).
