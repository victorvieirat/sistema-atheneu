"""Servidor MCP para manipulação de arquivos Obsidian Canvas (JSON Canvas 1.0).

Executado via FastMCP e stdio transport.
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP
from canvas import CanvasManager

# Inicializa o servidor MCP
mcp = FastMCP("obsidian-canvas")
manager = CanvasManager()


@mcp.tool()
def canvas_read(
    file_path: str,
    detail: str = "summary",
    search_text: Optional[str] = None
) -> str:
    """Lê um arquivo .canvas do Obsidian com níveis ajustáveis de detalhe e busca.
    
    Args:
        file_path: Caminho do arquivo .canvas (relativo ao cofre ou absoluto).
        detail: Nível de detalhe: 'summary' (padrão - estatísticas, caixas e IDs), 'full' (JSON completo), 'nodes' ou 'edges'.
        search_text: Palavra-chave opcional para filtrar nós e arestas conectadas.
    """
    try:
        res = manager.read_canvas(file_path=file_path, detail=detail, search_text=search_text)
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_create(
    file_path: str,
    overwrite: bool = False
) -> str:
    """Cria um novo arquivo .canvas em branco válido com gravação atômica em UTF-8.
    
    Args:
        file_path: Caminho do arquivo .canvas a ser criado.
        overwrite: Se True, substitui o arquivo caso já exista. Padrão False.
    """
    try:
        res = manager.create_canvas(file_path=file_path, overwrite=overwrite)
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_add_node(
    file_path: str,
    node_type: str,
    content: str,
    node_id: Optional[str] = None,
    color: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    placement: Optional[str] = None,
    relative_to: Optional[str] = None,
    gap: int = 60
) -> str:
    """Adiciona um novo nó ao Canvas com posicionamento absoluto ou relativo inteligente.
    
    Args:
        file_path: Caminho do arquivo .canvas.
        node_type: Tipo do nó: 'text', 'file', 'link' ou 'group'.
        content: Conteúdo do nó: texto markdown (text), caminho de nota (file), URL (link) ou título (group).
        node_id: ID único opcional (se omitido, um ID único será gerado).
        color: Cor do cartão: preset '1'..'6' ('1' vermelho, '2' laranja, '3' amarelo, '4' verde, '5' ciano, '6' roxo) ou '#RRGGBB'.
        width: Largura em pixels (padrões: text 360, file 420, link 320, group 680).
        height: Altura em pixels (padrões: text 220, file 240, link 180, group 440).
        x: Coordenada X absoluta opcional.
        y: Coordenada Y absoluta opcional.
        placement: Posicionamento relativo: 'right_of', 'below', 'left_of', 'above' ou 'auto'.
        relative_to: ID do nó de referência usado junto com placement.
        gap: Espaçamento em pixels entre caixas (padrão 60).
    """
    try:
        res = manager.add_node(
            file_path=file_path,
            node_type=node_type,
            content=content,
            node_id=node_id,
            color=color,
            width=width,
            height=height,
            x=x,
            y=y,
            placement=placement,
            relative_to=relative_to,
            gap=gap
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_update_node(
    file_path: str,
    node_id: str,
    content: Optional[str] = None,
    color: Optional[str] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> str:
    """Atualiza o conteúdo, cor, dimensões ou posição de um nó existente.
    
    Args:
        file_path: Caminho do arquivo .canvas.
        node_id: ID do nó a ser modificado.
        content: Novo conteúdo/texto/arquivo/rótulo.
        color: Nova cor ('1'..'6' ou '#RRGGBB').
        x: Nova coordenada X.
        y: Nova coordenada Y.
        width: Nova largura.
        height: Nova altura.
    """
    try:
        res = manager.update_node(
            file_path=file_path,
            node_id=node_id,
            content=content,
            color=color,
            x=x,
            y=y,
            width=width,
            height=height
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path, "node_id": node_id}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_delete_node(
    file_path: str,
    node_id: str,
    cascade_edges: bool = True
) -> str:
    """Remove um nó do Canvas e opcionalmente limpa suas arestas conectadas.
    
    Args:
        file_path: Caminho do arquivo .canvas.
        node_id: ID do nó a ser removido.
        cascade_edges: Se True (padrão), remove automaticamente as arestas ligadas a este nó.
    """
    try:
        res = manager.delete_node(
            file_path=file_path,
            node_id=node_id,
            cascade_edges=cascade_edges
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path, "node_id": node_id}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_add_edge(
    file_path: str,
    from_node: str,
    to_node: str,
    edge_id: Optional[str] = None,
    from_side: Optional[str] = None,
    to_side: Optional[str] = None,
    from_end: str = "none",
    to_end: str = "arrow",
    color: Optional[str] = None,
    label: Optional[str] = None
) -> str:
    """Conecta dois nós do Canvas com linha direcionada ou sem setas.
    
    Args:
        file_path: Caminho do arquivo .canvas.
        from_node: ID do nó de origem.
        to_node: ID do nó de destino.
        edge_id: ID único opcional da aresta.
        from_side: Lado de saída ('top', 'right', 'bottom', 'left' ou 'auto'). Padrão 'auto'.
        to_side: Lado de entrada ('top', 'right', 'bottom', 'left' ou 'auto'). Padrão 'auto'.
        from_end: Terminação na origem ('none' ou 'arrow'). Padrão 'none'.
        to_end: Terminação no destino ('none' ou 'arrow'). Padrão 'arrow'.
        color: Cor da conexão ('1'..'6' ou '#RRGGBB').
        label: Rótulo de texto descritivo sobre a aresta.
    """
    try:
        res = manager.add_edge(
            file_path=file_path,
            from_node=from_node,
            to_node=to_node,
            edge_id=edge_id,
            from_side=from_side,
            to_side=to_side,
            from_end=from_end,
            to_end=to_end,
            color=color,
            label=label
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_delete_edge(
    file_path: str,
    edge_id: Optional[str] = None,
    from_node: Optional[str] = None,
    to_node: Optional[str] = None
) -> str:
    """Remove uma conexão existente por ID ou pelo par de nós conectados.
    
    Args:
        file_path: Caminho do arquivo .canvas.
        edge_id: ID da aresta a ser removida.
        from_node: Nó de origem (se edge_id não fornecido).
        to_node: Nó de destino (se edge_id não fornecido).
    """
    try:
        res = manager.delete_edge(
            file_path=file_path,
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_batch_edit(
    file_path: str,
    operations: List[Dict[str, Any]]
) -> str:
    """Executa múltiplas operações atômicas em lote com apenas uma gravação final no disco.
    
    Cada operação é um dicionário com atributo 'action' ('add_node', 'update_node', 'delete_node', 'add_edge', 'delete_edge')
    e seus respectivos argumentos. Se qualquer operação falhar, toda a transação é abortada.
    """
    try:
        res = manager.batch_edit(file_path=file_path, operations=operations)
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


@mcp.tool()
def canvas_validate(
    file_path: str
) -> str:
    """Valida a conformidade técnica com o JSON Canvas 1.0, integridade de notas e colisões espaciais.
    
    Args:
        file_path: Caminho do arquivo .canvas.
    """
    try:
        res = manager.validate_canvas(file_path=file_path)
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "file_path": file_path}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
