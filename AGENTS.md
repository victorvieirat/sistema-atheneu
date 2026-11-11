# AGENTS.md — Sistema Atheneu (Segundo Cérebro)

Repositório de gestão de conhecimento pessoal multidisciplinar (Política, Economia, Carreira & Tecnologia, Biologia & Saúde, Filosofia, História, Moda & Beleza, Família & Relações). Foco em notas permanentes organizadas por grande domínio, Sub-MOCs transversais, compreensão ativa (Feynman) e conexões bidirecionais 100% compatíveis com Obsidian e visualizadores Markdown.

## Arquitetura do Repositório
- **Raiz (`sistema-atheneu/`)**: Vault do Obsidian e repositório Git privado.
  - `AGENTS.md`: Regras universais de escrita, organização e automação.
  - `atheneu/`: Núcleo de conteúdo sincronizado com o Google Drive.
  - `scripts/`, `mcp/` e `.agents/skills/`: Motor técnico e skills contextuais (ocultos da navegação visual do Obsidian).
- **Estrutura de `atheneu/`**:
  - `000_Home.md`: Portal central de entrada e navegação pelos MOCs, Sub-MOCs e `Painel_Ateneo.base`.
  - `Painel_Ateneo.base`: Painel dinâmico do Obsidian Bases filtrado por `status:`, pasta e eixos transversais.
  - `01_Diario/`: Porta única de captura e registros do dia a dia — aceita notas cronológicas (`YYYY-MM-DD.md`), rascunhos temáticos livres, links de estudo e exports externos aguardando triagem (`status: semente`).
  - `02_Fontes/`: Fichamentos de livros, artigos científicos, relatórios em PDF, vídeos e links externos (`Fonte_*.md`). Dados brutos e tabelas extensas de referência moram prioritariamente aqui.
  - `03_Jardim/`: Coração atemporal da biblioteca, organizado em subpastas pelos grandes domínios ativos (`Economia/`, `Politica/`, `Carreira_e_Tecnologia/`, `Biologia_e_Saude/`, `Moda_e_Beleza/`). Notas que cruzam áreas ficam na subpasta de seu mecanismo principal e conectam-se às demais via `mocs:` no YAML e tags.
  - `04_MOCs/`: Mapas de Conteúdo de grande área (`MOC_<Dominio>.md`), **Sub-MOCs transversais** (`MOC_<Assunto>.md`, ex.: `MOC_Combate_Austeridade_Fiscal.md`) e **Mapas Visuais de Blindagem/Síntese** no formato nativo Obsidian Canvas (`MOC_<Assunto>.canvas`, especificação JSON Canvas 1.0) criados quando um tema cruza múltiplas notas, áreas ou rodadas de debate teórico.
  - `05_Esforcos/`: Entregas práticas, campanhas, roteiros táticos e projetos com recorte temporal (ex.: `05_Esforcos/Eleicoes_2026/`), separados do conhecimento atemporal do Jardim.
  - `98_Privado/`: Notas íntimas e sensíveis (sincronizadas apenas com o Google Drive, ignoradas no Git).
  - `99_Sistema/`: Suporte estrutural (`_anexos/img/`, `_anexos/pdfs/` e `_templates/`).

## Barreira Estrita de Privacidade (`atheneu/98_Privado/`)
- **Bloqueio Espontâneo**: Agentes de IA estão **estritamente proibidos** de listar, ler, buscar, resumir ou indexar qualquer arquivo dentro de `atheneu/98_Privado/` por iniciativa própria.
- O acesso a um arquivo dessa pasta só é permitido se o usuário solicitar explicitamente o caminho ou nome exato da nota no prompt atual.

## Comportamento Geral e Escrita
- **Preservação de Autoria**: Em caso de ambiguidade em reflexões pessoais (Filosofia, Família, Carreira, Diário), preserve o tom original do usuário e sinalize sugestões ao final — nunca invente fatos pessoais.
- **Compreensão Ativa (Bloco Feynman)**: Toda nota em `03_Jardim/` e `05_Esforcos/` inicia com `## Resumo Feynman (Minhas Palavras)` logo abaixo do título `# ...` para o usuário sintetizar a ideia com as próprias palavras e registrar dúvidas antes do corpo técnico.
- **Estilo Híbrido de Escrita**:
  - **Ciências Exatas, Engenharia/IA, Biológicas, Economia e História**: Priorize frases atômicas, listas diretas com **negrito orgânico** nos conceitos nucleares e tabelas comparativas para oposições ou parâmetros técnicos.
  - **Filosofia, Família, Moda, Beleza e Diário**: Permita parágrafos em prosa fluida para preservar nuances, ensaios pessoais e narrativas subjetivas.
- **Anti-Redundância (Unicidade de Conceito)**: Cada conceito nuclear deve residir em sua própria nota em `03_Jardim/`. Se uma nota de Política, Esforços ou Carreira precisar mobilizar um conceito já existente no cofre, não repita a explicação: insira o WikiLink `[[Conceito_Existente]]` e desenvolva apenas a relação transversal entre ambos.
- **Postura Contextual**: Em pautas de conjuntura política, debate eleitoral ou macroeconomia brasileira, consulte e ative a skill dedicada em `.agents/skills/analise-politica-economica/SKILL.md`. Nos demais domínios, mantenha rigor técnico, científico ou autoral isento de jargão partidário.
- **Rubrica de Blindagem Teórica e Teste de Estresse (`MOC_*.canvas`)**: Ao construir matrizes de embate teórico em 2 rodadas (*Ataque → Resposta atual do cofre → Tréplica steelman → Veredito*), classifique cada ramificação em 4 níveis: **Forte** (cor `"4"` verde — mecanismo causal completo + evidência institucional neutra que sobrevive à tréplica), **Parcial** (cor `"3"` amarela — responde ao 1º round, mas falta variável-chave ou depende apenas de fonte militante/sindical), **Lacuna** (cor `"1"` vermelha — tema ausente nas notas do Jardim) ou **Vulnerável** (cor `"2"` laranja — tese atual contém premissa incompleta ou facilmente invertível pelo adversário), discriminando sempre a natureza da fonte (*Institucional Neutra* vs. *Militante/Sindical* vs. *Rascunho não verificado*).

## Regras de Estrutura e Metadados
- **Nomenclatura**: Títulos semânticos em `Snake_Case` legível, sem acentos e sem numeração sequencial em `03_Jardim/` e `05_Esforcos/` (ex: `Modelo_Dois_Processos_Sono_Borbely.md`). Notas em `01_Diario/` aceitam `YYYY-MM-DD.md` ou títulos livres. Notas em `02_Fontes/` iniciam com `Fonte_` e em `04_MOCs/` iniciam com `MOC_` (tanto `.md` quanto `.canvas`).
- **Frontmatter YAML Obrigatório (`03_Jardim/` e `05_Esforcos/`)**:
  - `mocs:` lista de WikiLinks entre aspas apontando para os MOCs e Sub-MOCs relevantes em `04_MOCs/` (ex: `"[[MOC_Economia]]"`).
  - `tags:` tags livres complementares (nunca repita o nome literal das grandes áreas já listadas em `mocs`). Classifique o **formato/função** (`conceito`, `protocolo`, `arquitetura`, `analise`, `retorica`, `metodologia`) e **temas transversais reutilizáveis** (evitando sinônimos duplicados ou tags soltas de uma única nota).
  - `fontes:` lista de WikiLinks para `02_Fontes/` (ex: `"[[Fonte_DIEESE_Sintese_Tesouraco_200_Bilhoes]]"`) ou URLs externas verificadas.
  - `status:` estágio de compreensão pessoal para filtragem no Obsidian Bases (`semente` | `em-estudo` | `dominada`).
  - `atualizado: YYYY-MM-DD`.
- **Contexto Oculto de Imagens (`%% IA_CONTEXTO %%`)**:
  - Posicionado imediatamente abaixo de qualquer imagem incorporada (`![[...]]`), seja gráfico estatístico, diagrama de arquitetura, árvore genealógica ou referência visual de moda/estilo.
  - Deve conter a transcrição técnica, séries numéricas e descrição literal da imagem para indexação de IA e busca textual, proibindo a repetição literal desses mesmos bullets logo abaixo no texto visível.
- **Uso de Callouts e Limpeza Visual**:
  - Permitidos em `03_Jardim/` e `05_Esforcos/`: `> [!note]` (bloco Feynman/dúvidas), `> [!quote]` (citações literais de autores/fontes), `> [!tip]` (insights práticos e aplicações acionáveis), `> [!warning]` (vieses cognitivos, riscos técnicos ou contradições lógicas).
  - Máximo de 2 callouts informativos por nota (além do bloco Feynman inicial). Zero emojis decorativos no corpo das notas do Jardim.
- **Política de PDFs**: Apenas livros, artigos científicos e relatórios primários são armazenados em `atheneu/99_Sistema/_anexos/pdfs/` (acompanhados de ficha em `02_Fontes/`). PDFs que sejam meras cópias exportadas de notas `.md` jamais devem ser salvos ou versionados no cofre.

## Fluxo de Triagem e Ciclo de Vida (`01_Diario/` e `## RASCUNHOS`)
- **Consolidação**: Ao executar a rotina de triagem em capturas maduras de `01_Diario/` (incluindo documentos `.docx` ou `.md` salvos a partir do Gemini Pro no Google Drive) ou na seção transitória `## RASCUNHOS` ao final de uma nota existente:
  1. Extraia eventuais imagens embutidas (Base64 ou mídia de `.docx`) para `atheneu/99_Sistema/_anexos/img/` adicionando o bloco `%% IA_CONTEXTO %%`.
  2. Integre insights complementares ao corpo de notas existentes em `03_Jardim/` ou `05_Esforcos/` (atualizando `atualizado:`).
  3. Crie novas notas em `03_Jardim/<Dominio>/` (com `status: semente` e bloco Feynman) ou `05_Esforcos/` e fichas em `02_Fontes/` para referências primárias novas.
  4. Atualize os índices correspondentes em `04_MOCs/` (criando um novo `MOC_*.md` ou Sub-MOC transversal e linkando no `000_Home.md` quando um novo domínio ou grande eixo estrear).
  5. Remova a seção transitória `## RASCUNHOS` (ou arquive/limpe o item processado de `01_Diario/` marcando como `status: dominada` quando fizer sentido manter o histórico).
  6. Execute a auditoria de integridade local via skill `.agents/skills/auditoria-referencias-obsidian/` (`python .agents/skills/auditoria-referencias-obsidian/scripts/auditar_referencias.py --check --strict`). Caso o Obsidian Desktop estivesse aberto durante movimentações no disco, oriente o usuário a recarregar o cache via `Ctrl+P` → `Reload app without saving` ou `Configurações → Arquivos e links → Reconstruir cache do cofre`.

## Diretrizes para Scripts (`scripts/` e `.agents/skills/*/scripts/`)
- **CLI Não-Interativo**: Receba todos os parâmetros via flags (`argparse`). Proibido o uso de `input()` para entrada de dados.
- **Modo Duplo de Execução**:
  - Modo Autônomo (IA): Flag `-y` / `--yes` para execução direta sem confirmação interativa.
  - Modo Humano (Padrão): Exibe resumo das notas que serão alteradas na pasta `atheneu/` e solicita confirmação `[S/n]`.
- **Operações Atômicas e UTF-8 (Segurança no Windows + Google Drive)**: Force `utf-8` em leitura/escrita e `stdout`. Para evitar conflitos de sincronização no Google Drive, toda modificação de arquivo `.md`, `.base` ou `.canvas` deve ser gravada primeiro em arquivo `.tmp` e substituída atomicamente via `os.replace()`.
- **Feedback Padronizado**: Utilize prefixos claros no terminal (`[ERRO]`, `[INSTRUCAO]`, `[SUCESSO]`, `[ARQUIVO]`). Nunca gere logs `.json` ou artefatos temporários soltos dentro de `atheneu/` (arquivos `.canvas` em `04_MOCs/` seguem a especificação JSON Canvas 1.0 do Obsidian e são mapas permanentes válidos do cofre).

## Servidores MCP (`mcp/`)
- **Obsidian Canvas (`mcp/obsidian_canvas/`)**: Servidor FastMCP executado via `uv` para leitura, criação e manipulação automatizada de mapas visuais (`.canvas`). Suas ferramentas (`canvas_read`, `canvas_create`, `canvas_add_node`, `canvas_update_node`, `canvas_delete_node`, `canvas_add_edge`, `canvas_delete_edge`, `canvas_batch_edit`, `canvas_validate`) operam em UTF-8 atômico (`.tmp` + `os.replace`), previnem colisões espaciais (AABB), limpam arestas órfãs em cascata e bloqueiam preventivamente qualquer acesso ou referência a `atheneu/98_Privado/`.

