---
name: auditoria-referencias-obsidian
description: Auditoria e normalização de referências locais do Obsidian (WikiLinks, embeds de mídia, arquivos .canvas e .base, subcaminhos de cabeçalhos e blocos, stems duplicados, stubs vazios e configs do .obsidian). Ative esta skill após movimentações de pastas/notas, criação de mapas .canvas, antes de commits ou sempre que o usuário relatar links quebrados ou notas que abrem vazias no Obsidian Desktop.
---

# Auditoria de Referências Locais do Obsidian

Procedimento operacional e script utilitário para auditar e corrigir problemas de integridade de links internos, mapas visuais (`.canvas`), bases dinâmicas (`.base`), anexos e configurações no vault do Obsidian, em conformidade com as diretrizes do `AGENTS.md` e respeitando estritamente a barreira de privacidade de `atheneu/98_Privado/`.

---

## 1. Quando Ativar esta Skill

- **Após reorganização ou renomeação de notas**: Sempre que arquivos forem movidos entre subpastas (ex.: de `03_Jardim/` para `03_Jardim/<Dominio>/` ou `05_Esforcos/`).
- **Após criar ou editar mapas `.canvas` em `04_MOCs/`**: Valida a sintaxe JSON Canvas 1.0, unicidade de IDs, existência real dos arquivos em nós `type: "file"`, resolução de `[[WikiLinks]]` dentro de nós `type: "text"` e integridade de `fromNode`/`toNode` em `edges`.
- **Ao detectar notas vazias inesperadas**: Quando um clique em WikiLink no Obsidian abrir uma nota nova em branco em vez da nota pretendida (indicativo de cache dessincronizado no app ou divergência de nome/caminho).
- **Antes de consolidar triagens do `01_Diario/` ou commits Git**: Para assegurar que nenhum WikiLink quebrado, anexo sem `%% IA_CONTEXTO %%` ou caminho de raiz frágil (`atheneu/...`) seja persistido.

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

## 3. Diretriz Crítica: Sincronização do Cache do Obsidian Desktop

Quando arquivos são movidos ou renomeados no disco através do terminal, Git ou agentes com o Obsidian Desktop aberto:
1. O Obsidian pode reter caminhos defasados em seu `metadataCache` em memória.
2. Nesses casos, clicar em uma nota existente que mudou de pasta pode levar o Obsidian a criar/abrir uma nota vazia.
3. **Instrução obrigatória**: oriente o usuário a pressionar `Ctrl+P` no Obsidian e executar **`Reload app without saving`** (ou acessar *Configurações → Arquivos e links → Reconstruir cache do cofre*).
