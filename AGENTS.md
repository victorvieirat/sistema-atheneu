# AGENTS.md — Sistema Atheneu (Segundo Cérebro)

Repositório de gestão de conhecimento pessoal multidisciplinar (Política, Economia, Carreira & Tecnologia, Biologia & Saúde, Filosofia, História, Moda & Beleza, Família & Relações). Foco em notas atômicas (Zettelkasten), Mapas de Conteúdo (MOCs) e conexões transversais 100% compatíveis com Obsidian e visualizadores Markdown.

## Arquitetura do Repositório
- **Raiz (`sistema-atheneu/`)**: Vault do Obsidian e repositório Git privado.
  - `AGENTS.md`: Regras universais de escrita, organização e automação.
  - `atheneu/`: Núcleo de conteúdo sincronizado com o Google Drive.
  - `scripts/`, `mcp/` e `.agents/skills/`: Motor técnico e skills contextuais (ocultos da navegação visual do Obsidian).
- **Estrutura de `atheneu/`**:
  - `000_Home.md`: Portal central de entrada e navegação pelos MOCs ativos.
  - `00_Inbox/`: Capturas rápidas (celular, web, exports do Gemini Pro) aguardando triagem.
  - `01_Diario/`: Registros cronológicos estritos (`YYYY-MM-DD.md`).
  - `02_Fontes/`: Fichamentos de livros, artigos científicos, relatórios em PDF, vídeos e links externos.
  - `03_Jardim/`: Coração da biblioteca. Notas atômicas permanentes sem subpastas e sem numeração fixa, interligadas por WikiLinks.
  - `04_MOCs/`: Mapas de Conteúdo temáticos (`MOC_*.md`) criados sob demanda apenas quando existirem notas reais na área.
  - `98_Privado/`: Notas íntimas e sensíveis (sincronizadas apenas com o Google Drive, ignoradas no Git).
  - `99_Sistema/`: Suporte estrutural (`_anexos/img/`, `_anexos/pdfs/` e `_templates/`).

## Barreira Estrita de Privacidade (`atheneu/98_Privado/`)
- **Bloqueio Espontâneo**: Agentes de IA estão **estritamente proibidos** de listar, ler, buscar, resumir ou indexar qualquer arquivo dentro de `atheneu/98_Privado/` por iniciativa própria.
- O acesso a um arquivo dessa pasta só é permitido se o usuário solicitar explicitamente o caminho ou nome exato da nota no prompt atual.

## Comportamento Geral e Escrita
- **Preservação de Autoria**: Em caso de ambiguidade em reflexões pessoais (Filosofia, Família, Carreira, Diário), preserve o tom original do usuário e sinalize sugestões ao final — nunca invente fatos pessoais.
- **Estilo Híbrido de Escrita**:
  - **Ciências Exatas, Engenharia/IA, Biológicas, Economia e História**: Priorize frases atômicas, listas diretas com **negrito orgânico** nos conceitos nucleares e tabelas comparativas para oposições ou parâmetros técnicos.
  - **Filosofia, Família, Moda, Beleza e Diário**: Permita parágrafos em prosa fluida para preservar nuances, ensaios pessoais e narrativas subjetivas.
- **Anti-Redundância (Unicidade de Conceito)**: Cada conceito nuclear deve residir em sua própria nota atômica em `03_Jardim/`. Se uma nota de Política ou Carreira precisar mobilizar um conceito de Biologia ou Economia já existente no cofre, não repita a explicação: insira o WikiLink `[[Conceito_Existente]]` e desenvolva apenas a relação transversal entre ambos.
- **Postura Contextual**: Em pautas de conjuntura política, debate eleitoral ou macroeconomia brasileira, consulte e ative a skill dedicada em `.agents/skills/analise-politica-economica/SKILL.md`. Nos demais domínios, mantenha rigor técnico, científico ou autoral isento de jargão partidário.

## Regras de Estrutura e Metadados
- **Nomenclatura**: Títulos semânticos em `Snake_Case` legível, sem acentos e sem numeração sequencial em `03_Jardim/` (ex: `Modelo_Dois_Processos_Sono_Borbely.md`). Notas em `01_Diario/` seguem estritamente `YYYY-MM-DD.md`. Notas em `02_Fontes/` iniciam com `Fonte_` e em `04_MOCs/` iniciam com `MOC_`.
- **Frontmatter YAML Obrigatório (`03_Jardim/`)**:
  - `mocs:` lista de WikiLinks entre aspas apontando para as grandes áreas em `04_MOCs/` (ex: `"[[MOC_Economia]]"`).
  - `tags:` papel complementar (nunca repita o nome das grandes áreas já listadas em `mocs`). Classifique o **formato/função** da nota (`conceito`, `protocolo`, `arquitetura`, `analise`, `retorica`, `ensaio`) e **micro-temas transversais** sem MOC próprio (ex: `sono`, `cloud-run`, `gemini`, `petrobras`, `previdencia`).
  - `fontes:` lista de WikiLinks para `02_Fontes/` (ex: `"[[Fonte_DIEESE_Sintese_Tesouraco_200_Bilhoes]]"`) ou URLs externas verificadas.
  - `atualizado: YYYY-MM-DD`.
- **Contexto Oculto de Imagens (`%% IA_CONTEXTO %%`)**:
  - Posicionado imediatamente abaixo de qualquer imagem incorporada (`![[...]]`), seja gráfico estatístico, diagrama de arquitetura, árvore genealógica ou referência visual de moda/estilo.
  - Deve conter a transcrição técnica, séries numéricas e descrição literal da imagem para indexação de IA e busca textual, proibindo a repetição literal desses mesmos bullets logo abaixo no texto visível.
- **Uso de Callouts e Limpeza Visual**:
  - Permitidos em `03_Jardim/`: `> [!quote]` (citações literais de autores/fontes), `> [!tip]` (insights práticos e aplicações acionáveis), `> [!warning]` (vieses cognitivos, riscos técnicos ou contradições lógicas).
  - Máximo de 2 callouts por nota em `03_Jardim/`. Zero emojis decorativos no corpo das notas do Jardim.
- **Política de PDFs**: Apenas livros, artigos científicos e relatórios primários são armazenados em `atheneu/99_Sistema/_anexos/pdfs/` (acompanhados de ficha em `02_Fontes/`). PDFs que sejam meras cópias exportadas de notas `.md` jamais devem ser salvos ou versionados no cofre.

## Fluxo de Triagem e Ciclo de Vida (`00_Inbox/` e `## RASCUNHOS`)
- **Consolidação**: Ao executar a rotina de triagem na `00_Inbox/` (incluindo documentos `.docx` ou `.md` salvos a partir do Gemini Pro no Google Drive) ou na seção transitória `## RASCUNHOS` ao final de uma nota existente:
  1. Extraia eventuais imagens embutidas (Base64 ou mídia de `.docx`) para `atheneu/99_Sistema/_anexos/img/` adicionando o bloco `%% IA_CONTEXTO %%`.
  2. Integre insights complementares ao corpo de notas existentes em `03_Jardim/` (atualizando o campo `atualizado:`).
  3. Crie novas notas atômicas em `03_Jardim/` para conceitos inéditos e fichas em `02_Fontes/` para referências primárias novas.
  4. Atualize os índices correspondentes em `04_MOCs/` (criando um novo `MOC_*.md` e linkando no `000_Home.md` apenas quando um novo grande domínio estrear com sua primeira nota real).
  5. Remova a seção transitória `## RASCUNHOS` (ou arquive/limpe o item processado da `00_Inbox/`).

## Diretrizes para Scripts (`scripts/`)
- **CLI Não-Interativo**: Receba todos os parâmetros via flags (`argparse`). Proibido o uso de `input()` para entrada de dados.
- **Modo Duplo de Execução**:
  - Modo Autônomo (IA): Flag `-y` / `--yes` para execução direta sem confirmação interativa.
  - Modo Humano (Padrão): Exibe resumo das notas que serão alteradas na pasta `atheneu/` e solicita confirmação `[S/n]`.
- **Operações Atômicas e UTF-8 (Segurança no Windows + Google Drive)**: Force `utf-8` em leitura/escrita e `stdout`. Para evitar conflitos de sincronização no Google Drive, toda modificação de arquivo `.md` deve ser gravada primeiro em arquivo `.tmp` e substituída atomicamente via `os.replace()`.
- **Feedback Padronizado**: Utilize prefixos claros no terminal (`[ERRO]`, `[INSTRUCAO]`, `[SUCESSO]`, `[ARQUIVO]`). Nunca gere logs `.json` ou artefatos temporários soltos dentro de `atheneu/`.
