# Obsidian Canvas MCP Server (`obsidian-canvas`)

Servidor MCP em Python (*FastMCP*) para leitura, criação e edição automatizada de mapas visuais do Obsidian (`.canvas`), operando conforme a especificação aberta **JSON Canvas 1.0**.

---

## Recursos Principais

1. **Leitura Flexível (`canvas_read`)**:
   - Modo resumo (`summary`) por padrão para economizar tokens na janela de contexto.
   - Modos completos (`full`, `nodes`, `edges`) e busca textual por palavras-chave (`search_text`).
2. **Criação Segura (`canvas_create`)**:
   - Cria arquivos `.canvas` vazios válidos com gravação atômica (`.tmp` + `os.replace`) em UTF-8.
3. **Manipulação Granular de Nós e Arestas (`canvas_add_node`, `canvas_update_node`, `canvas_delete_node`, `canvas_add_edge`, `canvas_delete_edge`)**:
   - Suporte aos 4 tipos de nós da especificação: `text`, `file`, `link` e `group`.
   - Limpeza em cascata de arestas órfãs ao remover um nó (`cascade_edges=True`).
4. **Posicionamento Relativo & Prevenção de Colisão AABB**:
   - Alocação relativa (`right_of`, `below`, `left_of`, `above`, `auto`) em relação a nós existentes.
   - Cálculo de caixa delimitadora (*Axis-Aligned Bounding Box*) para evitar que cartões fiquem sobrepostos.
   - Seleção automática dos lados de conexão (`auto_sides`) com base na orientação relativa dos cartões.
5. **Transações em Lote (`canvas_batch_edit`)**:
   - Executa uma sequência de mutações em memória e realiza apenas uma gravação atômica final.
6. **Validação de Conformidade (`canvas_validate`)**:
   - Checa conformidade com o JSON Canvas 1.0, arestas órfãs, IDs duplicados e existência de notas conectadas.
7. **Barreira Estrita de Privacidade**:
   - Bloqueio imediato contra referências ou criações apontando para a pasta sensível `98_Privado/`.

---

## Execução Local via `uv`

```powershell
uv run --directory mcp/obsidian_canvas python server.py
```
